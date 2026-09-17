import pytest
from agents.workflow import AirlineSupportWorkflow


@pytest.fixture
def workflow():
    return AirlineSupportWorkflow()


def test_scenario_1_priya(workflow):
    workflow.set_active_customer("priya_nair")
    msg = "I am furious! My flight SK-204 was cancelled. I want a full cash refund and a free upgrade to business class on my return flight for the trouble."
    res = workflow.process_user_turn(msg)

    # Priya wants refund + upgrade
    # Status should be ESCALATED due to upgrade request beyond policy
    assert res["status"] == "ESCALATED"
    assert res["escalation_record"] is not None
    assert "upgrade" in res["escalation_record"]["reason_for_escalation"].lower()

    # Refund was still identified as permitted
    actions = [a["action"] for a in res["executed_actions"]]
    assert "initiate_refund" in actions

    # Source citations must cite Data Pack
    assert any("Service Rules" in c for c in res["source_citations"])


def test_scenario_2_arvind(workflow):
    workflow.set_active_customer("arvind_kulkarni")
    msg = "My flight SK-118 is delayed 4 hours. Since it's been such a long delay, I ask for hotel accommodation."
    res = workflow.process_user_turn(msg)

    # 4h delay gets meal + lounge, but hotel is rejected under policy
    assert res["status"] == "RESOLVED"
    actions = [a["action"] for a in res["executed_actions"]]
    assert "issue_meal_voucher" in actions
    assert "grant_lounge_access" in actions
    assert "arrange_hotel_accommodation" not in actions

    # Ineligible request recorded
    dec_res = res["decision_result"]["policy_result"]
    ineligible = [r["request"] for r in dec_res["ineligible_requests"]]
    assert any("hotel" in r.lower() for r in ineligible)


def test_scenario_3_meher(workflow):
    workflow.set_active_customer("meher_kaur")
    msg = "My flight SK-305 is delayed 6 hours. I want a full night's hotel stay and to be moved to a different higher-fare flight with a ₹2,000 fare difference."
    res = workflow.process_user_turn(msg)

    # 6h delay gets hotel for delayed hours, full night is rejected
    # ₹2,000 fare difference exceeds ₹1,500 waiver limit -> ESCALATED
    assert res["status"] == "ESCALATED"
    assert res["escalation_record"] is not None
    assert res["escalation_record"]["escalation_target"] == "supervisor"
    assert "1,500" in res["escalation_record"]["reason_for_escalation"] or "2,000" in res["escalation_record"]["reason_for_escalation"]

    # Delayed hours hotel was permitted
    actions = [a["action"] for a in res["executed_actions"]]
    assert "arrange_hotel_delayed_hours" in actions
