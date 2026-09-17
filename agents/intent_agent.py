import re
from typing import Dict, Any, List, Optional


class IntentAgent:
    """
    Analyzes natural language messages to extract intents, entities,
    frustration markers, and policy escalation triggers.
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

    def parse(self, message: str, customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        msg_lower = message.lower()

        # 1. Detect Frustration
        detected_frustration = [w for w in self.FRUSTRATION_KEYWORDS if w in msg_lower]
        is_frustrated = len(detected_frustration) > 0

        # 2. Detect Legal Threats and Formal Complaints
        is_legal_threat = any(w in msg_lower for w in self.LEGAL_KEYWORDS)
        is_formal_complaint = any(w in msg_lower for w in self.FORMAL_COMPLAINT_KEYWORDS)

        # 3. Extract PNR (alphanumeric, containing both letters & numbers, e.g. SK4821X, TR1190B, WL7742)
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
