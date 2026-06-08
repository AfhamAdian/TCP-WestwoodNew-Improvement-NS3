#include "tcp-modified-tco-westwoodplus-new.h"

#include "ns3/log.h"
#include "ns3/simulator.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpModifiedTcoWestwoodPlusNew");

NS_OBJECT_ENSURE_REGISTERED (TcpModifiedTcoWestwoodPlusNew);

TypeId
TcpModifiedTcoWestwoodPlusNew::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpModifiedTcoWestwoodPlusNew")
    .SetParent<TcpWestwoodPlus> ()
    .SetGroupName ("Internet")
    .AddConstructor<TcpModifiedTcoWestwoodPlusNew> ()
  ;
  return tid;
}

TcpModifiedTcoWestwoodPlusNew::TcpModifiedTcoWestwoodPlusNew (void)
  : TcpWestwoodPlus (),
    m_previousBW (0),
    m_previousRtt (Seconds (0)),
    m_oldRto (Seconds (0)),
    m_linkRecovery (false)
{
  NS_LOG_FUNCTION (this);
}

TcpModifiedTcoWestwoodPlusNew::TcpModifiedTcoWestwoodPlusNew (const TcpModifiedTcoWestwoodPlusNew& sock)
  : TcpWestwoodPlus (sock),
    m_previousBW (sock.m_previousBW),
    m_previousRtt (sock.m_previousRtt),
    m_oldRto (sock.m_oldRto),
    m_linkRecovery (sock.m_linkRecovery)
{
  NS_LOG_FUNCTION (this);
}

TcpModifiedTcoWestwoodPlusNew::~TcpModifiedTcoWestwoodPlusNew (void)
{
  NS_LOG_FUNCTION (this);
}

std::string
TcpModifiedTcoWestwoodPlusNew::GetName () const
{
  return "TcpModifiedTcoWestwoodPlusNew";
}

Ptr<TcpCongestionOps>
TcpModifiedTcoWestwoodPlusNew::Fork ()
{
  NS_LOG_FUNCTION (this);
  return CopyObject<TcpModifiedTcoWestwoodPlusNew> (this);
}

double
TcpModifiedTcoWestwoodPlusNew::CalculateBWRatio (void)
{
  NS_LOG_FUNCTION (this);

  DataRate currentBW = m_currentBW;

  if (m_previousBW.GetBitRate () == 0)
    {
      NS_LOG_DEBUG ("Previous BW is zero, setting ratio to 1.0");
      return 1.0;
    }

  double ratio = static_cast<double> (currentBW.GetBitRate ()) /
                 static_cast<double> (m_previousBW.GetBitRate ());

  NS_LOG_DEBUG ("BWratio: " << ratio << " (current: " << currentBW << ", previous: "
                            << m_previousBW << ")");

  return ratio;
}

void
TcpModifiedTcoWestwoodPlusNew::CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  if (segmentsAcked > 0)
    {
      double bwRatio = CalculateBWRatio ();
      double adder = 0.0;

      if (bwRatio >= 1.5)
        {
          adder = 2.0 / static_cast<double> (tcb->m_cWnd.Get () / tcb->m_segmentSize);
          NS_LOG_DEBUG ("Network lightly loaded (BWratio >= 1.5), adder = 2/cwnd");
        }
      else if (bwRatio >= 1.0 && bwRatio < 1.5)
        {
          adder = 1.0 / static_cast<double> (tcb->m_cWnd.Get () / tcb->m_segmentSize);
          NS_LOG_DEBUG ("Normal network load (1.0 <= BWratio < 1.5), adder = 1/cwnd");
        }
      else
        {
          double gamma = 0.5;
          double decayFactor = 1.0 - gamma * (1.0 - bwRatio);
          decayFactor = std::max (decayFactor, 0.0);

          uint32_t newCwnd = static_cast<uint32_t> (tcb->m_cWnd.Get () * decayFactor);
          newCwnd = std::max (newCwnd, tcb->m_segmentSize);

          tcb->m_cWnd = newCwnd;

          NS_LOG_INFO ("Proportional decay applied: cwnd=" << tcb->m_cWnd
                                                             << " decayFactor=" << decayFactor
                                                             << " BWratio=" << bwRatio
                                                             << " gamma=" << gamma);

          m_previousBW = m_currentBW;
          return;
        }

      uint32_t cwndAdd = static_cast<uint32_t> (adder * tcb->m_segmentSize);
      tcb->m_cWnd += std::max (cwndAdd, 1u);

      NS_LOG_INFO ("Updated cwnd: " << tcb->m_cWnd << " (added: " << cwndAdd
                                     << " bytes, BWratio: " << bwRatio << ")");

      m_previousBW = m_currentBW;
    }
}

void
TcpModifiedTcoWestwoodPlusNew::PktsAcked (Ptr<TcpSocketState> tcb,
                                           uint32_t segmentsAcked,
                                           const Time& rtt)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked << rtt);

  TcpWestwoodPlus::PktsAcked (tcb, segmentsAcked, rtt);

  if (!rtt.IsZero ())
    {
      UpdateRtoEstimate (tcb);
      m_previousRtt = rtt;
    }
}

void
TcpModifiedTcoWestwoodPlusNew::UpdateRtoEstimate (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);

  if (!m_previousRtt.IsZero ())
    {
      Time currentRtt = tcb->m_lastRtt.Get ();
      double rttRatio = currentRtt.GetSeconds () / m_previousRtt.GetSeconds ();

      if (rttRatio > 1.5 || rttRatio < 0.5)
        {
          NS_LOG_DEBUG ("Significant RTT change detected (ratio: " << rttRatio << ")");
          m_linkRecovery = true;

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

          NS_LOG_INFO ("RTO estimate updated to " << newRto.GetSeconds ()
                                                   << "s (RTT ratio: " << rttRatio << ")");
        }
      else
        {
          m_linkRecovery = false;
          m_oldRto = Seconds (tcb->m_srtt.Get ().GetSeconds () * 2.0);
        }
    }
  else
    {
      Time srtt = tcb->m_srtt.Get ();
      if (!srtt.IsZero ())
        {
          m_oldRto = Seconds (srtt.GetSeconds () * 2.0);
        }
    }
}

} // namespace ns3