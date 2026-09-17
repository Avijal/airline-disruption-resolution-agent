from typing import Dict, Any, List, Optional
from services.data_service import DataService


class PolicyEvaluationResult:
    def __init__(
        self,
        status: str,
        applicable_policies: List[str],
        eligible_benefits: List[Dict[str, Any]],
        ineligible_requests: List[Dict[str, Any]],
        allowed_actions: List[Dict[str, Any]],
        prohibited_actions: List[Dict[str, Any]],
        escalation_required: bool = False,
        escalation_target: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        recommended_human_action: Optional[str] = None,
        source_citations: Optional[List[str]] = None,
        explanation: str = ""
    ):
        self.status = status  # "RESOLVED", "ESCALATED", "CLARIFY"
        self.applicable_policies = applicable_policies
        self.eligible_benefits = eligible_benefits
        self.ineligible_requests = ineligible_requests
        self.allowed_actions = allowed_actions
        self.prohibited_actions = prohibited_actions
        self.escalation_required = escalation_required
        self.escalation_target = escalation_target
        self.escalation_reason = escalation_reason
        self.recommended_human_action = recommended_human_action
        self.source_citations = source_citations or []
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "applicable_policies": self.applicable_policies,
            "eligible_benefits": self.eligible_benefits,
            "ineligible_requests": self.ineligible_requests,
            "allowed_actions": self.allowed_actions,
            "prohibited_actions": self.prohibited_actions,
            "escalation_required": self.escalation_required,
            "escalation_target": self.escalation_target,
            "escalation_reason": self.escalation_reason,
            "recommended_human_action": self.recommended_human_action,
            "source_citations": self.source_citations,
            "explanation": self.explanation
        }


