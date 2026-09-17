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
from services.llm_provider import get_llm_provider

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

workflow: AirlineSupportWorkflow = st.session_state.workflow
data_service: DataService = st.session_state.data_service

# --- SIDEBAR: DYNAMIC DATA & CONFIGURATION ---
with st.sidebar:
    st.title("✈️ SkyResolve")
    st.caption("AIONOS Assignment 3: Data-Driven Customer Support Agent")
    st.markdown("---")

    st.markdown("### 👤 Active Customer Selection")
    st.caption("Loaded dynamically from `data/customers.json`:")

    all_customers = data_service.get_all_customers()
    cust_ids = [c["id"] for c in all_customers]

    # Maintain selected customer in session
    if "selected_customer_id" not in st.session_state or st.session_state.selected_customer_id not in cust_ids:
        st.session_state.selected_customer_id = cust_ids[0] if cust_ids else None

    selected_id = st.selectbox(
        "Select Customer",
        options=cust_ids,
        format_func=lambda cid: f"{data_service.get_customer_by_id(cid).get('name', cid)} ({data_service.get_customer_by_id(cid).get('loyalty_tier', '')}) — PNR {data_service.get_customer_by_id(cid).get('booking_reference', '')}"
    )

    if selected_id != st.session_state.selected_customer_id:
        st.session_state.selected_customer_id = selected_id
        workflow.reset(new_customer_id=selected_id)
        st.rerun()

    cust = data_service.get_customer_by_id(selected_id) if selected_id else None
    pnr = cust.get("booking_reference") if cust else ""
    booking = data_service.get_booking_by_pnr(pnr) if pnr else None

    # Context Cards
    if cust:
        st.markdown(f"**Customer:** `{cust.get('name')}`")
        st.markdown(f"**Tier:** `{cust.get('loyalty_tier')}` | **PNR:** `{pnr}`")
        st.markdown(f"**Contact:** `{cust.get('contact', {}).get('email')}`, `{cust.get('contact', {}).get('phone')}`")
        hist = cust.get("travel_history", {})
        st.caption(f"Travel History: {hist.get('flights_last_12_months', 0)} flights in past 12m, {len(hist.get('prior_complaints', []))} prior complaint(s).")

    if booking:
        segments = booking.get("segments", [])
        if segments:
            seg = segments[0]
            st.markdown(f"**Disrupted Flight:** `{seg.get('flight_number')}` ({seg.get('route')})")
            st.markdown(f"**Status:** `{seg.get('status')}` ({seg.get('disruption_reason', 'N/A')})")
            if seg.get("delay_hours", 0) > 0:
                st.markdown(f"**Delay:** `{seg.get('delay_hours')} hours` (New: `{seg.get('new_departure')}`)")
            st.markdown(f"**Payment Instrument:** `{booking.get('payment_method')}`")

    st.markdown("---")

    # DYNAMIC EXTENSIBILITY TOOL: Add 4th / 5th Customer live
    with st.expander("➕ Add New Customer (Zero-Code Extensibility)", expanded=False):
        st.caption("Demonstrates that adding customers/bookings requires zero code modifications.")
        new_name = st.text_input("Full Name", value="Karan Roy")
        new_tier = st.selectbox("Loyalty Tier", ["Bronze", "Silver", "Gold", "Platinum"], index=0)
        new_pnr = st.text_input("PNR", value="ZX9901").upper()
        new_flight = st.text_input("Flight Number", value="SK-555")
        new_route = st.text_input("Route", value="Delhi → Pune")
        new_status = st.selectbox("Flight Status", ["Delayed", "Cancelled"], index=0)
        new_delay = st.number_input("Delay Hours", min_value=0.0, max_value=24.0, value=2.0, step=0.5)

        if st.button("Save & Switch to New Customer", use_container_width=True):
            new_id = new_name.lower().replace(" ", "_")
            # Update customers.json
            cust_file = data_service.data_dir / "customers.json"
            with open(cust_file, "r", encoding="utf-8") as f:
                cust_list = json.load(f)
            if not any(c["id"] == new_id for c in cust_list):
                cust_list.append({
                    "id": new_id,
                    "name": new_name,
                    "loyalty_tier": new_tier,
                    "booking_reference": new_pnr,
                    "contact": {"email": f"{new_id}@example.com", "phone": "+91-98xxxxxxx4"},
                    "travel_history": {"flights_last_12_months": 1, "prior_complaints": []}
                })
                with open(cust_file, "w", encoding="utf-8") as f:
                    json.dump(cust_list, f, indent=2)

            # Update bookings.json
            book_file = data_service.data_dir / "bookings.json"
            with open(book_file, "r", encoding="utf-8") as f:
                book_list = json.load(f)
            if not any(b["pnr"] == new_pnr for b in book_list):
                book_list.append({
                    "pnr": new_pnr,
                    "customer_id": new_id,
                    "customer_name": new_name,
                    "segments": [{
                        "segment_id": f"{new_pnr}-1",
                        "flight_number": new_flight,
                        "route": new_route,
                        "origin": new_route.split("→")[0].strip() if "→" in new_route else "Origin",
                        "destination": new_route.split("→")[1].strip() if "→" in new_route else "Dest",
                        "date": "Wed 23 Sep 2026",
                        "scheduled_departure": "10:00",
                        "new_departure": "12:00" if new_delay > 0 else None,
                        "status": new_status,
                        "disruption_type": "airline_caused",
                        "disruption_reason": "operational disruption",
                        "delay_hours": float(new_delay),
                        "cabin_class": "Economy"
                    }],
                    "payment_method": "Original Credit Card (ending 7711)"
                })
                with open(book_file, "w", encoding="utf-8") as f:
                    json.dump(book_list, f, indent=2)

            data_service.reload()
            st.session_state.selected_customer_id = new_id
            workflow.reset(new_customer_id=new_id)
            st.success(f"Added {new_name} ({new_pnr}) to data files! Switching context...")
            st.rerun()

    st.markdown("---")

    # LLM & API Configuration Expander
    with st.expander("⚙️ LLM Model & API Settings", expanded=False):
        st.caption("Connected to your environment or dynamic API key:")
        llm_choice = st.selectbox(
            "Provider",
            ["Groq (Active in .env)", "Google Gemini", "xAI Grok", "OpenAI", "Anthropic Claude", "Built-in Offline"],
            index=0
        )
        api_key_input = st.text_input(
            "API Key",
            type="password",
            value=os.getenv("LLM_API_KEY", ""),
            help="Enter your API key here."
        )
        default_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        model_input = st.text_input("Model Name", value=default_model)

        if st.button("Apply API Settings", use_container_width=True):
            prov_code = "groq"
            if "Gemini" in llm_choice:
                prov_code = "gemini"
            elif "Grok" in llm_choice:
                prov_code = "grok"
            elif "OpenAI" in llm_choice:
                prov_code = "openai"
            elif "Anthropic" in llm_choice:
                prov_code = "anthropic"
            elif "Offline" in llm_choice:
                prov_code = "deterministic"

            new_provider = get_llm_provider(
                provider_name=prov_code,
                api_key=api_key_input,
                model=model_input
            )
            workflow.agent.llm_provider = new_provider
            workflow.agent.response_agent.llm_provider = new_provider
            workflow.agent.intent_agent.llm_provider = new_provider
            st.session_state.active_provider_label = f"{llm_choice} ({model_input or 'default'})"
            st.success("API settings applied!")
            st.rerun()

    active_label = st.session_state.get("active_provider_label", f"{os.getenv('LLM_PROVIDER', 'groq').upper()} ({os.getenv('LLM_MODEL', 'openai/gpt-oss-120b')})")
    st.caption(f"🤖 **Active AI Engine:** `{active_label}`")

    st.markdown("---")
    if st.button("🔄 Reset Conversation", use_container_width=True):
        workflow.reset(new_customer_id=selected_id)
        st.rerun()

