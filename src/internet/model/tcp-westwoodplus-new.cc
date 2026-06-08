#include "tcp-westwoodplus-new.h"
#include "ns3/log.h"
#include "ns3/simulator.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpWestwoodPlusNew");

//ensures the class is registered with ns-3’s object system.
NS_OBJECT_ENSURE_REGISTERED (TcpWestwoodPlusNew);

TypeId
TcpWestwoodPlusNew::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpWestwoodPlusNew")
    .SetParent<TcpWestwoodPlus> ()
    .SetGroupName ("Internet")
    .AddConstructor<TcpWestwoodPlusNew> ()
  ;
  return tid;
}

TcpWestwoodPlusNew::TcpWestwoodPlusNew (void)
  : TcpWestwoodPlus (),
    m_previousBW (0),
    m_previousRtt (Seconds (0)),
    m_oldRto (Seconds (0)),
    m_linkRecovery (false)
{
  NS_LOG_FUNCTION (this);
}

TcpWestwoodPlusNew::TcpWestwoodPlusNew (const TcpWestwoodPlusNew& sock)
  : TcpWestwoodPlus (sock),
    m_previousBW (sock.m_previousBW),
    m_previousRtt (sock.m_previousRtt),
    m_oldRto (sock.m_oldRto),
    m_linkRecovery (sock.m_linkRecovery)
{
  NS_LOG_FUNCTION (this);
}

TcpWestwoodPlusNew::~TcpWestwoodPlusNew (void)
{
  NS_LOG_FUNCTION (this);
}

std::string
TcpWestwoodPlusNew::GetName () const
{
  return "TcpWestwoodPlusNew";
}

Ptr<TcpCongestionOps>
TcpWestwoodPlusNew::Fork ()
{
  NS_LOG_FUNCTION (this);
  return CopyObject<TcpWestwoodPlusNew> (this);
}

double
TcpWestwoodPlusNew::CalculateBWRatio (void)
{
  NS_LOG_FUNCTION (this);
  
  // Get current bandwidth estimate from parent class
  // m_currentBW is protected member of TcpWestwoodPlus
  DataRate currentBW = m_currentBW;
  
  // Avoid division by zero
  if (m_previousBW.GetBitRate () == 0)
    {
      NS_LOG_DEBUG ("Previous BW is zero, setting ratio to 1.0");
      return 1.0;
    }
  
  double ratio = static_cast<double> (currentBW.GetBitRate ()) / 
                 static_cast<double> (m_previousBW.GetBitRate ());
  
  NS_LOG_DEBUG ("BWratio: " << ratio << " (current: " << currentBW << 
                ", previous: " << m_previousBW << ")");
  
  return ratio;
}



void
TcpWestwoodPlusNew::CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
  
  if (segmentsAcked > 0)
    {
      // Calculate bandwidth ratio
      double bwRatio = CalculateBWRatio ();
      
      // Enhanced congestion avoidance algorithm from paper
      double adder = 0.0;
      
      if (bwRatio >= 1.5)
        {
          // Network is lightly loaded - increase aggressively
          adder = 2.0 / static_cast<double> (tcb->m_cWnd.Get () / tcb->m_segmentSize);
          NS_LOG_DEBUG ("Network lightly loaded (BWratio >= 1.5), adder = 2/cwnd");
        }
      else if (bwRatio >= 1.0 && bwRatio < 1.5)
        {
          // Normal network conditions - standard increase
          adder = 1.0 / static_cast<double> (tcb->m_cWnd.Get () / tcb->m_segmentSize);
          NS_LOG_DEBUG ("Normal network load (1.0 <= BWratio < 1.5), adder = 1/cwnd");
        }
      else // bwRatio < 1.0
        {
          // Network congested - hold steady
          adder = 0.0;
          NS_LOG_DEBUG ("Network congested (BWratio < 1.0), adder = 0");
        }
      
      // Update congestion window
      uint32_t cwndAdd = static_cast<uint32_t> (adder * tcb->m_segmentSize);
      tcb->m_cWnd += std::max (cwndAdd, 1u);
      
      NS_LOG_INFO ("Updated cwnd: " << tcb->m_cWnd << 
                   " (added: " << cwndAdd << " bytes, BWratio: " << bwRatio << ")");
      
      // Store current BW as previous for next calculation
      m_previousBW = m_currentBW;
    }
}





void
TcpWestwoodPlusNew::PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked << rtt);
  
  // Call parent class method to update bandwidth estimate
  TcpWestwoodPlus::PktsAcked (tcb, segmentsAcked, rtt);
  
  // Update RTO estimate based on RTT changes
  if (!rtt.IsZero ())
    {
      UpdateRtoEstimate (tcb);
      m_previousRtt = rtt;
    }
}

void
TcpWestwoodPlusNew::UpdateRtoEstimate (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);
  
  if (!m_previousRtt.IsZero ())
    {
      Time currentRtt = tcb->m_lastRtt.Get ();
      double rttRatio = currentRtt.GetSeconds () / m_previousRtt.GetSeconds ();
      
      // Detect significant RTT change (indicating possible link recovery)
      if (rttRatio > 1.5 || rttRatio < 0.5)
        {
          NS_LOG_DEBUG ("Significant RTT change detected (ratio: " << rttRatio << ")");
          m_linkRecovery = true;
          
          // Calculate adjusted RTO based on RTT ratio
          Time newRto = Seconds (rttRatio * m_oldRto.GetSeconds ());
          
          Time minRto = MilliSeconds (200);
          Time maxRto = Seconds (60.0);     
          
          if (newRto.Compare (minRto) < 0)
          {
              newRto = minRto;
          }
          else if (newRto.Compare (maxRto) > 0)
          {
              newRto = maxRto;
          }
          
          m_oldRto = newRto;
          
          NS_LOG_INFO ("RTO estimate updated to " << newRto.GetSeconds () << 
                       "s (RTT ratio: " << rttRatio << ")");
        }
      else
      {
          m_linkRecovery = false;
          // Track the SRTT-based RTO estimate
          m_oldRto = Seconds (tcb->m_srtt.Get ().GetSeconds () * 2.0);
      }
    }
  else
    {
      // Initialize old RTO from current SRTT
      Time srtt = tcb->m_srtt.Get ();
      if (!srtt.IsZero ())
        {
          m_oldRto = Seconds (srtt.GetSeconds () * 2.0);
        }
    }
}

} // namespace ns3