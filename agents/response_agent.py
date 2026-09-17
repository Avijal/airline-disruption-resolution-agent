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
1. ONLY state facts provided in the resolution context. NEVER invent flight numbers, airline policies, or compensation amounts.
2. If flight rebooking is eligible, explain priority access and state that the operational flight inventory system will assign the exact flight. Never hallucinate alternative flight numbers.
3. If an action was executed or simulated, inform the customer clearly.
4. If an item is outside policy authority or escalated (e.g. business class upgrade, fare waiver > ₹1,500, legal threat), explain the policy limit politely and confirm escalation to specialists/supervisors.
5. Keep the tone professional, calm, empathetic, and concise without over-apologizing.
6. Always mention the exact policy source reference provided in the context."""

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

        context_dict = {
            "status": decision_result.status,
            "tone_acknowledgment": decision_result.tone_acknowledgment,
            "decision_summary": decision_result.decision_summary,
            "actions_summary": decision_result.actions_summary,
            "escalation_summary": decision_result.escalation_summary,
            "citations": citation_str,
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
            f"Executed Actions:\n{decision_result.actions_summary}\n"
            f"Escalation Note:\n{decision_result.escalation_summary}\n"
            f"Policy Sources:\n{citation_str}\n"
            f"Customer Message: {customer_message}\n"
        )

        messages = [
            {"role": "user", "content": context_prompt}
        ]

        # Call provider with context kwargs
        response = self.llm_provider.generate(
            system_prompt=self.SYSTEM_PROMPT,
            messages=messages,
            resolution_context=context_dict
        )

        # Ensure citations and simulated markers are clearly visible if omitted
        if citation_str and "Source:" not in response:
            response += f"\n\n**Policy References:**\n{citation_str}"

        return response
