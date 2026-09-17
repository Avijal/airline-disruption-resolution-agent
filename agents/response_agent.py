from typing import Dict, Any, List, Optional
from core.decision_engine import DecisionResult
from services.llm_provider import BaseLLMProvider


class ResponseAgent:
    """
    Synthesizes conversational, empathetic responses strictly grounded
    in the deterministic PolicyEngine evaluation and executed tools.
    """

    SYSTEM_PROMPT = """You are an official Airline Disruption Customer Support Agent.
Your responsibility is to assist disrupted passengers empathetically, concisely, and strictly according to airline service policies.

CRITICAL OPERATIONAL RULES:
1. STRICT TRUTH IN ACTION EXECUTION:
   - ONLY state that an action was executed, rebooked, refunded, or issued IF it is explicitly listed under 'Executed Actions:'.
   - If 'Executed Actions:' is None or empty, you MUST NOT claim or imply that a rebooking occurred, a refund was initiated, or a voucher was created.
   - For flight cancellations: clearly explain that the passenger is entitled to choose between priority rebooking OR a full refund. Ask which option they prefer before proceeding.
2. GREETINGS & INITIAL CONTACT:
   - If the customer message is a greeting (e.g. 'hi', 'hello'), greet them warmly by name, acknowledge their flight and disruption status in one concise sentence, and ask how you can help them today.
   - Do NOT execute or claim to have executed any rebooking, refund, or vouchers on a greeting.
3. ZERO HALLUCINATION OF FLIGHTS & POLICIES:
   - NEVER invent flight numbers (e.g. SK-999), schedules, or alternative routes.
   - When rebooking is discussed, explain that the operational flight inventory system will assign the exact seat once confirmed.
4. ESCALATIONS:
   - If an item exceeds policy authority (e.g. cabin upgrade, fare difference > ₹1,500, legal threat), explain the policy limit politely and confirm escalation to a supervisor or specialist support.
5. CONCISE & EMPATHETIC:
   - Keep responses professional, warm, and concise (under 120 words). Never contradict yourself."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    def generate_response(
        self,
        customer_message: str,
        chat_history: List[Dict[str, str]],
        decision_result: DecisionResult,
        customer_context: Dict[str, Any],
        booking_context: Dict[str, Any]
    ) -> str:
        citations = decision_result.policy_result.source_citations
        citation_str = "\n".join([f"- Source: {c}" for c in citations]) if citations else ""

        executed_str = decision_result.actions_summary.strip() if decision_result.actions_summary.strip() else "None (no actions executed this turn)"

        context_dict = {
            "status": decision_result.status,
            "tone_acknowledgment": decision_result.tone_acknowledgment,
            "decision_summary": decision_result.decision_summary,
            "actions_summary": executed_str,
            "escalation_summary": decision_result.escalation_summary or "None",
            "citations": citation_str or "None",
            "customer_name": customer_context.get("name", "Customer"),
            "loyalty_tier": customer_context.get("loyalty_tier", "Standard"),
            "pnr": booking_context.get("pnr", "")
        }

        # Build prompt for LLM
        context_prompt = (
            f"RESOLUTION CONTEXT:\n"
            f"Status: {decision_result.status}\n"
            f"Customer: {context_dict['customer_name']} (Tier: {context_dict['loyalty_tier']})\n"
            f"PNR: {context_dict['pnr']}\n"
            f"Acknowledgment: {decision_result.tone_acknowledgment}\n"
            f"Policy Decision: {decision_result.decision_summary}\n"
            f"Executed Actions (ONLY claim an action happened if listed here):\n{executed_str}\n"
            f"Escalation Note:\n{context_dict['escalation_summary']}\n"
            f"Policy Sources:\n{citation_str or 'None'}\n"
            f"Customer Message: {customer_message}\n"
        )

        messages = []
        # Include past turns for multi-turn conversational coherence
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": context_prompt})

        # Call provider with context kwargs
        response = self.llm_provider.generate(
            system_prompt=self.SYSTEM_PROMPT,
            messages=messages,
            resolution_context=context_dict
        )

        # Ensure citations are included if policy citations exist and were omitted
        if citation_str and "Source:" not in response and "Policy Reference" not in response:
            response += f"\n\n**Policy References:**\n{citation_str}"

        return response
