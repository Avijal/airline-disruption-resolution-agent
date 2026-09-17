import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Color Palette
    COLOR_NAVY = RGBColor(10, 25, 47)       # #0A192F
    COLOR_ACCENT = RGBColor(0, 180, 216)    # #00B4D8
    COLOR_BLUE_DARK = RGBColor(15, 23, 42)  # Slate 900
    COLOR_CARD_BG = RGBColor(241, 245, 249) # Slate 100
    COLOR_WHITE = RGBColor(255, 255, 255)
    COLOR_TEXT_MAIN = RGBColor(30, 41, 59)  # Slate 800
    COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
    COLOR_GREEN = RGBColor(16, 185, 129)
    COLOR_RED = RGBColor(239, 68, 68)

    def add_header(slide, title_text, category="AIONOS RECRUITMENT ASSIGNMENT 3 | AIRLINE DISRUPTION AGENT"):
        # Header category
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = category.upper()
        p_c.font.size = Pt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = COLOR_ACCENT

        # Slide Title
        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.8))
        tf_t = t_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_NAVY

    def add_card(slide, left, top, width, height, title, items, bg_color=COLOR_CARD_BG, title_color=COLOR_NAVY):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = RGBColor(226, 232, 240)
        shape.line.width = Pt(1)

        txBox = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
        tf = txBox.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(15)
        p0.font.bold = True
        p0.font.color.rgb = title_color
        p0.space_after = Pt(10)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"•  {item}"
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_TEXT_MAIN
            p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_slide_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_NAVY
    bg1.line.fill.background()

    t_box1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.5))
    tf1 = t_box1.text_frame
    tf1.word_wrap = True

    p_badge = tf1.paragraphs[0]
    p_badge.text = "AIONOS RECRUITMENT ASSIGNMENT 3 — SUBMISSION"
    p_badge.font.size = Pt(13)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_ACCENT
    p_badge.space_after = Pt(14)

    p_title = tf1.add_paragraph()
    p_title.text = "Customer-Facing Resolution Agent"
    p_title.font.size = Pt(36)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    p_title.space_after = Pt(8)

    p_sub = tf1.add_paragraph()
    p_sub.text = "Airline Disruption Support: Policy-Grounded, Data-Driven Autonomous Resolution Architecture"
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)
    p_sub.space_after = Pt(24)

    p_meta = tf1.add_paragraph()
    p_meta.text = "Role: AI Engineer Lead  |  Stack: Python, Streamlit, Modular Policy Engine, LLMProvider  |  Date: September 2026"
    p_meta.font.size = Pt(13)
    p_meta.font.color.rgb = COLOR_ACCENT

    # =========================================================================
    # SLIDE 2: Business Problem
    # =========================================================================
    s2 = prs.slides.add_slide(blank_slide_layout)
    add_header(s2, "Business Problem: High-Stakes Airline Disruption Resolution")
    add_card(s2, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Operational Disruption Reality", [
        "Flight cancellations and multi-hour delays trigger sudden spikes in customer distress.",
        "Emotional customers demand immediate financial answers (cash refunds, hotel rooms, cabin upgrades).",
        "High agent turnover and cognitive overload cause inconsistent, erroneous resolutions."
    ])
    add_card(s2, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "The Automation Pitfall", [
        "Generic LLM chatbots hallucinate compensation, invent flight numbers, or make unauthorized promises.",
        "Hardcoded chatbots break immediately when flight contexts or passenger tiers change.",
        "Uncontrolled AI waivers create direct financial leakage and regulatory non-compliance."
    ])
    add_card(s2, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), "Why Policy-Grounded AI", [
        "Combines empathetic natural language understanding with 100% deterministic rule enforcement.",
        "Protects corporate liability by enforcing agent waiver limits (e.g. max ₹1,500).",
        "Generates immutable, inspectable audit trails for every decision and external transaction."
    ])

    # =========================================================================
    # SLIDE 3: Requirements & Success Criteria
    # =========================================================================
    s3 = prs.slides.add_slide(blank_slide_layout)
    add_header(s3, "Requirements & Core Success Criteria")
    add_card(s3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3), "Perception & Intent Recognition", [
        "Accurately extract intent (refund, rebooking, vouchers, hotel, upgrade).",
        "Detect customer frustration and emotional cues without over-apologizing.",
        "Ask only necessary questions when customer/booking context is missing."
    ])
    add_card(s3, Inches(6.8), Inches(1.8), Inches(5.7), Inches(2.3), "Zero-Hallucination Grounding", [
        "Evaluate customer entitlements against the official Data Pack only.",
        "Strictly prohibit inventing flight numbers, inventory, or payment methods.",
        "Explicitly separate customer data, bookings, service rules, and tone guidelines."
    ])
    add_card(s3, Inches(0.8), Inches(4.4), Inches(5.6), Inches(2.4), "Autonomous Tool Execution", [
        "Execute permitted actions: meal vouchers, lounge passes, transit hotel rooms.",
        "Clearly tag simulated actions [SIMULATED] for external transparency.",
        "Support priority rebooking for Gold and Platinum loyalty members."
    ])
    add_card(s3, Inches(6.8), Inches(4.4), Inches(5.7), Inches(2.4), "Supervised Human Escalation & Audit", [
        "Escalate legal threats, formal complaints, and fare differences > ₹1,500.",
        "Produce structured escalation records with specific recommended human actions.",
        "Maintain real-time, inspectable audit logs for compliance review."
    ])

    # =========================================================================
    # SLIDE 4: Data, Sources & Assumptions
    # =========================================================================
    s4 = prs.slides.add_slide(blank_slide_layout)
    add_header(s4, "Data Sources, Segregation & Operational Boundaries")
    add_card(s4, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Decoupled Data Architecture", [
        "customers.json: Profiles, tiers (Gold, Silver, Platinum), travel history, prior complaints.",
        "bookings.json: PNR, segments, cancellation/delay causes, payment instruments.",
        "policies.json: Explicit disruption service rules, delay tiers (<3h, 3-5h, >5h), waiver ceilings.",
        "actions.json: Strict whitelist of permitted agent actions vs. prohibited escalation triggers."
    ])
    add_card(s4, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "Source-of-Truth Enforcement", [
        "Single Source of Truth: Assignment 3 Data Pack PDF exclusively.",
        "Zero Invented Flights: Flight inventory is not hallucinated; operational dispatch noted.",
        "Zero Invented Policies: No ungrounded compensation, upgrade, or payment waivers.",
        "Tone-Only Calibration: PDF sample conversations provide empathy style only, not customer facts."
    ])
    add_card(s4, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), "Extensibility Proof", [
        "Completely data-driven: Adding Customer 4 ('Karan Roy', Bronze, PNR ZX9901) requires zero Python code edits.",
        "Automated regression test tests/test_extensibility.py proves dynamic ingestion and policy execution.",
        "Demonstrates enterprise-grade separation of data from runtime application logic."
    ])

    # =========================================================================
    # SLIDE 5: System Architecture
    # =========================================================================
    s5 = prs.slides.add_slide(blank_slide_layout)
    add_header(s5, "System Architecture: Modular & Safe Agent Pipeline")
    add_card(s5, Inches(0.8), Inches(1.8), Inches(2.7), Inches(4.8), "1. Interface & State", [
        "Streamlit UI",
        "Multi-turn Dialogue State",
        "Pre-Configured Scenarios",
        "Custom PNR Lookup",
        "Live Grounding Inspector",
        "Audit Log Viewer"
    ])
    add_card(s5, Inches(3.8), Inches(1.8), Inches(2.7), Inches(4.8), "2. Intent & Perception", [
        "IntentAgent",
        "Regex + Entity Extraction",
        "Frustration Detector",
        "Legal Threat Interceptor",
        "Customer & PNR Binding",
        "DataService Retrieval"
    ])
    add_card(s5, Inches(6.8), Inches(1.8), Inches(2.7), Inches(4.8), "3. Policy & Decision", [
        "Deterministic PolicyEngine",
        "Delay Tier Thresholds",
        "Cancellation vs Rebook",
        "Waiver Ceiling ($1,500)",
        "Loyalty Tier Gate",
        "DecisionEngine"
    ])
    add_card(s5, Inches(9.8), Inches(1.8), Inches(2.7), Inches(4.8), "4. Execution & Audit", [
        "Action Tools ([SIMULATED])",
        "Escalation Dispatcher",
        "ResponseAgent (LLM/Offline)",
        "Source Citation Injector",
        "Structured AuditLogger",
        "JSON/SQLite Persistence"
    ])

    # =========================================================================
    # SLIDE 6: Agent Process Flow
    # =========================================================================
    s6 = prs.slides.add_slide(blank_slide_layout)
    add_header(s6, "Agent Process Flow: 7-Stage Deterministic Pipeline")
    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3), "Stage 1 → 2: Message & Entity Extraction", [
        "Customer message received; regex & intent parser extract PNR, flight, amounts, and tone.",
        "Critical check: Immediate short-circuit if legal action or formal complaint detected."
    ])
    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(2.3), "Stage 3 → 4: Context Retrieval & Policy Evaluation", [
        "DataService fetches customer profile (tier, history) and flight booking records.",
        "Deterministic PolicyEngine checks entitlement rules against disruption type and hours."
    ])
    add_card(s6, Inches(0.8), Inches(4.4), Inches(5.6), Inches(2.4), "Stage 5: Autonomous Action or Escalation", [
        "If permitted: triggers generic simulated tools (meal voucher, lounge pass, delayed-hours hotel, refund).",
        "If prohibited or beyond limit: constructs structured EscalationRecord for human supervisors."
    ])
    add_card(s6, Inches(6.8), Inches(4.4), Inches(5.7), Inches(2.4), "Stage 6 → 7: Grounded Response & Audit Logging", [
        "ResponseAgent drafts empathetic message citing exact Service Rules from Data Pack.",
        "AuditLogger appends timestamped JSON audit record containing customer, intent, decision, and status."
    ])

    # =========================================================================
    # SLIDE 7: Agent & AI Design: Guardrails Against Hallucination
    # =========================================================================
    s7 = prs.slides.add_slide(blank_slide_layout)
    add_header(s7, "Agent & AI Design: Constrained LLM with Deterministic Engine")
    add_card(s7, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Role of the LLM", [
        "Restricted strictly to linguistic phrasing, empathy, and conversational fluency.",
        "NEVER acts as the authority for business policy or compensation entitlements.",
        "Operates under a strict system prompt prohibiting invented flights, policies, or monetary amounts."
    ])
    add_card(s7, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "Deterministic Policy Engine", [
        "Pure Python rule evaluator guarantees zero hallucinated decisions.",
        "Mathematically enforces delay thresholds: <3h (meal), 3-5h (lounge), >5h (delayed-hours hotel).",
        "Enforces hard ceiling on agent fare waivers: strictly <= ₹1,500."
    ])
    add_card(s7, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), "LLM Provider Abstraction", [
        "Pluggable LLMProvider interface supports OpenAI, Anthropic, Gemini, or Groq.",
        "Built-in DeterministicFallbackProvider guarantees 100% functionality offline without external API keys.",
        "Fail-safe architecture protects operations against API latency, rate limits, or network downtime."
    ])

    # =========================================================================
    # SLIDE 8: Scenario Demonstrations
    # =========================================================================
    s8 = prs.slides.add_slide(blank_slide_layout)
    add_header(s8, "Scenario Verification: 100% Policy-Driven Outcomes")
    add_card(s8, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Scenario 1: Priya Nair (Gold)", [
        "Disruption: SK-204 Cancelled (Operational). Customer expresses fury, asks for full refund + business upgrade.",
        "Policy Action: Free rebooking (priority tier) OR full refund approved to original payment within 7 days.",
        "Boundary Enforced: Cabin upgrade rejected & escalated; Gold tier gives priority rebooking only, not free upgrades."
    ])
    add_card(s8, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "Scenario 2: Arvind Kulkarni (Silver)", [
        "Disruption: SK-118 Delayed 4 hours. Customer frustrated over missed meeting, demands hotel room.",
        "Policy Action: ₹500 meal voucher issued + airport lounge access pass activated.",
        "Boundary Enforced: Hotel accommodation declined based on policy (>5 hours required). Policy citation provided."
    ])
    add_card(s8, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), "Scenario 3: Meher Kaur (Platinum)", [
        "Disruption: SK-305 Delayed 6h. Demands full-night hotel stay + higher-fare flight (₹2,000 difference).",
        "Policy Action: Meal voucher, lounge pass, and hotel for delayed hours (transit room) approved.",
        "Boundary Enforced: Full-night stay declined; ₹2,000 fare waiver exceeds ₹1,500 limit → Escalated to supervisor."
    ])

    # =========================================================================
    # SLIDE 9: Safety, Guardrails & Auditability
    # =========================================================================
    s9 = prs.slides.add_slide(blank_slide_layout)
    add_header(s9, "Safety, Compliance Guardrails & Transparent Auditability")
    add_card(s9, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Operational Guardrails", [
        "Zero Flight Hallucination: Rebooking explains priority queue; actual flight assignment awaits operational inventory.",
        "Payment Integrity: Refunds strictly locked to original payment instrument (no third-party card switches).",
        "Legal Threat Interception: Lawsuit/formal threats immediately escalated to Specialist Support."
    ])
    add_card(s9, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "Structured Escalation Dossier", [
        "Captures Customer Name, PNR, Issue, Requested Action, and Policy Limitation.",
        "Explicitly states Reason for Escalation and Recommended Human Action for specialist review.",
        "Creates clean operational handoffs between AI and human operations teams."
    ])
    add_card(s9, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), "Immutable Audit Trail", [
        "Every turn logs: timestamp, conversation_id, customer, PNR, intent, policy used, actions executed, status.",
        "Persisted to structured JSON log (data/audit_log.json) with interactive UI inspector.",
        "Zero secrets committed: environment variables managed via .env.example."
    ])

    # =========================================================================
    # SLIDE 10: Deployment & Future Enhancements
    # =========================================================================
    s10 = prs.slides.add_slide(blank_slide_layout)
    add_header(s10, "Deployment Architecture & Production Roadmap")
    add_card(s10, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Deployment Readiness", [
        "Turnkey Local Run: streamlit run app.py",
        "100% Automated Test Pass: pytest tests/ -v (17 automated policy, scenario, & security tests pass in 0.22s).",
        "Containerized: Dockerfile and docker-compose.yml ready for cloud deployment (AWS ECS, GCP Cloud Run, Streamlit Cloud)."
    ])
    add_card(s10, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "Current Scope & Boundaries", [
        "Data scope strictly derived from Assignment 3 Data Pack PDF.",
        "Simulated action tools clearly labeled to prevent mock transaction confusion.",
        "Deterministic fallback ensures complete presentation usability without paid LLM API keys."
    ])
    add_card(s10, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), "Production Roadmap", [
        "GDS / PSS Integration: Live Amadeus/Sabre API connectors for real-time flight inventory and seat booking.",
        "Payment Gateway API: Automated webhook integration for instantaneous merchant refund triggers.",
        "Human-in-the-Loop CRM: Direct Zendesk/Salesforce Service Cloud webhook integration for supervisor escalation queues."
    ])

    output_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "AIONOS_Assignment3_ResolutionAgent.pptx"
    prs.save(out_file)
    print(f"Presentation successfully saved to: {out_file}")

if __name__ == "__main__":
    create_deck()
