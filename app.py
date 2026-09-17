import streamlit as st
import json
import os
import sys
from pathlib import Path

# Ensure project root is in path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from services.data_service import DataService
from agents.workflow import AirlineSupportWorkflow
from core.audit import AuditLogger

# Page configuration
st.set_page_config(
    page_title="SkyResolve | Airline Disruption Resolution Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "data_service" not in st.session_state:
    st.session_state.data_service = DataService()

if "workflow" not in st.session_state:
    st.session_state.workflow = AirlineSupportWorkflow(data_service=st.session_state.data_service)

if "audit_logger" not in st.session_state:
    st.session_state.audit_logger = AuditLogger()

if "selected_scenario_key" not in st.session_state:
    st.session_state.selected_scenario_key = "priya_nair"

workflow: AirlineSupportWorkflow = st.session_state.workflow
data_service: DataService = st.session_state.data_service

# Scenarios Metadata
SCENARIOS = {
    "priya_nair": {
        "title": "Scenario 1: Priya Nair (Gold)",
        "customer_id": "priya_nair",
        "pnr": "SK4821X",
        "subtitle": "Flight SK-204 Cancelled (Operational reasons)",
        "sample_prompts": [
            "My flight was cancelled and I am furious! I want a full cash refund and a free business class upgrade on my return flight.",
            "Can I get a full cash refund for my cancelled flight SK-204?",
            "Can you rebook me on the next available flight to Goa?"
        ]
    },
    "arvind_kulkarni": {
        "title": "Scenario 2: Arvind Kulkarni (Silver)",
        "customer_id": "arvind_kulkarni",
        "pnr": "TR1190B",
        "subtitle": "Flight SK-118 Delayed 4h (Mumbai → Bengaluru)",
        "sample_prompts": [
            "My flight is delayed 4 hours. Since it's been such a long delay, I ask for hotel accommodation.",
            "What benefits or compensation am I eligible for during this 4-hour delay?",
            "Can I at least get meal vouchers and lounge access while I wait?"
        ]
    },
    "meher_kaur": {
        "title": "Scenario 3: Meher Kaur (Platinum)",
        "customer_id": "meher_kaur",
        "pnr": "WL7742",
        "subtitle": "Flight SK-305 Delayed 6h (Delhi → Hyderabad)",
        "sample_prompts": [
            "My flight is delayed 6 hours. I want a full night's hotel stay, and I want to be moved to a different higher-fare flight with a ₹2,000 fare difference.",
            "Can you arrange hotel accommodation for me for this 6-hour delay?",
            "I'm willing to switch flights, will you waive the ₹2,000 fare difference?"
        ]
    }
}

# --- SIDEBAR ---
with st.sidebar:
    st.title("✈️ SkyResolve")
    st.caption("AIONOS Assignment 3: Airline Disruption Customer Support")
    st.markdown("---")

    demo_mode = st.radio(
        "Demonstration Mode",
        ["Curated Scenarios", "Custom PNR / Extensible Customer"],
        index=0
    )

    if demo_mode == "Curated Scenarios":
        scenario_key = st.selectbox(
            "Select Scenario",
            options=list(SCENARIOS.keys()),
            format_func=lambda k: SCENARIOS[k]["title"]
        )

        # Handle Scenario Switching
        if scenario_key != st.session_state.selected_scenario_key:
            st.session_state.selected_scenario_key = scenario_key
            workflow.reset(new_customer_id=SCENARIOS[scenario_key]["customer_id"])
            st.rerun()

        cust = data_service.get_customer_by_id(SCENARIOS[scenario_key]["customer_id"])
        pnr = SCENARIOS[scenario_key]["pnr"]
        booking = data_service.get_booking_by_pnr(pnr)

    else:
        st.markdown("##### Custom Customer / PNR Input")
        custom_input = st.text_input("Enter Customer ID or PNR", value="ZX9901").strip()
        cust = data_service.get_customer_by_id(custom_input.lower()) or data_service.get_customer_by_pnr(custom_input)
        if cust:
            pnr = cust.get("booking_reference")
            booking = data_service.get_booking_by_pnr(pnr)
            if workflow.active_customer_id != cust.get("id"):
                workflow.reset(new_customer_id=cust.get("id"))
        else:
            pnr = custom_input
            booking = data_service.get_booking_by_pnr(pnr)

    st.markdown("---")
    # Context Cards
    if cust:
        st.markdown(f"**Customer:** `{cust.get('name')}`")
        st.markdown(f"**Tier:** `{cust.get('loyalty_tier')}` | **PNR:** `{pnr}`")
        st.markdown(f"**Contact:** `{cust.get('contact', {}).get('phone')}`")
        hist = cust.get("travel_history", {})
        st.caption(f"Travel History: {hist.get('flights_last_12_months', 0)} flights in past 12m, {len(hist.get('prior_complaints', []))} prior complaint(s).")
    else:
        st.warning("Customer profile not loaded. Agent will ask for PNR.")

    if booking:
        segments = booking.get("segments", [])
        if segments:
            seg = segments[0]
            st.markdown(f"**Flight:** `{seg.get('flight_number')}` ({seg.get('route')})")
            st.markdown(f"**Status:** `{seg.get('status')}` ({seg.get('disruption_reason', 'N/A')})")
            if seg.get("delay_hours", 0) > 0:
                st.markdown(f"**Delay:** `{seg.get('delay_hours')} hours` (New: `{seg.get('new_departure')}`)")
            st.markdown(f"**Payment:** `{booking.get('payment_method')}`")

    st.markdown("---")
    if st.button("🔄 Reset Conversation", use_container_width=True):
        active_id = cust.get("id") if cust else None
        workflow.reset(new_customer_id=active_id)
        st.rerun()

# --- MAIN AREA ---
st.subheader("Airline Disruption Resolution Agent")
st.caption("Data-Driven, Policy-Grounded Architecture • Zero Hallucination • Audit Logged")

# Ensure workflow has customer bound
if cust and workflow.active_customer_id != cust.get("id"):
    workflow.set_active_customer(cust.get("id"))

# Two Column Layout: Chat on Left (60%), Grounding & Audit on Right (40%)
col_chat, col_inspect = st.columns([1.2, 0.8], gap="large")

with col_chat:
    # Quick prompt chips for fast testing
    if demo_mode == "Curated Scenarios":
        st.markdown("##### ⚡ Click-to-Test Suggested Prompts:")
        prompt_cols = st.columns(len(SCENARIOS[st.session_state.selected_scenario_key]["sample_prompts"]))
        for idx, prompt_text in enumerate(SCENARIOS[st.session_state.selected_scenario_key]["sample_prompts"]):
            with prompt_cols[idx]:
                if st.button(f"Prompt {idx+1}", help=prompt_text, use_container_width=True):
                    workflow.process_user_turn(prompt_text)
                    st.rerun()

    st.markdown("---")

    # Status Banner
    last_res = workflow.last_turn_result
    if last_res:
        status = last_res.get("status", "ACTIVE")
        if status == "RESOLVED":
            st.success("✅ **Status: RESOLVED** — Eligible policy benefits approved and executed.")
        elif status == "ESCALATED":
            st.error("🚨 **Status: ESCALATED** — Request exceeds agent authority or involves prohibited action.")
        else:
            st.info("ℹ️ **Status: ACTIVE** — Identification or further details required.")

        # Display Executed Action Badges
        executed = last_res.get("executed_actions", [])
        if executed:
            for act in executed:
                st.info(f"⚡ **Tool Executed:** {act.get('summary')}")

    # Conversation History Display
    chat_container = st.container(height=480)
    with chat_container:
        if not workflow.chat_history:
            st.markdown(
                "_No messages yet. Send a customer message or select a test prompt above to start the resolution workflow._"
            )
        for msg in workflow.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat Input Box
    user_query = st.chat_input("Type customer message here...")
    if user_query:
        workflow.process_user_turn(user_query)
        st.rerun()

with col_inspect:
    st.markdown("#### 🔍 Grounding & Agent Transparency")

    tab_policy, tab_decision, tab_escalation, tab_audit = st.tabs([
        "📜 Grounding", "🧠 Decision Log", "🚨 Escalation", "📊 Audit Trail"
    ])

    with tab_policy:
        st.markdown("##### 📌 Active Policy Grounding")
        if last_res and last_res.get("source_citations"):
            st.markdown("**Exact Sources Cited from Assignment Data Pack:**")
            for c in last_res["source_citations"]:
                st.markdown(f"- 🏷️ `{c}`")
        else:
            st.caption("No policy evaluation triggered for this turn yet.")

        with st.expander("📖 View Complete Disruption Service Rules", expanded=False):
            st.json(data_service.get_all_policies())

    with tab_decision:
        st.markdown("##### 🧩 Policy Engine Evaluation")
        if last_res and last_res.get("decision_result"):
            dec = last_res["decision_result"]
            pol = dec.get("policy_result", {})
            st.markdown(f"**Outcome:** `{pol.get('status')}`")
            st.markdown(f"**Summary:** {pol.get('explanation')}")

            if pol.get("eligible_benefits"):
                st.markdown("**Eligible Benefits:**")
                for b in pol["eligible_benefits"]:
                    st.markdown(f"- ✅ **{b.get('benefit')}**: {b.get('description')}")

            if pol.get("ineligible_requests"):
                st.markdown("**Ineligible / Denied Requests:**")
                for r in pol["ineligible_requests"]:
                    st.markdown(f"- ❌ **{r.get('request')}**: {r.get('reason')}")

            if pol.get("allowed_actions"):
                st.markdown("**Authorized Actions:**")
                for a in pol["allowed_actions"]:
                    st.markdown(f"- 🔧 `{a.get('action')}` ({a.get('source', '')})")
        else:
            st.caption("Awaiting first user turn to display evaluation log.")

    with tab_escalation:
        st.markdown("##### 🚨 Human Escalation Dossier")
        if last_res and last_res.get("escalation_record"):
            esc = last_res["escalation_record"]
            st.error(f"**Escalated To:** `{esc.get('escalation_target')}`")
            st.markdown(f"**Customer:** `{esc.get('customer')}` (PNR: `{esc.get('booking_reference')}`)")
            st.markdown(f"**Issue:** {esc.get('issue')}")
            st.markdown(f"**Requested Action:** {esc.get('requested_action')}")
            st.markdown(f"**Policy Limitation:** {esc.get('policy_limitation')}")
            st.markdown(f"**Trigger Reason:** {esc.get('reason_for_escalation')}")
            st.markdown(f"**Recommended Human Action:** {esc.get('recommended_human_action')}")
            st.caption(f"Timestamp: {esc.get('timestamp')} | Conv ID: {esc.get('conversation_id')}")
        else:
            st.success("No active escalation for this turn. Request is within agent authority.")

    with tab_audit:
        st.markdown("##### 📊 Real-Time Audit Log")
        events = st.session_state.audit_logger.get_events_for_conversation(workflow.conversation_id)
        if events:
            st.caption(f"Logged {len(events)} event(s) for conversation `{workflow.conversation_id}`")
            for idx, ev in enumerate(reversed(events)):
                with st.expander(f"Turn {len(events)-idx}: {ev.get('intent')} [{ev.get('status')}]", expanded=(idx==0)):
                    st.json(ev)
        else:
            st.caption("No audit events recorded for current session.")

        if st.button("🧹 Clear Audit Logs"):
            st.session_state.audit_logger.clear()
            st.rerun()