# --- MAIN AREA ---
st.subheader("Airline Disruption Resolution Agent")
st.caption("Data-Driven Policy Engine • Live LLM Semantic Perception • Zero Hardcoding • Structured Audit")

# Ensure workflow customer binding
if cust and workflow.active_customer_id != cust.get("id"):
    workflow.set_active_customer(cust.get("id"))

# Layout: Chat Column (60%), Grounding & Audit Inspector (40%)
col_chat, col_inspect = st.columns([1.2, 0.8], gap="large")

with col_chat:
    # Generic Quick Action Ideas
    st.markdown("##### 💡 Sample Inquiries (Or type anything below):")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("Check benefits & compensation", use_container_width=True):
            workflow.process_user_turn("What benefits or compensation am I entitled to for this disruption?")
            st.rerun()
    with q2:
        if st.button("Request rebooking / refund", use_container_width=True):
            workflow.process_user_turn("What are my rebooking and refund options?")
            st.rerun()
    with q3:
        if st.button("Request hotel accommodation", use_container_width=True):
            workflow.process_user_turn("I need hotel accommodation due to this disruption.")
            st.rerun()

    st.markdown("---")

    # Status Banner
    last_res = workflow.last_turn_result
    if last_res:
        status = last_res.get("status", "ACTIVE")
        if status == "RESOLVED":
            st.success("✅ **Status: RESOLVED** — Request evaluated against policies and actions executed.")
        elif status == "ESCALATED":
            st.error("🚨 **Status: ESCALATED** — Request exceeds agent authority or involves prohibited exception.")
        else:
            st.info("ℹ️ **Status: ACTIVE** — Processing conversation turn.")

        # Display Executed Action Badges
        executed = last_res.get("executed_actions", [])
        if executed:
            for act in executed:
                st.info(f"⚡ **Action Executed:** {act.get('summary')}")

    # Conversation History Display
    chat_container = st.container(height=480)
    with chat_container:
        if not workflow.chat_history:
            st.markdown(
                "_Start the conversation by typing your request below or selecting one of the generic inquiries above._"
            )
        for msg in workflow.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat Input Box
    user_query = st.chat_input("Type your customer message here...")
    if user_query:
        workflow.process_user_turn(user_query)
        st.rerun()

with col_inspect:
    st.markdown("#### 🔍 Policy Grounding & Audit Trail")

    tab_policy, tab_decision, tab_escalation, tab_audit = st.tabs([
        "📜 Policy Grounding", "🧠 Decision Engine", "🚨 Escalation Dossier", "📊 Audit Log"
    ])

    with tab_policy:
        st.markdown("##### 📌 Active Policy Grounding")
        if last_res and last_res.get("source_citations"):
            st.markdown("**Exact Sources Cited from Assignment Data Pack:**")
            for c in last_res["source_citations"]:
                st.markdown(f"- 🏷️ `{c}`")
        else:
            st.caption("Citations will appear when policies are evaluated.")

        with st.expander("📖 View Dynamic Disruption Service Rules (data/policies.json)", expanded=False):
            st.json(data_service.get_all_policies())

    with tab_decision:
        st.markdown("##### 🧩 Policy Engine Evaluation (data-driven)")
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
            st.success("No active escalation. Request is within agent authority.")

    with tab_audit:
        st.markdown("##### 📊 Real-Time Structured Audit Log")
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
