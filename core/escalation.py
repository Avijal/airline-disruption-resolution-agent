import datetime
from typing import Dict, Any, Optional


class EscalationRecord:
    def __init__(
        self,
        customer_name: str,
        booking_reference: str,
        issue: str,
        requested_action: str,
        policy_limitation: str,
        reason_for_escalation: str,
        recommended_human_action: str,
        escalation_target: str = "specialist_support_team",
        conversation_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.customer_name = customer_name
        self.booking_reference = booking_reference
        self.issue = issue
        self.requested_action = requested_action
        self.policy_limitation = policy_limitation
        self.reason_for_escalation = reason_for_escalation
        self.recommended_human_action = recommended_human_action
        self.escalation_target = escalation_target
        self.conversation_id = conversation_id or "CONV-AUTO"
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer": self.customer_name,
            "booking_reference": self.booking_reference,
            "issue": self.issue,
            "requested_action": self.requested_action,
            "policy_limitation": self.policy_limitation,
            "reason_for_escalation": self.reason_for_escalation,
            "recommended_human_action": self.recommended_human_action,
            "escalation_target": self.escalation_target,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp
        }


def create_escalation_record(
    customer_context: Dict[str, Any],
    booking_context: Dict[str, Any],
    policy_result: Any,
    conversation_id: str,
    user_message: str
) -> EscalationRecord:
    cust_name = customer_context.get("name", "Unknown Customer")
    pnr = booking_context.get("pnr", "Unknown PNR")

    issue = f"Disruption on PNR {pnr}"
    segments = booking_context.get("segments", [])
    if segments:
        s = segments[0]
        issue += f" ({s.get('flight_number')} - {s.get('status')})"

    requested_action = user_message
    if policy_result.ineligible_requests:
        requested_action = "; ".join([r.get("request", "") for r in policy_result.ineligible_requests])

    policy_limitation = "; ".join([r.get("reason", "") for r in policy_result.ineligible_requests]) or "Request exceeds standard agent operating boundaries."
    reason = policy_result.escalation_reason or "Escalation triggered by policy rule."
    target = policy_result.escalation_target or "human_specialist"
    recommended_action = policy_result.recommended_human_action or "Review case facts and provide customer response."

    return EscalationRecord(
        customer_name=cust_name,
        booking_reference=pnr,
        issue=issue,
        requested_action=requested_action,
        policy_limitation=policy_limitation,
        reason_for_escalation=reason,
        recommended_human_action=recommended_action,
        escalation_target=target,
        conversation_id=conversation_id
    )
