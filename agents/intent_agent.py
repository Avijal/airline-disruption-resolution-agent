import re
import json
import logging
from typing import Dict, Any, List, Optional
from services.llm_provider import BaseLLMProvider, DeterministicFallbackProvider

logger = logging.getLogger("airline_resolution_agent.intent")


class IntentAgent:
    """
    Analyzes natural language messages using LLM understanding when available,
    with a robust deterministic parser fallback.
    Extracts intents, entities, frustration markers, and escalation triggers.
    """

    FRUSTRATION_KEYWORDS = [
        "furious", "unacceptable", "ruined", "ridiculous", "angry",
        "horrible", "disaster", "terrible", "waste of time", "pissed", "fed up"
    ]

    LEGAL_KEYWORDS = [
        "legal action", "lawyer", "court", "sue", "attorney", "litigation"
    ]

    FORMAL_COMPLAINT_KEYWORDS = [
        "formal complaint", "official complaint", "consumer forum", "dgca", "aviation authority"
    ]

    PNR_STOPWORDS = {
        "FLIGHT", "CANCEL", "TICKET", "RETURN", "DELHI", "MUMBAI", "STATUS",
        "HOURS", "MINUTES", "REFUND", "REBOOK", "HOTEL", "LOUNGE", "MEALS",
        "AIRLINE", "GROUND", "SYSTEM", "PERSON"
    }

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    def parse(self, message: str, customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # If live LLM provider is available, use LLM for semantic extraction
        if self.llm_provider and not isinstance(self.llm_provider, DeterministicFallbackProvider):
            llm_result = self._parse_with_llm(message)
            if llm_result:
                return llm_result

        # Deterministic semantic parser
        return self._parse_deterministic(message)

    def _parse_with_llm(self, message: str) -> Optional[Dict[str, Any]]:
        system_prompt = """You are an NLP entity and intent extraction engine for an airline customer support agent.
Analyze the customer's message and return ONLY a valid JSON object with these exact keys:
{
  "intents": ["request_refund" | "request_rebooking" | "request_hotel" | "request_amenities" | "request_upgrade" | "request_fare_waiver" | "legal_threat" | "formal_complaint" | "status_query" | "general_inquiry"],
  "is_frustrated": true/false,
  "frustration_keywords": ["extracted words indicating anger/distress"],
  "is_legal_threat": true/false (true if customer threatens legal action, lawsuit, court, lawyer),
  "is_formal_complaint": true/false (true if customer threatens formal regulatory complaints),
  "wants_refund": true/false,
  "wants_rebooking": true/false,
  "wants_hotel": true/false,
  "wants_full_night_hotel": true/false (true if customer specifically asks for full night, overnight, or whole night stay),
  "wants_upgrade": true/false (true if customer asks for business class or cabin upgrade),
  "wants_higher_fare_rebooking": true/false,
  "wants_fare_waiver": true/false (true if asking to waive fare difference or rebook on higher fare flight without paying),
  "fare_difference_amount": float or 0.0 (e.g. 2000.0 if ₹2,000 is mentioned),
  "alternate_payment_method_requested": true/false (true if refund to different card/cash is requested),
  "detected_pnr": string or null
}
Return ONLY the raw JSON object. No explanation or markdown fences."""

        try:
            response_text = self.llm_provider.generate(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": message}]
            )
            clean_json = response_text.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?", "", clean_json)
                clean_json = re.sub(r"```$", "", clean_json).strip()
            data = json.loads(clean_json)
            data["raw_message"] = message
            return data
        except Exception as e:
            logger.warning(f"LLM intent parsing failed or returned non-JSON: {e}. Falling back to deterministic parser.")
            return None

    def _parse_deterministic(self, message: str) -> Dict[str, Any]:
        msg_lower = message.lower()

        # 1. Detect Frustration
        detected_frustration = [w for w in self.FRUSTRATION_KEYWORDS if w in msg_lower]
        is_frustrated = len(detected_frustration) > 0

        # 2. Detect Legal Threats and Formal Complaints
        is_legal_threat = any(w in msg_lower for w in self.LEGAL_KEYWORDS)
        is_formal_complaint = any(w in msg_lower for w in self.FORMAL_COMPLAINT_KEYWORDS)

        # 3. Extract PNR (alphanumeric, containing both letters & numbers)
        detected_pnr = None
        pnr_candidates = re.findall(r"\b([A-Z0-9]{5,7})\b", message.upper())
        for cand in pnr_candidates:
            if cand not in self.PNR_STOPWORDS and any(c.isdigit() for c in cand) and any(c.isalpha() for c in cand):
                detected_pnr = cand
                break

        # 4. Extract Fare Difference Amount
        fare_amount = 0.0
        fare_match = re.search(r"(?:₹|rs\.?|inr)\s*([0-9]{1,2}(?:,[0-9]{3})+|[0-9]+)", message, re.IGNORECASE)
        if not fare_match:
            fare_match = re.search(r"(?:fare\s+difference\s+(?:is|of)?\s*|difference\s+(?:is|of)?\s*)([0-9]{1,2}(?:,[0-9]{3})+|[0-9]+)", message, re.IGNORECASE)

        if fare_match:
            clean_num = fare_match.group(1).replace(",", "")
            fare_amount = float(clean_num)

        # 5. Classify Request Entities and Intents
        wants_refund = any(w in msg_lower for w in ["refund", "money back", "cash refund", "cancel and refund"])
        wants_rebooking = any(w in msg_lower for w in [
            "rebook", "next flight", "another flight", "change flight", "alternative flight",
            "moved onto a different", "moved to a different", "different flight", "higher-fare flight",
            "different, higher-fare"
        ])
        wants_hotel = any(w in msg_lower for w in ["hotel", "room", "accommodation", "stay"])
        wants_full_night_hotel = wants_hotel and any(w in msg_lower for w in ["full night", "night's stay", "night stay", "overnight", "entire night", "whole night"])
        wants_meal_voucher = any(w in msg_lower for w in ["meal", "food", "voucher", "refreshment", "eat"])
        wants_lounge = any(w in msg_lower for w in ["lounge", "lounge access"])
        wants_upgrade = any(w in msg_lower for w in ["upgrade", "business class", "business-class", "higher class", "first class"])
        wants_fare_waiver = fare_amount > 0 or any(w in msg_lower for w in ["waive", "waiver", "without paying", "free move", "waive the fare", "cover the difference", "higher-fare"])
        alternate_payment = wants_refund and any(w in msg_lower for w in ["different account", "another card", "cash instead", "alternate account", "different payment", "different method"])
        is_status_query = any(w in msg_lower for w in ["status", "what happened", "is it cancelled", "is it delayed", "tell me about my flight", "booking details"])

        intents = []
        if is_legal_threat:
            intents.append("legal_threat")
        if is_formal_complaint:
            intents.append("formal_complaint")
        if wants_refund:
            intents.append("request_refund")
        if wants_rebooking or fare_amount > 0:
            intents.append("request_rebooking")
        if wants_hotel:
            intents.append("request_hotel")
        if wants_upgrade:
            intents.append("request_upgrade")
        if wants_fare_waiver:
            intents.append("request_fare_waiver")
        if wants_meal_voucher or wants_lounge:
            intents.append("request_amenities")
        if is_status_query and not intents:
            intents.append("status_query")
        if not intents:
            intents.append("general_inquiry")

        return {
            "intents": intents,
            "is_frustrated": is_frustrated,
            "frustration_keywords": detected_frustration,
            "is_legal_threat": is_legal_threat,
            "is_formal_complaint": is_formal_complaint,
            "wants_refund": wants_refund,
            "wants_rebooking": wants_rebooking or (fare_amount > 0),
            "wants_hotel": wants_hotel,
            "wants_full_night_hotel": wants_full_night_hotel,
            "wants_upgrade": wants_upgrade,
            "wants_higher_fare_rebooking": (wants_rebooking or fare_amount > 0) and fare_amount > 0,
            "wants_fare_waiver": wants_fare_waiver,
            "fare_difference_amount": fare_amount,
            "alternate_payment_method_requested": alternate_payment,
            "detected_pnr": detected_pnr,
            "raw_message": message
        }
