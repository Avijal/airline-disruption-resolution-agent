import pytest
from services.data_service import DataService
from core.policy_engine import PolicyEngine


@pytest.fixture
def policy_engine():
    data_service = DataService()
    return PolicyEngine(data_service=data_service)


@pytest.fixture
def priya_context(policy_engine):
    cust = policy_engine.data_service.get_customer_by_id("priya_nair")
    booking = policy_engine.data_service.get_booking_by_pnr("SK4821X")
    return cust, booking


@pytest.fixture
def arvind_context(policy_engine):
    cust = policy_engine.data_service.get_customer_by_id("arvind_kulkarni")
    booking = policy_engine.data_service.get_booking_by_pnr("TR1190B")
    return cust, booking


@pytest.fixture
def meher_context(policy_engine):
    cust = policy_engine.data_service.get_customer_by_id("meher_kaur")
    booking = policy_engine.data_service.get_booking_by_pnr("WL7742")
    return cust, booking


def test_airline_cancellation_refund_eligibility(policy_engine, priya_context):
    cust, booking = priya_context
    req = {"wants_refund": True}
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "RESOLVED"
    assert "cancellation_rebooking" in res.applicable_policies
    assert "refund_processing" in res.applicable_policies
    assert any(a["action"] == "initiate_refund" for a in res.allowed_actions)
    assert not res.escalation_required


def test_airline_cancellation_rebooking_eligibility(policy_engine, priya_context):
    cust, booking = priya_context
    req = {"wants_rebooking": True}
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "RESOLVED"
    assert any(a["action"] == "rebook_flight" for a in res.allowed_actions)
    # Priya is Gold tier -> priority access
    assert any(b["benefit"] == "priority_rebooking" for b in res.eligible_benefits)


def test_four_hour_delay_meal_and_lounge(policy_engine, arvind_context):
    cust, booking = arvind_context
    req = {"wants_amenities": True}
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "RESOLVED"
    assert "delay_compensation" in res.applicable_policies
    benefits = [b["benefit"] for b in res.eligible_benefits]
    assert "meal_voucher" in benefits
    assert "lounge_access" in benefits
    assert any(a["action"] == "issue_meal_voucher" for a in res.allowed_actions)
    assert any(a["action"] == "grant_lounge_access" for a in res.allowed_actions)


def test_four_hour_delay_no_hotel(policy_engine, arvind_context):
    cust, booking = arvind_context
    req = {"wants_hotel": True}
    res = policy_engine.evaluate(cust, booking, req)

    # 4h delay qualifies for meal + lounge, but hotel must be denied
    hotel_denied = any("hotel" in r["request"].lower() for r in res.ineligible_requests)
    assert hotel_denied
    assert not any(a["action"] == "arrange_hotel_delayed_hours" for a in res.allowed_actions)


def test_six_hour_delay_hotel_for_delayed_hours(policy_engine, meher_context):
    cust, booking = meher_context
    req = {"wants_hotel": True}
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "RESOLVED"
    benefits = [b["benefit"] for b in res.eligible_benefits]
    assert "hotel_accommodation" in benefits
    assert any(a["action"] == "arrange_hotel_delayed_hours" for a in res.allowed_actions)


def test_six_hour_delay_no_full_night_entitlement(policy_engine, meher_context):
    cust, booking = meher_context
    req = {"wants_hotel": True, "wants_full_night_hotel": True}
    res = policy_engine.evaluate(cust, booking, req)

    # Policy covers delayed hours only, not full night
    rejection = any("full night" in r["request"].lower() for r in res.ineligible_requests)
    assert rejection
    # Delayed hours is still granted
    assert any(a["action"] == "arrange_hotel_delayed_hours" for a in res.allowed_actions)


def test_fare_difference_above_1500_escalates(policy_engine, meher_context):
    cust, booking = meher_context
    req = {
        "wants_higher_fare_rebooking": True,
        "wants_fare_waiver": True,
        "fare_difference_amount": 2000.0
    }
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "ESCALATED"
    assert res.escalation_required is True
    assert res.escalation_target == "supervisor"
    assert "1,500" in res.escalation_reason or "1500" in res.escalation_reason


def test_unsupported_compensation_escalation(policy_engine, priya_context):
    cust, booking = priya_context
    req = {
        "wants_refund": True,
        "wants_upgrade": True
    }
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "ESCALATED"
    assert res.escalation_required is True
    assert any("upgrade" in r["request"].lower() for r in res.ineligible_requests)


def test_legal_threat_immediate_escalation(policy_engine, priya_context):
    cust, booking = priya_context
    req = {
        "is_legal_threat": True,
        "raw_message": "I am filing a lawsuit and taking legal action."
    }
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "ESCALATED"
    assert res.escalation_required is True
    assert res.escalation_target == "specialist_support_team"


def test_refund_to_alternate_payment_method_escalation(policy_engine, priya_context):
    cust, booking = priya_context
    req = {
        "wants_refund": True,
        "alternate_payment_method_requested": True
    }
    res = policy_engine.evaluate(cust, booking, req)

    assert res.status == "ESCALATED"
    assert res.escalation_required is True
    assert any("alternate payment" in r["request"].lower() for r in res.ineligible_requests)
