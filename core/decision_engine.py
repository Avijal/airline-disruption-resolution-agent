from typing import Dict, Any, List, Optional
from core.policy_engine import PolicyEngine, PolicyEvaluationResult
from core.escalation import create_escalation_record, EscalationRecord
from tools.resolution_tools import (
    simulate_rebooking,
    simulate_issue_meal_voucher,
    simulate_grant_lounge_access,
    simulate_arrange_hotel,
    simulate_initiate_refund
)
from tools.escalation_tools import dispatch_escalation


class DecisionResult:
    def __init__(
        self,
        status: str,
        policy_result: PolicyEvaluationResult,
        executed_actions: List[Dict[str, Any]],
        escalation_record: Optional[EscalationRecord] = None,
        escalation_dispatch: Optional[Dict[str, Any]] = None,
        decision_summary: str = "",
        actions_summary: str = "",
        escalation_summary: str = "",
        tone_acknowledgment: str = ""
    ):
        self.status = status
        self.policy_result = policy_result
        self.executed_actions = executed_actions
        self.escalation_record = escalation_record
        self.escalation_dispatch = escalation_dispatch
        self.decision_summary = decision_summary
        self.actions_summary = actions_summary
        self.escalation_summary = escalation_summary
        self.tone_acknowledgment = tone_acknowledgment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "policy_result": self.policy_result.to_dict(),
            "executed_actions": self.executed_actions,
            "escalation_record": self.escalation_record.to_dict() if self.escalation_record else None,
            "escalation_dispatch": self.escalation_dispatch,
            "decision_summary": self.decision_summary,
            "actions_summary": self.actions_summary,
            "escalation_summary": self.escalation_summary,
            "tone_acknowledgment": self.tone_acknowledgment
        }


class DecisionEngine:
    """
    Executes business decisions by orchestrating the PolicyEngine with
    concrete action tools and human escalation workflows.
    """

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def process(
        self,
        customer_context: Dict[str, Any],
        booking_context: Dict[str, Any],
        parsed_intent: Dict[str, Any],
        conversation_id: str
    ) -> DecisionResult:
        policy_res = self.policy_engine.evaluate(
            customer_context=customer_context,
            booking_context=booking_context,
            customer_request=parsed_intent
        )

        # 1. Tone / Empathy calibration
        tone_ack = ""
        pnr = booking_context.get("pnr", "")
        segments = booking_context.get("segments", [])
        disrupted_segment = segments[0] if segments else {}
        flight_no = disrupted_segment.get("flight_number", "your flight")
        flight_status = disrupted_segment.get("status", "disrupted")

        if parsed_intent.get("is_frustrated"):
            tone_ack = f"I completely understand your frustration regarding the disruption to flight {flight_no}."
        elif flight_status == "Cancelled":
            tone_ack = f"I'm sorry for the inconvenience caused by the operational cancellation of flight {flight_no}."
        elif flight_status == "Delayed":
            tone_ack = f"I apologize for the delay to flight {flight_no}."

        # 2. Execute Allowed Action Tools
        executed_actions = []
        action_descriptions = []
        for allowed in policy_res.allowed_actions:
            action_name = allowed.get("action")
            if action_name == "initiate_refund":
                payment_method = allowed.get("method", "original payment method")
                act_res = simulate_initiate_refund(pnr=pnr, payment_method=payment_method)
                executed_actions.append(act_res)
                action_descriptions.append(act_res["summary"])
            elif action_name == "rebook_flight":
                priority_tier = customer_context.get("loyalty_tier", "Standard")
                act_res = simulate_rebooking(pnr=pnr, priority_tier=priority_tier)
                executed_actions.append(act_res)
                action_descriptions.append(act_res["summary"])
            elif action_name == "issue_meal_voucher":
                amount = allowed.get("amount_inr", 500)
                act_res = simulate_issue_meal_voucher(pnr=pnr, amount_inr=amount)
                executed_actions.append(act_res)
                action_descriptions.append(act_res["summary"])
            elif action_name == "grant_lounge_access":
                act_res = simulate_grant_lounge_access(pnr=pnr)
                executed_actions.append(act_res)
                action_descriptions.append(act_res["summary"])
            elif action_name == "arrange_hotel_delayed_hours":
                hours = allowed.get("duration_hours", 0.0)
                act_res = simulate_arrange_hotel(pnr=pnr, delay_hours=hours)
                executed_actions.append(act_res)
                action_descriptions.append(act_res["summary"])

        # 3. Handle Escalations
        escalation_record = None
        escalation_dispatch = None
        escalation_summary = ""

        if policy_res.escalation_required:
            escalation_record = create_escalation_record(
                customer_context=customer_context,
                booking_context=booking_context,
                policy_result=policy_res,
                conversation_id=conversation_id,
                user_message=parsed_intent.get("raw_message", "")
            )
            escalation_dispatch = dispatch_escalation(escalation_record)
            escalation_summary = (
                f"**Escalation Created:** Case escalated to `{escalation_record.escalation_target}`. "
                f"Reason: {escalation_record.reason_for_escalation} "
                f"Recommended human action: {escalation_record.recommended_human_action}"
            )

        # 4. Formulate Decision Summaries
        decision_summary = policy_res.explanation
        if policy_res.ineligible_requests:
            rejections = [f"- **{r.get('request')}**: {r.get('reason')}" for r in policy_res.ineligible_requests]
            decision_summary += "\n\n**Policy Clarification:**\n" + "\n".join(rejections)

        actions_summary = "\n".join(action_descriptions) if action_descriptions else ""

        return DecisionResult(
            status=policy_res.status,
            policy_result=policy_res,
            executed_actions=executed_actions,
            escalation_record=escalation_record,
            escalation_dispatch=escalation_dispatch,
            decision_summary=decision_summary,
            actions_summary=actions_summary,
            escalation_summary=escalation_summary,
            tone_acknowledgment=tone_ack
        )
