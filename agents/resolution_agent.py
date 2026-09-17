import uuid
from typing import Dict, Any, List, Optional
from services.data_service import DataService
from services.llm_provider import BaseLLMProvider, get_llm_provider
from core.policy_engine import PolicyEngine
from core.decision_engine import DecisionEngine, DecisionResult
from core.audit import AuditLogger
from agents.intent_agent import IntentAgent
from agents.response_agent import ResponseAgent
from tools.customer_tools import get_customer_profile
from tools.booking_tools import get_booking_status


class ResolutionAgent:
    """
    Main conversational resolution agent for airline disruptions.
    Guarantees strict policy grounding, zero hallucination, and full auditability.
    """

    def __init__(
        self,
        data_service: Optional[DataService] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.data_service = data_service or DataService()
        self.llm_provider = llm_provider or get_llm_provider()
        self.audit_logger = audit_logger or AuditLogger()
        self.policy_engine = PolicyEngine(data_service=self.data_service)
        self.decision_engine = DecisionEngine(policy_engine=self.policy_engine)
        self.intent_agent = IntentAgent()
        self.response_agent = ResponseAgent(llm_provider=self.llm_provider)

    def handle_message(
        self,
        customer_message: str,
        customer_id_or_pnr: Optional[str] = None,
        conversation_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        conv_id = conversation_id or f"CONV-{uuid.uuid4().hex[:8].upper()}"
        history = chat_history or []

        # 1. Parse Intent & Entities
        parsed_intent = self.intent_agent.parse(customer_message)

        # 2. Resolve Customer Profile and Booking Context
        # Check explicit parameter, or check parsed PNR from message
        lookup_key = customer_id_or_pnr or parsed_intent.get("detected_pnr")

        customer_context = None
        booking_context = None

        if lookup_key:
            customer_context = get_customer_profile(lookup_key, self.data_service)
            pnr = customer_context.get("booking_reference") if customer_context else lookup_key
            booking_context = get_booking_status(pnr, self.data_service)

        # If customer or booking could not be found, request identification
        if not customer_context or not booking_context:
            reply = (
                "Welcome to Airline Disruption Support. To assist you with your booking, "
                "could you please provide your 6-character Booking Reference (PNR) or your customer ID?"
            )
            # Log audit event for clarification
            self.audit_logger.record_event(
                conversation_id=conv_id,
                customer=customer_id_or_pnr or "Unidentified",
                pnr="UNKNOWN",
                intent="identity_clarification",
                policy_used=[],
                decision="Requested customer PNR identification",
                action=[],
                status="CLARIFY",
                reason="Missing booking reference or customer profile"
            )
            return {
                "conversation_id": conv_id,
                "status": "CLARIFY",
                "response": reply,
                "decision_result": None,
                "customer_context": None,
                "booking_context": None,
                "executed_actions": [],
                "escalation_record": None,
                "source_citations": []
            }

        # 3. Decision Processing (Policy Evaluation + Action Dispatch + Escalation Check)
        decision_result = self.decision_engine.process(
            customer_context=customer_context,
            booking_context=booking_context,
            parsed_intent=parsed_intent,
            conversation_id=conv_id
        )

        # 4. Generate Empathetic, Policy-Grounded Response
        response_text = self.response_agent.generate_response(
            customer_message=customer_message,
            chat_history=history,
            decision_result=decision_result,
            customer_context=customer_context,
            booking_context=booking_context
        )

        # 5. Record Audit Trail Event
        action_names = [a.get("action", "") for a in decision_result.executed_actions]
        if decision_result.escalation_record:
            action_names.append(f"escalate_to_{decision_result.escalation_record.escalation_target}")

        self.audit_logger.record_event(
            conversation_id=conv_id,
            customer=customer_context.get("name", "Unknown"),
            pnr=booking_context.get("pnr", "Unknown"),
            intent=", ".join(parsed_intent.get("intents", ["general_inquiry"])),
            policy_used=decision_result.policy_result.applicable_policies,
            decision=decision_result.decision_summary,
            action=action_names,
            status=decision_result.status,
            reason=decision_result.policy_result.explanation,
            source_citations=decision_result.policy_result.source_citations,
            extra={
                "frustration_detected": parsed_intent.get("is_frustrated"),
                "frustration_keywords": parsed_intent.get("frustration_keywords"),
                "is_legal_threat": parsed_intent.get("is_legal_threat"),
                "is_formal_complaint": parsed_intent.get("is_formal_complaint"),
                "executed_actions": decision_result.executed_actions,
                "escalation_record": decision_result.escalation_record.to_dict() if decision_result.escalation_record else None
            }
        )

        return {
            "conversation_id": conv_id,
            "status": decision_result.status,
            "response": response_text,
            "decision_result": decision_result.to_dict(),
            "customer_context": customer_context,
            "booking_context": booking_context,
            "executed_actions": decision_result.executed_actions,
            "escalation_record": decision_result.escalation_record.to_dict() if decision_result.escalation_record else None,
            "source_citations": decision_result.policy_result.source_citations
        }