class PolicyEngine:
    """
    Deterministic business policy evaluation engine.
    Strictly enforces rules from the Assignment Data Pack without hallucination.
    """

    def __init__(self, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService()

    def evaluate(
        self,
        customer_context: Optional[Dict[str, Any]],
        booking_context: Optional[Dict[str, Any]],
        customer_request: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """
        Evaluate customer request against customer profile, booking status,
        and official service policies.
        """
        policies = self.data_service.get_all_policies()
        citations = []
        applicable_policies = []
        eligible_benefits = []
        ineligible_requests = []
        allowed_actions = []
        prohibited_actions = []

        # 1. IMMEDIATE GUARDRAIL: Legal Threats or Formal Complaints
        if customer_request.get("is_legal_threat") or customer_request.get("is_formal_complaint"):
            citation = "Assignment 3 Data Pack, Section 4 'Allowed vs. Prohibited Actions' § Prohibited (Item 4)"
            citations.append(citation)
            applicable_policies.append("legal_or_formal_complaint")
            prohibited_actions.append({
                "rule": "Handling threats of legal action or formal complaints autonomously",
                "action": "legal_or_formal_complaint",
                "source": citation
            })
            return PolicyEvaluationResult(
                status="ESCALATED",
                applicable_policies=applicable_policies,
                eligible_benefits=[],
                ineligible_requests=[],
                allowed_actions=[],
                prohibited_actions=prohibited_actions,
                escalation_required=True,
                escalation_target="specialist_support_team",
                escalation_reason="Threat of legal action or formal complaint detected.",
                recommended_human_action="Transfer ticket immediately to the Specialist Support Team for legal/formal risk assessment and direct customer outreach.",
                source_citations=citations,
                explanation="Per airline policy, threats of legal action or formal complaints cannot be handled by automated agents and must be escalated immediately to specialist support."
            )

        # 2. Check if customer and booking exist
        if not customer_context or not booking_context:
            return PolicyEvaluationResult(
                status="CLARIFY",
                applicable_policies=[],
                eligible_benefits=[],
                ineligible_requests=[],
                allowed_actions=[],
                prohibited_actions=[],
                escalation_required=False,
                explanation="Booking or customer verification required before proceeding."
            )

        loyalty_tier = customer_context.get("loyalty_tier", "Standard")
        is_priority_tier = loyalty_tier in ["Gold", "Platinum"]
        segments = booking_context.get("segments", [])

        # Identify primary disrupted segment
        disrupted_segment = None
        for seg in segments:
            if seg.get("status") in ["Cancelled", "Delayed"]:
                disrupted_segment = seg
                break
        if not disrupted_segment and segments:
            disrupted_segment = segments[0]

        flight_status = disrupted_segment.get("status", "Unknown") if disrupted_segment else "Unknown"
        disruption_type = disrupted_segment.get("disruption_type", "none") if disrupted_segment else "none"
        delay_hours = float(disrupted_segment.get("delay_hours", 0.0)) if disrupted_segment else 0.0

        # 3. Guardrail: Non-airline-caused disruption
        if customer_request.get("is_non_airline_caused") or disruption_type == "passenger_caused":
            citation = "Assignment 3 Data Pack, Section 4 'Allowed vs. Prohibited Actions' § Prohibited (Item 3)"
            citations.append(citation)
            applicable_policies.append("non_airline_caused_exceptions")
            prohibited_actions.append({
                "rule": "Making exceptions for non-airline-caused disruptions",
                "source": citation
            })
            return PolicyEvaluationResult(
                status="ESCALATED",
                applicable_policies=applicable_policies,
                eligible_benefits=[],
                ineligible_requests=[{"request": "Compensation for non-airline disruption", "reason": "Not covered under policy"}],
                allowed_actions=[],
                prohibited_actions=prohibited_actions,
                escalation_required=True,
                escalation_target="human_specialist",
                escalation_reason="Requested exception for non-airline-caused disruption.",
                recommended_human_action="Review passenger circumstances and determine whether exceptional discretionary relief is warranted.",
                source_citations=citations,
                explanation="Policy prohibits autonomous agent exceptions for non-airline-caused disruptions (e.g. missed flight)."
            )

        # 4. Loyalty Tier Rules Evaluation
        if is_priority_tier:
            loyalty_cite = "Assignment 3 Data Pack, Section 3 'Service Rules' - Loyalty Tier Rule"
            if loyalty_cite not in citations:
                citations.append(loyalty_cite)
            applicable_policies.append("loyalty_tier")
            eligible_benefits.append({
                "benefit": "priority_rebooking",
                "description": f"{loyalty_tier} tier member entitled to priority rebooking (first access to next-available seats).",
                "source": loyalty_cite
            })

        # 5. Cancellation Evaluation
        if flight_status == "Cancelled" and disruption_type == "airline_caused":
            can_cite = "Assignment 3 Data Pack, Section 3 'Service Rules' - Cancellation Rebooking Rule"
            ref_cite = "Assignment 3 Data Pack, Section 3 'Service Rules' - Refund Processing Rule"
            citations.extend([can_cite, ref_cite])
            applicable_policies.extend(["cancellation_rebooking", "refund_processing"])

            eligible_benefits.append({
                "benefit": "free_rebooking",
                "description": "Free rebooking on the next available flight within 24 hours at no extra charge.",
                "priority_access": is_priority_tier,
                "source": can_cite
            })
            eligible_benefits.append({
                "benefit": "full_refund",
                "description": "Full refund processed within 7 business days to original payment method.",
                "source": ref_cite
            })

            # Check specific refund request
            if customer_request.get("wants_refund"):
                # Check payment method constraint
                if customer_request.get("alternate_payment_method_requested"):
                    alt_cite = "Assignment 3 Data Pack, Section 4 'Allowed vs. Prohibited Actions' § Prohibited (Item 5)"
                    citations.append(alt_cite)
                    prohibited_actions.append({
                        "rule": "Processing refunds to a different payment method than original",
                        "source": alt_cite
                    })
                    return PolicyEvaluationResult(
                        status="ESCALATED",
                        applicable_policies=applicable_policies,
                        eligible_benefits=eligible_benefits,
                        ineligible_requests=[{
                            "request": "Refund to alternate payment method",
                            "reason": "Policy strictly limits refunds to original payment method only"
                        }],
                        allowed_actions=[],
                        prohibited_actions=prohibited_actions,
                        escalation_required=True,
                        escalation_target="finance_supervisor",
                        escalation_reason="Customer requested refund to an alternate payment method.",
                        recommended_human_action="Verify identity and banking credentials before evaluating manual manual accounting override.",
                        source_citations=citations,
                        explanation="Refunds can only be processed to the original payment method. Alternate payment method requests require supervisor escalation."
                    )

                allowed_actions.append({
                    "action": "initiate_refund",
                    "pnr": booking_context.get("pnr"),
                    "amount": "full_ticket_value",
                    "method": booking_context.get("payment_method", "original payment method"),
                    "timeline": "7 business days",
                    "source": ref_cite
                })

            if customer_request.get("wants_rebooking"):
                allowed_actions.append({
                    "action": "rebook_flight",
                    "pnr": booking_context.get("pnr"),
                    "window": "within 24 hours",
                    "priority": is_priority_tier,
                    "cost": "free (no charge)",
                    "source": can_cite
                })

        # 6. Delay Compensation Evaluation
        elif flight_status == "Delayed" and disruption_type == "airline_caused":
            del_cite = "Assignment 3 Data Pack, Section 3 'Service Rules' - Delay Compensation Rule"
            citations.append(del_cite)
            applicable_policies.append("delay_compensation")

            if delay_hours < 3.0:
                eligible_benefits.append({
                    "benefit": "meal_voucher",
                    "amount_inr": 500,
                    "description": "₹500 meal voucher for delay under 3 hours",
                    "source": del_cite
                })
                allowed_actions.append({
                    "action": "issue_meal_voucher",
                    "pnr": booking_context.get("pnr"),
                    "amount_inr": 500,
                    "source": del_cite
                })
            elif 3.0 <= delay_hours <= 5.0:
                eligible_benefits.append({
                    "benefit": "meal_voucher",
                    "amount_inr": 500,
                    "description": "Meal voucher",
                    "source": del_cite
                })
                eligible_benefits.append({
                    "benefit": "lounge_access",
                    "description": "Airport lounge access during the delay",
                    "source": del_cite
                })
                allowed_actions.append({
                    "action": "issue_meal_voucher",
                    "pnr": booking_context.get("pnr"),
                    "amount_inr": 500,
                    "source": del_cite
                })
                allowed_actions.append({
                    "action": "grant_lounge_access",
                    "pnr": booking_context.get("pnr"),
                    "source": del_cite
                })
            elif delay_hours > 5.0:
                eligible_benefits.append({
                    "benefit": "meal_voucher",
                    "amount_inr": 500,
                    "description": "Meal voucher",
                    "source": del_cite
                })
                eligible_benefits.append({
                    "benefit": "lounge_access",
                    "description": "Airport lounge access",
                    "source": del_cite
                })
                eligible_benefits.append({
                    "benefit": "hotel_accommodation",
                    "scope": "delayed_hours_only",
                    "description": "Hotel accommodation covering only the delayed hours (not a full night's stay)",
                    "source": del_cite
                })
                allowed_actions.append({
                    "action": "issue_meal_voucher",
                    "pnr": booking_context.get("pnr"),
                    "amount_inr": 500,
                    "source": del_cite
                })
                allowed_actions.append({
                    "action": "grant_lounge_access",
                    "pnr": booking_context.get("pnr"),
                    "source": del_cite
                })
                allowed_actions.append({
                    "action": "arrange_hotel_delayed_hours",
                    "pnr": booking_context.get("pnr"),
                    "duration_hours": delay_hours,
                    "source": del_cite
                })

            # Check Hotel Request against Policy
            if customer_request.get("wants_hotel"):
                if delay_hours <= 5.0:
                    ineligible_requests.append({
                        "request": "Hotel accommodation",
                        "reason": f"Flight delay is {delay_hours} hours. Policy requires a delay of more than 5 hours to qualify for hotel accommodation.",
                        "source": del_cite
                    })
                elif delay_hours > 5.0:
                    if customer_request.get("wants_full_night_hotel"):
                        ineligible_requests.append({
                            "request": "Full night's hotel stay",
                            "reason": "Policy strictly limits hotel accommodation to covering only the delayed hours (not a full night's stay).",
                            "source": del_cite
                        })

        # 7. Upgrade Requests / Unsupported Compensation
        if customer_request.get("wants_upgrade"):
            comp_cite = "Assignment 3 Data Pack, Section 4 'Allowed vs. Prohibited Actions' § Prohibited (Item 1)"
            loy_cite = "Assignment 3 Data Pack, Section 3 'Service Rules' - Loyalty Tier Rule"
            citations.extend([comp_cite, loy_cite])
            prohibited_actions.append({
                "rule": "Approving compensation beyond stated policy amounts (complimentary cabin upgrade)",
                "source": comp_cite
            })
            ineligible_requests.append({
                "request": "Complimentary upgrade to business class",
                "reason": f"Under airline service rules, disruption policy does not include complimentary cabin upgrades. Loyalty tier ({loyalty_tier}) provides priority rebooking only, with no additional compensation beyond standard policy.",
                "source": comp_cite
            })

            # Mark escalation required for upgrade demand
            return PolicyEvaluationResult(
                status="ESCALATED",
                applicable_policies=applicable_policies,
                eligible_benefits=eligible_benefits,
                ineligible_requests=ineligible_requests,
                allowed_actions=allowed_actions,
                prohibited_actions=prohibited_actions,
                escalation_required=True,
                escalation_target="specialist_support_team",
                escalation_reason=f"Customer requested complimentary business-class upgrade, which exceeds agent authority and stated disruption policy.",
                recommended_human_action=f"Process eligible options (e.g. full refund/free rebooking) and inform customer that cabin upgrade exceptions require commercial supervisor sign-off.",
                source_citations=list(dict.fromkeys(citations)),
                explanation=f"Refund/rebooking is supported, but complimentary business class upgrade is prohibited beyond standard policy without supervisor authorization."
            )

        # 8. Fare Difference Waiver Requests
        if customer_request.get("wants_higher_fare_rebooking") or customer_request.get("fare_difference_amount", 0) > 0:
            fare_cite = "Assignment 3 Data Pack, Section 3 'Service Rules' - Fare Difference Rule"
            waiver_prohibit_cite = "Assignment 3 Data Pack, Section 4 'Allowed vs. Prohibited Actions' § Prohibited (Item 2)"
            citations.extend([fare_cite, waiver_prohibit_cite])
            applicable_policies.append("fare_difference")

            fare_diff = float(customer_request.get("fare_difference_amount", 0.0))
            wants_waiver = customer_request.get("wants_fare_waiver", False)

            if wants_waiver and fare_diff > 1500.0:
                prohibited_actions.append({
                    "rule": "Waiving a fare difference above ₹1,500 without supervisor approval",
                    "amount": fare_diff,
                    "limit": 1500,
                    "source": waiver_prohibit_cite
                })
                ineligible_requests.append({
                    "request": f"Waiver of ₹{fare_diff:,.0f} fare difference",
                    "reason": f"Agents cannot waive fare differences above ₹1,500 without supervisor approval.",
                    "source": fare_cite
                })
                return PolicyEvaluationResult(
                    status="ESCALATED",
                    applicable_policies=applicable_policies,
                    eligible_benefits=eligible_benefits,
                    ineligible_requests=ineligible_requests,
                    allowed_actions=allowed_actions,
                    prohibited_actions=prohibited_actions,
                    escalation_required=True,
                    escalation_target="supervisor",
                    escalation_reason=f"Requested waiver of ₹{fare_diff:,.0f} fare difference exceeds the ₹1,500 agent waiver authority.",
                    recommended_human_action=f"Supervisor review required to approve or deny fare difference waiver of ₹{fare_diff:,.0f} for rebooking on higher-fare flight.",
                    source_citations=list(dict.fromkeys(citations)),
                    explanation=f"Under the Fare Difference Rule, agents can only waive fare differences up to ₹1,500. A waiver of ₹{fare_diff:,.0f} requires supervisor escalation."
                )

        # 9. Clean deduplication of citations
        citations = list(dict.fromkeys(citations))

        # Determine overall status
        status = "RESOLVED"
        if ineligible_requests and not allowed_actions:
            explanation = "Requested services are not covered under standard policy."
        elif ineligible_requests and allowed_actions:
            explanation = "Eligible policy benefits have been approved and applied. Ineligible requests were declined in accordance with service rules."
        elif allowed_actions:
            explanation = "Eligible policy benefits have been approved and applied."
        else:
            explanation = "Customer status retrieved. Eligible benefits determined."

        return PolicyEvaluationResult(
            status=status,
            applicable_policies=applicable_policies,
            eligible_benefits=eligible_benefits,
            ineligible_requests=ineligible_requests,
            allowed_actions=allowed_actions,
            prohibited_actions=prohibited_actions,
            escalation_required=False,
            source_citations=citations,
            explanation=explanation
        )
