/*
 * Enhancements over TCP WestwoodPlus:
 * 1. Enhanced Congestion Avoidance with BWratio-based cwnd adjustment
 * 2. Modified RTO calculation based on RTT changes
 */

#ifndef TCP_WESTWOODPLUS_NEW_H
#define TCP_WESTWOODPLUS_NEW_H

#include "tcp-westwood-plus.h"

namespace ns3 {

class TcpWestwoodPlusNew : public TcpWestwoodPlus
{
public:
  static TypeId GetTypeId (void);

  TcpWestwoodPlusNew (void);
  TcpWestwoodPlusNew (const TcpWestwoodPlusNew& sock);
  ~TcpWestwoodPlusNew () override;

  virtual std::string GetName () const;
  virtual Ptr<TcpCongestionOps> Fork ();

protected:
  virtual void CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
  virtual void PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt);

private:
  double CalculateBWRatio (void);
  void UpdateRtoEstimate (Ptr<TcpSocketState> tcb);

  DataRate m_previousBW;           //!< Previous bandwidth estimate
  Time m_previousRtt;              //!< Previous RTT measurement
  Time m_oldRto;                   //!< Old RTO value before update
  bool m_linkRecovery;             //!< Flag indicating link recovery
};

} // namespace ns3

#endif /* TCP_WESTWOODPLUS_NEW_H */