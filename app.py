import streamlit as st
import json
import os
import sys
import datetime
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
    page_title="SkyResolve | Airline Disruption Customer Support",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Aviation Executive Dashboard)
st.markdown("""
<style>
    /* Global Typography & Spacing */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Executive Header */
    .main-header {
        background: linear-gradient(135deg, #0A192F 0%, #1E3A8A 100%);
        padding: 22px 28px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .main-header h1 {
        color: #FFFFFF !important;
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #93C5FD;
        margin: 4px 0 0 0;
        font-size: 13px;
    }

    /* Live Flight Disruption Strip */
    .flight-strip {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .flight-meta-item {
        display: flex;
        flex-direction: column;
    }
    .flight-meta-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .flight-meta-val {
        font-size: 15px;
        font-weight: 700;
        color: #0F172A;
    }
    
    /* Tier Badges */
    .tier-gold { color: #B45309; background: #FEF3C7; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 12px; }
    .tier-silver { color: #475569; background: #F1F5F9; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 12px; }
    .tier-platinum { color: #4338CA; background: #E0E7FF; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 12px; }
    .tier-bronze { color: #9A3412; background: #FFEDD5; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 12px; }

    /* Disruption Badges */
    .status-cancelled { color: #B91C1C; background: #FEE2E2; padding: 3px 10px; border-radius: 8px; font-weight: 700; }
    .status-delayed { color: #C2410C; background: #FFEDD5; padding: 3px 10px; border-radius: 8px; font-weight: 700; }

    /* Action Voucher Card */
    .voucher-card {
        background: #FFFFFF;
        border-left: 4px solid #0284C7;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 13px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Escalation Ticket Box */
    .escalation-box {
        background: #FFF1F2;
        border: 1px solid #FECDD3;
        border-left: 5px solid #E11D48;
        border-radius: 8px;
        padding: 14px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "data_service" not in st.session_state:
    st.session_state.data_service = DataService()

if "workflow" not in st.session_state:
    st.session_state.workflow = AirlineSupportWorkflow(data_service=st.session_state.data_service)

if "audit_logger" not in st.session_state:
    st.session_state.audit_logger = AuditLogger()

workflow: AirlineSupportWorkflow = st.session_state.workflow
data_service: DataService = st.session_state.data_service

# --- SIDEBAR: PASSENGER CONTEXT & SETTINGS ---
with st.sidebar:
    st.markdown("### ✈️ SkyResolve Console")
    st.caption("AIONOS Assignment 3: Data-Driven Resolution Agent")
    st.markdown("---")

    st.markdown("#### 👤 Select Passenger")
    all_customers = data_service.get_all_customers()
    cust_ids = [c["id"] for c in all_customers]

    if "selected_customer_id" not in st.session_state or st.session_state.selected_customer_id not in cust_ids:
        st.session_state.selected_customer_id = cust_ids[0] if cust_ids else None

    selected_id = st.selectbox(
        "Select Passenger Profile",
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

    # Passenger Details Card
    if cust:
        tier = cust.get('loyalty_tier', 'Standard')
        tier_class = f"tier-{tier.lower()}"
        st.markdown(f"**Customer:** `{cust.get('name')}` <span class='{tier_class}'>{tier.upper()}</span>", unsafe_allow_html=True)
        st.markdown(f"**PNR Reference:** `{pnr}`")
        st.markdown(f"**Contact:** `{cust.get('contact', {}).get('email')}`")
        st.markdown(f"**Phone:** `{cust.get('contact', {}).get('phone')}`")
        hist = cust.get("travel_history", {})
        st.caption(f"📊 {hist.get('flights_last_12_months', 0)} flights in past 12 months • {len(hist.get('prior_complaints', []))} prior incident(s).")

    st.markdown("---")

    # Add New Customer (Zero-Code Extensibility Tool)
    with st.expander("➕ Add New Customer (Extensibility Test)", expanded=False):
        st.caption("Demonstrates dynamic data architecture: add any customer without touching Python code.")
        new_name = st.text_input("Full Name", value="Karan Roy")
        new_tier = st.selectbox("Loyalty Tier", ["Bronze", "Silver", "Gold", "Platinum"], index=0)
        new_pnr = st.text_input("PNR", value="ZX9901").upper()
        new_flight = st.text_input("Flight Number", value="SK-555")
        new_route = st.text_input("Route", value="Delhi → Pune")
        new_status = st.selectbox("Status", ["Delayed", "Cancelled"], index=0)
        new_delay = st.number_input("Delay Hours", min_value=0.0, max_value=24.0, value=2.0, step=0.5)

        if st.button("Save & Select Passenger", use_container_width=True):
            new_id = new_name.lower().replace(" ", "_")
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
            st.success(f"Added {new_name}! Switched context.")
            st.rerun()

    st.markdown("---")

    # LLM Settings Expander
    with st.expander("⚙️ LLM Model & API Settings", expanded=False):
        st.caption("Active model configuration:")
        llm_choice = st.selectbox(
            "Provider",
            ["Groq (Active)", "Google Gemini", "xAI Grok", "OpenAI", "Anthropic Claude", "Built-in Offline"],
            index=0
        )
        api_key_input = st.text_input(
            "API Key",
            type="password",
            value=os.getenv("LLM_API_KEY", ""),
            help="Your API key is kept in memory."
        )
        default_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        model_input = st.text_input("Model Name", value=default_model)

        if st.button("Apply Settings", use_container_width=True):
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
    st.caption(f"🤖 **AI Engine:** `{active_label}`")

    st.markdown("---")

    # Download Case Session Dossier
    session_data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "customer": cust,
        "booking": booking,
        "conversation_id": workflow.conversation_id,
        "chat_history": workflow.chat_history,
        "last_turn": workflow.last_turn_result,
        "audit_trail": st.session_state.audit_logger.get_events_for_conversation(workflow.conversation_id)
    }
    st.download_button(
        label="📥 Download Session Record (JSON)",
        data=json.dumps(session_data, indent=2),
        file_name=f"case_record_{pnr or 'session'}.json",
        mime="application/json",
        use_container_width=True
    )

    if st.button("🔄 Reset Conversation", use_container_width=True):
        workflow.reset(new_customer_id=selected_id)
        st.rerun()

# --- MAIN AREA ---
# Header
st.markdown("""
<div class="main-header">
    <div>
        <h1>✈️ SkyResolve | Airline Disruption Support</h1>
        <p>AIONOS Recruitment Assignment 3 • Deterministic Policy Engine with LLM Semantic Perception</p>
    </div>
    <div style="text-align: right;">
        <span style="font-size: 12px; background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-weight: 600;">
            Wednesday, 23 Sep 2026
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Ensure workflow has customer bound
if cust and workflow.active_customer_id != cust.get("id"):
    workflow.set_active_customer(cust.get("id"))

# Live Flight Strip (Airport FIDS Display)
if booking:
    segments = booking.get("segments", [])
    if segments:
        seg = segments[0]
        status_text = seg.get('status', 'Scheduled')
        status_badge_class = "status-cancelled" if status_text == "Cancelled" else "status-delayed"
        delay_info = f"⏱️ Delayed {seg.get('delay_hours')}h (New Departure: {seg.get('new_departure')})" if seg.get('delay_hours', 0) > 0 else f"Departure: {seg.get('scheduled_departure')}"
        reason_info = seg.get('disruption_reason', 'Operational disruption')

        st.markdown(f"""
        <div class="flight-strip">
            <div class="flight-meta-item">
                <span class="flight-meta-label">Flight & Route</span>
                <span class="flight-meta-val">{seg.get('flight_number')} • {seg.get('route')}</span>
            </div>
            <div class="flight-meta-item">
                <span class="flight-meta-label">Disruption Status</span>
                <span class="{status_badge_class}">{status_text.upper()}</span>
            </div>
            <div class="flight-meta-item">
                <span class="flight-meta-label">Timing</span>
                <span class="flight-meta-val">{delay_info}</span>
            </div>
            <div class="flight-meta-item">
                <span class="flight-meta-label">Cause</span>
                <span class="flight-meta-val" style="color: #64748B;">{reason_info.title()}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Two Column Layout: Chat Area (60%), Grounding & Audit (40%)
col_chat, col_inspect = st.columns([1.25, 0.75], gap="large")

with col_chat:
    # Quick Inquiries Bar
    st.markdown("##### 💡 Suggested Inquiries (Or type any natural language query below):")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("Check disruption benefits", use_container_width=True):
            workflow.process_user_turn("What benefits and compensation am I entitled to for this flight disruption?")
            st.rerun()
    with q2:
        if st.button("Inquire rebooking & refund", use_container_width=True):
            workflow.process_user_turn("Can you explain my rebooking and refund options?")
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
            st.success("🟢 **Resolution Status: RESOLVED** — Policy rules evaluated. Eligible benefits authorized.")
        elif status == "ESCALATED":
            st.error("🔴 **Resolution Status: ESCALATED** — Request exceeds agent authority or involves prohibited exception.")
        else:
            st.info("🔵 **Resolution Status: ACTIVE** — Processing conversation turn.")

        # Executed Actions Display (Voucher Cards)
        executed = last_res.get("executed_actions", [])
        if executed:
            for act in executed:
                st.markdown(f"""
                <div class="voucher-card">
                    <span style="font-size: 18px;">⚡</span>
                    <div>
                        <strong>Action Executed:</strong> {act.get('summary')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Chat Stream Display
    chat_container = st.container(height=480)
    with chat_container:
        if not workflow.chat_history:
            st.markdown(
                "_Welcome to SkyResolve Disruption Support. Ask any question about your flight, entitlements, rebooking, or compensation._"
            )
        for msg in workflow.chat_history:
            avatar = "👤" if msg["role"] == "user" else "✈️"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Interactive Chat Input
    user_query = st.chat_input("Type your message here (e.g. 'Can I get a full refund to my card?' or 'I need a hotel room')...")
    if user_query:
        workflow.process_user_turn(user_query)
        st.rerun()

with col_inspect:
    st.markdown("#### 🔍 Grounding & Governance")

    tab_policy, tab_decision, tab_escalation, tab_audit = st.tabs([
        "📜 Grounding", "🧠 Decision Log", "🚨 Escalation", "📊 Audit Log"
    ])

    with tab_policy:
        st.markdown("##### 📌 Active Policy Grounding")
        if last_res and last_res.get("source_citations"):
            st.markdown("**Strictly Grounded in Assignment 3 Data Pack:**")
            for c in last_res["source_citations"]:
                st.markdown(f"- 🏷️ `{c}`")
        else:
            st.caption("Active policy citations will appear here upon message evaluation.")

        with st.expander("📖 View Complete Disruption Service Rules (data/policies.json)", expanded=False):
            st.json(data_service.get_all_policies())

    with tab_decision:
        st.markdown("##### 🧩 Policy Engine Evaluation")
        if last_res and last_res.get("decision_result"):
            dec = last_res["decision_result"]
            pol = dec.get("policy_result", {})
            st.markdown(f"**Outcome:** `{pol.get('status')}`")
            st.markdown(f"**Decision Summary:** {pol.get('explanation')}")

            if pol.get("eligible_benefits"):
                st.markdown("**Eligible Benefits Approved:**")
                for b in pol["eligible_benefits"]:
                    st.markdown(f"- ✅ **{b.get('benefit')}**: {b.get('description')}")

            if pol.get("ineligible_requests"):
                st.markdown("**Policy Limitations / Denials:**")
                for r in pol["ineligible_requests"]:
                    st.markdown(f"- ❌ **{r.get('request')}**: {r.get('reason')}")

            if pol.get("allowed_actions"):
                st.markdown("**Authorized Action Dispatches:**")
                for a in pol["allowed_actions"]:
                    st.markdown(f"- 🔧 `{a.get('action')}`")
        else:
            st.caption("Awaiting conversation turn to display evaluation log.")

    with tab_escalation:
        st.markdown("##### 🚨 Human Escalation Dossier")
        if last_res and last_res.get("escalation_record"):
            esc = last_res["escalation_record"]
            st.markdown(f"""
            <div class="escalation-box">
                <div style="font-weight: 700; color: #9F1239; font-size: 14px; margin-bottom: 8px;">
                    🚨 ESCALATION TICKET: {esc.get('booking_reference')}
                </div>
                <div style="font-size: 13px; color: #1E293B;">
                    <strong>Target Queue:</strong> <code>{esc.get('escalation_target')}</code><br>
                    <strong>Passenger:</strong> {esc.get('customer')} (PNR: {esc.get('booking_reference')})<br>
                    <strong>Trigger:</strong> {esc.get('reason_for_escalation')}<br>
                    <strong>Policy Restriction:</strong> {esc.get('policy_limitation')}<br>
                    <strong>Action for Supervisor:</strong> {esc.get('recommended_human_action')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"Ref: `{esc.get('conversation_id')}` | Timestamp: `{esc.get('timestamp')}`")
        else:
            st.success("No active escalation. Request is within automated agent authority.")

    with tab_audit:
        st.markdown("##### 📊 Real-Time Audit Log")
        events = st.session_state.audit_logger.get_events_for_conversation(workflow.conversation_id)
        if events:
            st.caption(f"Logged {len(events)} event(s) for session `{workflow.conversation_id}`")
            for idx, ev in enumerate(reversed(events)):
                with st.expander(f"Turn {len(events)-idx}: {ev.get('intent')} [{ev.get('status')}]", expanded=(idx==0)):
                    st.json(ev)
        else:
            st.caption("No audit events recorded for current session.")

        if st.button("🧹 Clear Audit Logs"):
            st.session_state.audit_logger.clear()
            st.rerun()
