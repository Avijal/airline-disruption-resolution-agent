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
    Dynamic, policy-grounded business rules engine.
    Derives all decisions, thresholds, and entitlements dynamically from
    the data layer (policies.json and actions.json). Zero hardcoded business logic.
    """

    def __init__(self, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService()

    def evaluate(
        self,
        customer_context: Optional[Dict[str, Any]],
        booking_context: Optional[Dict[str, Any]],
        customer_request: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        policies = self.data_service.get_all_policies()
        actions_data = self.data_service.get_actions()

        prohibited_defs = actions_data.get("prohibited_actions", [])
        allowed_defs = actions_data.get("allowed_actions", [])

        citations = []
        applicable_policies = []
        eligible_benefits = []
        ineligible_requests = []
        allowed_actions = []
        prohibited_actions = []

        # 1. DYNAMIC GUARDRAIL: Legal Threats or Formal Complaints
        legal_prohibit_def = next((p for p in prohibited_defs if p.get("name") == "legal_or_formal_complaint"), None)
        if customer_request.get("is_legal_threat") or customer_request.get("is_formal_complaint"):
            cite = legal_prohibit_def.get("source_document") if legal_prohibit_def else "Allowed vs. Prohibited Actions § Prohibited"
            citations.append(cite)
            applicable_policies.append("legal_or_formal_complaint")
            prohibited_actions.append({
                "rule": legal_prohibit_def.get("description", "Handling threats of legal action or formal complaints"),
                "action": "legal_or_formal_complaint",
                "source": cite
            })
            return PolicyEvaluationResult(
                status="ESCALATED",
                applicable_policies=applicable_policies,
                eligible_benefits=[],
                ineligible_requests=[],
                allowed_actions=[],
                prohibited_actions=prohibited_actions,
                escalation_required=True,
                escalation_target=legal_prohibit_def.get("escalation_target", "specialist_support_team") if legal_prohibit_def else "specialist_support_team",
                escalation_reason="Threat of legal action or formal complaint detected.",
                recommended_human_action="Transfer ticket immediately to the Specialist Support Team for legal risk assessment and direct customer outreach.",
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

        # Extract dynamic policy objects
        cancel_policy = policies.get("cancellation_rebooking", {})
        delay_policy = policies.get("delay_compensation", {})
        refund_policy = policies.get("refund_processing", {})
        fare_policy = policies.get("fare_difference", {})
        loyalty_policy = policies.get("loyalty_tier", {})

        priority_tiers = loyalty_policy.get("priority_rebooking_tiers", ["Gold", "Platinum"])
        loyalty_tier = customer_context.get("loyalty_tier", "Standard")
        is_priority_tier = loyalty_tier in priority_tiers

        segments = booking_context.get("segments", [])
        disrupted_segment = next((s for s in segments if s.get("status") in ["Cancelled", "Delayed"]), None)
        if not disrupted_segment and segments:
            disrupted_segment = segments[0]

        flight_status = disrupted_segment.get("status", "Unknown") if disrupted_segment else "Unknown"
        disruption_type = disrupted_segment.get("disruption_type", "none") if disrupted_segment else "none"
        delay_hours = float(disrupted_segment.get("delay_hours", 0.0)) if disrupted_segment else 0.0

        # 3. Dynamic Guardrail: Non-airline-caused disruption
        non_airline_prohibit = next((p for p in prohibited_defs if p.get("name") == "non_airline_caused_exceptions"), None)
        if customer_request.get("is_non_airline_caused") or disruption_type == "passenger_caused":
            cite = non_airline_prohibit.get("source_document") if non_airline_prohibit else "Allowed vs. Prohibited Actions § Prohibited"
            citations.append(cite)
            applicable_policies.append("non_airline_caused_exceptions")
            prohibited_actions.append({
                "rule": non_airline_prohibit.get("description", "Exceptions for non-airline-caused disruptions"),
                "source": cite
            })
            return PolicyEvaluationResult(
                status="ESCALATED",
                applicable_policies=applicable_policies,
                eligible_benefits=[],
                ineligible_requests=[{"request": "Compensation for non-airline disruption", "reason": "Not covered under policy"}],
                allowed_actions=[],
                prohibited_actions=prohibited_actions,
                escalation_required=True,
                escalation_target=non_airline_prohibit.get("escalation_target", "human_specialist") if non_airline_prohibit else "human_specialist",
                escalation_reason="Requested exception for non-airline-caused disruption.",
                recommended_human_action="Review passenger circumstances and determine whether discretionary relief is warranted.",
                source_citations=citations,
                explanation="Policy prohibits autonomous agent exceptions for non-airline-caused disruptions (e.g. missed flight)."
            )

        # 4. Loyalty Tier Rules Evaluation
        if is_priority_tier:
            loyalty_cite = loyalty_policy.get("source_document", "Service Rules § Loyalty Tier Rule")
            citations.append(loyalty_cite)
            applicable_policies.append("loyalty_tier")
            eligible_benefits.append({
                "benefit": "priority_rebooking",
                "description": f"{loyalty_tier} tier member entitled to priority rebooking (first access to next-available seats).",
                "source": loyalty_cite
            })

        # 5. Cancellation Policy Evaluation (Driven by policies.json)
        if flight_status == "Cancelled" and disruption_type == "airline_caused":
            can_cite = cancel_policy.get("source_document", "Service Rules § Cancellation Rebooking Rule")
            ref_cite = refund_policy.get("source_document", "Service Rules § Refund Processing Rule")
            citations.extend([can_cite, ref_cite])
            applicable_policies.extend(["cancellation_rebooking", "refund_processing"])

            rebook_window = cancel_policy.get("entitlements", {}).get("free_rebooking_window_hours", 24)
            eligible_benefits.append({
                "benefit": "free_rebooking",
                "description": f"Free rebooking on the next available flight within {rebook_window} hours at no extra charge.",
                "priority_access": is_priority_tier,
                "source": can_cite
            })

            processing_days = refund_policy.get("processing_time_business_days", 7)
            payment_rule = refund_policy.get("payment_method_constraint", "original_payment_method_only")
            eligible_benefits.append({
                "benefit": "full_refund",
                "description": f"Full refund processed within {processing_days} business days to original payment method.",
                "source": ref_cite
            })

            # Check specific refund request
            if customer_request.get("wants_refund"):
                alt_pay_prohibit = next((p for p in prohibited_defs if p.get("name") == "refund_to_alternate_payment"), None)
                if customer_request.get("alternate_payment_method_requested"):
                    cite = alt_pay_prohibit.get("source_document") if alt_pay_prohibit else "Allowed vs. Prohibited Actions § Prohibited"
                    citations.append(cite)
                    prohibited_actions.append({
                        "rule": alt_pay_prohibit.get("description", "Processing refunds to a different payment method"),
                        "source": cite
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
                        escalation_target=alt_pay_prohibit.get("escalation_target", "finance_supervisor") if alt_pay_prohibit else "finance_supervisor",
                        escalation_reason="Customer requested refund to an alternate payment method.",
                        recommended_human_action="Verify identity and banking credentials before evaluating accounting override.",
                        source_citations=citations,
                        explanation="Refunds can only be processed to the original payment method. Alternate payment method requests require supervisor escalation."
                    )

                allowed_actions.append({
                    "action": "initiate_refund",
                    "pnr": booking_context.get("pnr"),
                    "amount": "full_ticket_value",
                    "method": booking_context.get("payment_method", "original payment method"),
                    "timeline": f"{processing_days} business days",
                    "source": ref_cite
                })

            if customer_request.get("wants_rebooking"):
                allowed_actions.append({
                    "action": "rebook_flight",
                    "pnr": booking_context.get("pnr"),
                    "window": f"within {rebook_window} hours",
                    "priority": is_priority_tier,
                    "cost": "free (no charge)",
                    "source": can_cite
                })

        # 6. Delay Compensation Policy Evaluation (Driven dynamically by tiers in policies.json)
        elif flight_status == "Delayed" and disruption_type == "airline_caused":
            del_cite = delay_policy.get("source_document", "Service Rules § Delay Compensation Rule")
            citations.append(del_cite)
            applicable_policies.append("delay_compensation")

            # Match matching tier dynamically from policy tiers
            matched_tier = None
            for tier in delay_policy.get("tiers", []):
                min_h = tier.get("min_delay_exclusive_hours", 0.0)
                max_h = tier.get("max_delay_inclusive_hours")
                if max_h is not None:
                    if min_h < delay_hours <= max_h:
                        matched_tier = tier
                        break
                else:
                    if delay_hours > min_h:
                        matched_tier = tier
                        break

            if matched_tier:
                if matched_tier.get("meal_voucher"):
                    amt = matched_tier.get("meal_voucher_amount_inr", 500)
                    eligible_benefits.append({
                        "benefit": "meal_voucher",
                        "amount_inr": amt,
                        "description": f"Meal voucher (₹{amt})",
                        "source": del_cite
                    })
                    allowed_actions.append({
                        "action": "issue_meal_voucher",
                        "pnr": booking_context.get("pnr"),
                        "amount_inr": amt,
                        "source": del_cite
                    })

                if matched_tier.get("lounge_access"):
                    eligible_benefits.append({
                        "benefit": "lounge_access",
                        "description": "Airport lounge access during delay",
                        "source": del_cite
                    })
                    allowed_actions.append({
                        "action": "grant_lounge_access",
                        "pnr": booking_context.get("pnr"),
                        "source": del_cite
                    })

                if matched_tier.get("hotel_accommodation"):
                    eligible_benefits.append({
                        "benefit": "hotel_accommodation",
                        "scope": matched_tier.get("hotel_scope", "delayed_hours_only"),
                        "description": "Hotel accommodation covering only the delayed hours (not a full night's stay)",
                        "source": del_cite
                    })
                    allowed_actions.append({
                        "action": "arrange_hotel_delayed_hours",
                        "pnr": booking_context.get("pnr"),
                        "duration_hours": delay_hours,
                        "source": del_cite
                    })

            # Check Hotel Request against Dynamic Policy
            if customer_request.get("wants_hotel"):
                hotel_qualifying_tier = next((t for t in delay_policy.get("tiers", []) if t.get("hotel_accommodation")), None)
                min_hotel_delay = hotel_qualifying_tier.get("min_delay_exclusive_hours", 5.0) if hotel_qualifying_tier else 5.0

                if delay_hours <= min_hotel_delay:
                    ineligible_requests.append({
                        "request": "Hotel accommodation",
                        "reason": f"Flight delay is {delay_hours} hours. Policy requires a delay of more than {min_hotel_delay:g} hours to qualify for hotel accommodation.",
                        "source": del_cite
                    })
                elif delay_hours > min_hotel_delay and customer_request.get("wants_full_night_hotel"):
                    ineligible_requests.append({
                        "request": "Full night's hotel stay",
                        "reason": "Policy strictly limits hotel accommodation to covering only the delayed hours (not a full night's stay).",
                        "source": del_cite
                    })

        # 7. Unsupported Compensation / Cabin Upgrade (Driven by actions.json & policies.json)
        if customer_request.get("wants_upgrade"):
            excess_prohibit = next((p for p in prohibited_defs if p.get("name") == "compensation_beyond_policy"), None)
            comp_cite = excess_prohibit.get("source_document") if excess_prohibit else "Allowed vs. Prohibited Actions § Prohibited"
            loy_cite = loyalty_policy.get("source_document", "Service Rules § Loyalty Tier Rule")
            citations.extend([comp_cite, loy_cite])

            prohibited_actions.append({
                "rule": excess_prohibit.get("description", "Approving compensation beyond stated policy amounts"),
                "source": comp_cite
            })
            ineligible_requests.append({
                "request": "Complimentary upgrade to business class",
                "reason": f"Under airline service rules, disruption policy does not include complimentary cabin upgrades. Loyalty tier ({loyalty_tier}) provides priority rebooking only, with no additional compensation beyond standard policy.",
                "source": comp_cite
            })

            return PolicyEvaluationResult(
                status="ESCALATED",
                applicable_policies=applicable_policies,
                eligible_benefits=eligible_benefits,
                ineligible_requests=ineligible_requests,
                allowed_actions=allowed_actions,
                prohibited_actions=prohibited_actions,
                escalation_required=True,
                escalation_target=excess_prohibit.get("escalation_target", "specialist_support_team") if excess_prohibit else "specialist_support_team",
                escalation_reason="Customer requested complimentary business-class upgrade, which exceeds agent authority and stated disruption policy.",
                recommended_human_action="Process eligible options (e.g. full refund/free rebooking) and inform customer that cabin upgrade exceptions require commercial supervisor sign-off.",
                source_citations=list(dict.fromkeys(citations)),
                explanation="Refund/rebooking is supported, but complimentary business class upgrade is prohibited beyond standard policy without supervisor authorization."
            )

        # 8. Fare Difference Waiver Requests (Driven by fare_difference policy & actions.json)
        if customer_request.get("wants_higher_fare_rebooking") or customer_request.get("fare_difference_amount", 0) > 0:
            fare_cite = fare_policy.get("source_document", "Service Rules § Fare Difference Rule")
            fare_waiver_prohibit = next((p for p in prohibited_defs if p.get("name") == "waiving_fare_difference_above_1500"), None)
            waiver_prohibit_cite = fare_waiver_prohibit.get("source_document") if fare_waiver_prohibit else "Allowed vs. Prohibited Actions § Prohibited"
            citations.extend([fare_cite, waiver_prohibit_cite])
            applicable_policies.append("fare_difference")

            max_agent_waiver = float(fare_policy.get("agent_max_waiver_inr", 1500.0))
            fare_diff = float(customer_request.get("fare_difference_amount", 0.0))

            if fare_diff > max_agent_waiver:
                prohibited_actions.append({
                    "rule": fare_waiver_prohibit.get("description", f"Waiving a fare difference above ₹{max_agent_waiver:,.0f} without supervisor approval"),
                    "amount": fare_diff,
                    "limit": max_agent_waiver,
                    "source": waiver_prohibit_cite
                })
                ineligible_requests.append({
                    "request": f"Waiver of ₹{fare_diff:,.0f} fare difference",
                    "reason": f"Agents cannot waive fare differences above ₹{max_agent_waiver:,.0f} without supervisor approval.",
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
                    escalation_target=fare_waiver_prohibit.get("escalation_target", "supervisor") if fare_waiver_prohibit else "supervisor",
                    escalation_reason=f"Requested waiver of ₹{fare_diff:,.0f} fare difference exceeds the ₹{max_agent_waiver:,.0f} agent waiver authority.",
                    recommended_human_action=f"Supervisor review required to approve or deny fare difference waiver of ₹{fare_diff:,.0f} for rebooking on higher-fare flight.",
                    source_citations=list(dict.fromkeys(citations)),
                    explanation=f"Under the Fare Difference Rule, agents can only waive fare differences up to ₹{max_agent_waiver:,.0f}. A waiver of ₹{fare_diff:,.0f} requires supervisor escalation."
                )

        citations = list(dict.fromkeys(citations))

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
