#include "tcp-dual-modified-tcp-westwoodplus-new.h"

#include "ns3/log.h"
#include "ns3/simulator.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpDualModifiedTcpWestwoodPlusNew");

NS_OBJECT_ENSURE_REGISTERED (TcpDualModifiedTcpWestwoodPlusNew);

TypeId
TcpDualModifiedTcpWestwoodPlusNew::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpDualModifiedTcpWestwoodPlusNew")
    .SetParent<TcpWestwoodPlus> ()
    .SetGroupName ("Internet")
    .AddConstructor<TcpDualModifiedTcpWestwoodPlusNew> ()
  ;
  return tid;
}

TcpDualModifiedTcpWestwoodPlusNew::TcpDualModifiedTcpWestwoodPlusNew (void)
  : TcpWestwoodPlus (),
    m_previousBW (0),
    m_previousRtt (Seconds (0)),
    m_oldRto (Seconds (0)),
    m_linkRecovery (false),
    m_alpha (0.125),
    m_smoothedRtt (Seconds (0))
{
  NS_LOG_FUNCTION (this);
}

TcpDualModifiedTcpWestwoodPlusNew::TcpDualModifiedTcpWestwoodPlusNew (
  const TcpDualModifiedTcpWestwoodPlusNew& sock)
  : TcpWestwoodPlus (sock),
    m_previousBW (sock.m_previousBW),
    m_previousRtt (sock.m_previousRtt),
    m_oldRto (sock.m_oldRto),
    m_linkRecovery (sock.m_linkRecovery),
    m_alpha (sock.m_alpha),
    m_smoothedRtt (sock.m_smoothedRtt)
{
  NS_LOG_FUNCTION (this);
}

TcpDualModifiedTcpWestwoodPlusNew::~TcpDualModifiedTcpWestwoodPlusNew (void)
{
  NS_LOG_FUNCTION (this);
}

std::string
TcpDualModifiedTcpWestwoodPlusNew::GetName () const
{
  return "TcpDualModifiedTcpWestwoodPlusNew";
}

Ptr<TcpCongestionOps>
TcpDualModifiedTcpWestwoodPlusNew::Fork ()
{
  NS_LOG_FUNCTION (this);
  return CopyObject<TcpDualModifiedTcpWestwoodPlusNew> (this);
}

double
TcpDualModifiedTcpWestwoodPlusNew::CalculateBWRatio (void)
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
TcpDualModifiedTcpWestwoodPlusNew::CongestionAvoidance (Ptr<TcpSocketState> tcb,
                                                         uint32_t segmentsAcked)
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
TcpDualModifiedTcpWestwoodPlusNew::PktsAcked (Ptr<TcpSocketState> tcb,
                                               uint32_t segmentsAcked,
                                               const Time& rtt)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked << rtt);

  TcpWestwoodPlus::PktsAcked (tcb, segmentsAcked, rtt);

  if (!rtt.IsZero ())
    {
      UpdateRtoEstimate (tcb);
    }
}

void
TcpDualModifiedTcpWestwoodPlusNew::UpdateRtoEstimate (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);

  Time currentRtt = tcb->m_lastRtt.Get ();
  if (currentRtt.IsZero ())
    {
      return;
    }

  if (m_smoothedRtt.IsZero ())
    {
      m_smoothedRtt = currentRtt;
    }
  else
    {
      double smoothed = m_alpha * currentRtt.GetSeconds () +
                        (1.0 - m_alpha) * m_smoothedRtt.GetSeconds ();
      m_smoothedRtt = Seconds (smoothed);
    }

  if (!m_previousRtt.IsZero ())
    {
      double rttRatio = m_smoothedRtt.GetSeconds () / m_previousRtt.GetSeconds ();
      Time scaledRto = Seconds (rttRatio * m_oldRto.GetSeconds ());

      Time minRto = MilliSeconds (200);
      Time maxRto = Seconds (60.0);

      if (scaledRto.Compare (minRto) < 0)
        {
          scaledRto = minRto;
        }
      else if (scaledRto.Compare (maxRto) > 0)
        {
          scaledRto = maxRto;
        }

      if (rttRatio > 1.5 || rttRatio < 0.5)
        {
          m_linkRecovery = true;
          m_oldRto = scaledRto;

          NS_LOG_INFO ("Smoothed adaptive RTO update: " << m_oldRto.GetSeconds ()
                                                          << "s (smoothed RTT ratio: "
                                                          << rttRatio << ")");
        }
      else
        {
          m_linkRecovery = false;
          m_oldRto = Seconds (m_smoothedRtt.GetSeconds () * 2.0);
        }
    }
  else
    {
      m_oldRto = Seconds (m_smoothedRtt.GetSeconds () * 2.0);
    }
    
  m_previousRtt = m_smoothedRtt;
}

} // namespace ns3