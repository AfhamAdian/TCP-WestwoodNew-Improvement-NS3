/*
 * Modified TCO TCP WestwoodPlus New variant.
 */

#ifndef TCP_MODIFIED_TCO_WESTWOODPLUS_NEW_H
#define TCP_MODIFIED_TCO_WESTWOODPLUS_NEW_H

#include "tcp-westwood-plus.h"

namespace ns3 {

class TcpModifiedTcoWestwoodPlusNew : public TcpWestwoodPlus
{
public:
  static TypeId GetTypeId (void);

  TcpModifiedTcoWestwoodPlusNew (void);
  TcpModifiedTcoWestwoodPlusNew (const TcpModifiedTcoWestwoodPlusNew& sock);
  ~TcpModifiedTcoWestwoodPlusNew () override;

  std::string GetName () const override;
  Ptr<TcpCongestionOps> Fork () override;

protected:
  void CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked) override;
  void PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt) override;

private:
  double CalculateBWRatio (void);
  void UpdateRtoEstimate (Ptr<TcpSocketState> tcb);

  DataRate m_previousBW;  //!< Previous bandwidth estimate
  Time m_previousRtt;     //!< Previous RTT measurement
  Time m_oldRto;          //!< Old RTO value before update
  bool m_linkRecovery;    //!< Flag indicating link recovery
};

} // namespace ns3

#endif /* TCP_MODIFIED_TCO_WESTWOODPLUS_NEW_H */