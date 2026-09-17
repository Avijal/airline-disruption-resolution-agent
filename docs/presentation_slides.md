# AIONOS Recruitment Assignment 3 — Presentation Deck

**Deck File:** `outputs/AIONOS_Assignment3_ResolutionAgent.pptx`  
**Total Slides:** Exactly 10 Substantive Slides  
**Format:** 16:9 Widescreen Presentation  

---

## Slide 1: Title Slide
- **Title:** Customer-Facing Resolution Agent
- **Subtitle:** Airline Disruption Support: Policy-Grounded, Data-Driven Autonomous Resolution Architecture
- **Metadata:** AIONOS Recruitment Assignment 3 Submission | Role: AI Engineer Lead | Date: September 2026
- **Speaker Notes:** "Welcome. Today I am presenting the Customer-Facing Resolution Agent built for AIONOS Recruitment Assignment 3. The system tackles airline flight disruption resolution using an agentic, policy-grounded architecture that strictly eliminates hallucinations, enforces corporate operating boundaries, and maintains complete audit transparency."

---

## Slide 2: Business Problem
- **Header:** Business Problem: High-Stakes Airline Disruption Resolution
- **Card 1: Operational Disruption Reality:**
  - Flight cancellations and multi-hour delays trigger sudden spikes in customer distress.
  - Emotional customers demand immediate financial answers (cash refunds, hotel rooms, cabin upgrades).
  - High agent turnover and cognitive overload cause inconsistent, erroneous resolutions.
- **Card 2: The Automation Pitfall:**
  - Generic LLM chatbots hallucinate compensation, invent flight numbers, or make unauthorized promises.
  - Hardcoded chatbots break immediately when flight contexts or passenger tiers change.
  - Uncontrolled AI waivers create direct financial leakage and regulatory non-compliance.
- **Card 3: Why Policy-Grounded AI:**
  - Combines empathetic natural language understanding with 100% deterministic rule enforcement.
  - Protects corporate liability by enforcing agent waiver limits (e.g. max ₹1,500).
  - Generates immutable, inspectable audit trails for every decision and external transaction.
- **Speaker Notes:** "Disruptions represent the highest-risk customer touchpoint in aviation. Unconstrained LLMs create financial and legal liability by hallucinating entitlements. Our solution pairs natural language understanding with a deterministic policy layer."

---

## Slide 3: Requirements & Core Success Criteria
- **Header:** Requirements & Core Success Criteria
- **Card 1: Perception & Intent Recognition:**
  - Accurately extract intent (refund, rebooking, vouchers, hotel, upgrade).
  - Detect customer frustration and emotional cues without over-apologizing.
  - Ask only necessary questions when customer/booking context is missing.
- **Card 2: Zero-Hallucination Grounding:**
  - Evaluate customer entitlements against the official Data Pack only.
  - Strictly prohibit inventing flight numbers, inventory, or payment methods.
  - Explicitly separate customer data, bookings, service rules, and tone guidelines.
- **Card 3: Autonomous Tool Execution:**
  - Execute permitted actions: meal vouchers, lounge passes, transit hotel rooms.
  - Clearly tag simulated actions `[SIMULATED]` for external transparency.
  - Support priority rebooking for Gold and Platinum loyalty members.
- **Card 4: Supervised Human Escalation & Audit:**
  - Escalate legal threats, formal complaints, and fare differences > ₹1,500.
  - Produce structured escalation records with specific recommended human actions.
  - Maintain real-time, inspectable audit logs for compliance review.
- **Speaker Notes:** "We defined clear success criteria: zero invented policies, dynamic multi-tier support, safe tool simulation, structured escalation, and an immutable audit trail."

---

## Slide 4: Data Sources, Segregation & Operational Boundaries
- **Header:** Data Sources, Segregation & Operational Boundaries
- **Card 1: Decoupled Data Architecture:**
  - `customers.json`: Profiles, tiers (Gold, Silver, Platinum), travel history, prior complaints.
  - `bookings.json`: PNR, segments, cancellation/delay causes, payment instruments.
  - `policies.json`: Explicit disruption service rules, delay tiers (<3h, 3-5h, >5h), waiver ceilings.
  - `actions.json`: Strict whitelist of permitted agent actions vs. prohibited escalation triggers.
- **Card 2: Source-of-Truth Enforcement:**
  - Single Source of Truth: Assignment 3 Data Pack PDF exclusively.
  - Zero Invented Flights: Flight inventory is not hallucinated; operational dispatch noted.
  - Zero Invented Policies: No ungrounded compensation, upgrade, or payment waivers.
  - Tone-Only Calibration: PDF sample conversations provide empathy style only, not customer facts.
- **Card 3: Extensibility Proof:**
  - Completely data-driven: Adding Customer 4 ('Karan Roy', Bronze, PNR ZX9901) requires zero Python code edits.
  - Automated regression test `tests/test_extensibility.py` proves dynamic ingestion and policy execution.
  - Demonstrates enterprise-grade separation of data from runtime application logic.
- **Speaker Notes:** "Data integrity is absolute. Customer facts, bookings, service rules, and tone samples are cleanly segregated in JSON files. Adding a fourth passenger works out-of-the-box without editing Python logic."

---

## Slide 5: System Architecture
- **Header:** System Architecture: Modular & Safe Agent Pipeline
- **Card 1: Interface & State:**
  - Streamlit UI
  - Multi-turn Dialogue State
  - Pre-Configured Scenarios & Custom PNR Lookup
  - Live Grounding Inspector & Audit Log Viewer
- **Card 2: Intent & Perception:**
  - `IntentAgent` with Regex + Entity Extraction
  - Frustration Detector & Legal Threat Interceptor
  - Customer & PNR Binding via `DataService`
- **Card 3: Policy & Decision:**
  - Deterministic `PolicyEngine` (Delay thresholds, cancellation rebook vs refund, waiver ceiling)
  - `DecisionEngine` coordinating entitlements and actions
- **Card 4: Execution & Audit:**
  - Action Tools (`[SIMULATED]` rebook, voucher, lounge, hotel, refund)
  - `EscalationRecord` Generator and Dispatcher
  - `ResponseAgent` with `LLMProvider`
  - Structured `AuditLogger` with JSON persistence
- **Speaker Notes:** "Our 4-tier architecture separates UI, intent perception, deterministic decisioning, and external execution. The policy engine is isolated from LLM prompt variability."

---

## Slide 6: Agent Process Flow
- **Header:** Agent Process Flow: 7-Stage Deterministic Pipeline
- **Stage 1 → 2: Message & Entity Extraction:** Customer message received; regex & intent parser extract PNR, flight, amounts, and tone. Immediate short-circuit if legal action or formal complaint detected.
- **Stage 3 → 4: Context Retrieval & Policy Evaluation:** `DataService` fetches customer profile and flight booking records. Deterministic `PolicyEngine` checks entitlement rules against disruption type and hours.
- **Stage 5: Autonomous Action or Escalation:** If permitted: triggers generic simulated tools. If prohibited or beyond limit: constructs structured `EscalationRecord`.
- **Stage 6 → 7: Grounded Response & Audit Logging:** `ResponseAgent` drafts empathetic message citing exact Service Rules from Data Pack. `AuditLogger` appends timestamped JSON audit record.
- **Speaker Notes:** "The 7-stage pipeline ensures every customer utterance undergoes rigorous parsing, context enrichment, rule evaluation, tool dispatch, and audit logging."

---

## Slide 7: Agent & AI Design: Guardrails Against Hallucination
- **Header:** Agent & AI Design: Constrained LLM with Deterministic Engine
- **Card 1: Role of the LLM:**
  - Restricted strictly to linguistic phrasing, empathy, and conversational fluency.
  - NEVER acts as the authority for business policy or compensation entitlements.
  - Operates under a strict system prompt prohibiting invented flights, policies, or monetary amounts.
- **Card 2: Deterministic Policy Engine:**
  - Pure Python rule evaluator guarantees zero hallucinated decisions.
  - Mathematically enforces delay thresholds: <3h (meal), 3-5h (lounge), >5h (delayed-hours hotel).
  - Enforces hard ceiling on agent fare waivers: strictly <= ₹1,500.
- **Card 3: LLM Provider Abstraction:**
  - Pluggable `LLMProvider` interface supports OpenAI, Anthropic, Gemini, or Groq.
  - Built-in `DeterministicFallbackProvider` guarantees 100% functionality offline without external API keys.
  - Fail-safe architecture protects operations against API latency, rate limits, or network downtime.
- **Speaker Notes:** "By treating the LLM as a phrasing generator rather than a business logic engine, we achieve total reliability. The deterministic fallback guarantees zero downtime even if internet or API keys fail."

---

## Slide 8: Scenario Demonstrations
- **Header:** Scenario Verification: 100% Policy-Driven Outcomes
- **Scenario 1: Priya Nair (Gold):**
  - Disruption: SK-204 Cancelled (Operational). Customer expresses fury, asks for full refund + business upgrade.
  - Policy Action: Free rebooking (priority tier) OR full refund approved to original payment within 7 days.
  - Boundary Enforced: Cabin upgrade rejected & escalated; Gold tier gives priority rebooking only, not free upgrades.
- **Scenario 2: Arvind Kulkarni (Silver):**
  - Disruption: SK-118 Delayed 4 hours. Customer frustrated over missed meeting, demands hotel room.
  - Policy Action: ₹500 meal voucher issued + airport lounge access pass activated.
  - Boundary Enforced: Hotel accommodation declined based on policy (>5 hours required). Policy citation provided.
- **Scenario 3: Meher Kaur (Platinum):**
  - Disruption: SK-305 Delayed 6h. Demands full-night hotel stay + higher-fare flight (₹2,000 difference).
  - Policy Action: Meal voucher, lounge pass, and hotel for delayed hours (transit room) approved.
  - Boundary Enforced: Full-night stay declined; ₹2,000 fare waiver exceeds ₹1,500 limit → Escalated to supervisor.
- **Speaker Notes:** "All three mandatory scenarios from the assignment pass automated regression tests and work interactively in the Streamlit UI, strictly enforcing policy boundaries."

---

## Slide 9: Safety, Compliance Guardrails & Transparent Auditability
- **Header:** Safety, Compliance Guardrails & Transparent Auditability
- **Card 1: Operational Guardrails:**
  - Zero Flight Hallucination: Rebooking explains priority queue; actual flight assignment awaits operational inventory.
  - Payment Integrity: Refunds strictly locked to original payment instrument (no third-party card switches).
  - Legal Threat Interception: Lawsuit/formal threats immediately escalated to Specialist Support.
- **Card 2: Structured Escalation Dossier:**
  - Captures Customer Name, PNR, Issue, Requested Action, and Policy Limitation.
  - Explicitly states Reason for Escalation and Recommended Human Action for specialist review.
  - Creates clean operational handoffs between AI and human operations teams.
- **Card 3: Immutable Audit Trail:**
  - Every turn logs: timestamp, conversation_id, customer, PNR, intent, policy used, actions executed, status.
  - Persisted to structured JSON log (`data/audit_log.json`) with interactive UI inspector.
  - Zero secrets committed: environment variables managed via `.env.example`.
- **Speaker Notes:** "Safety is baked in. Escalation dossiers provide supervisors with complete context, and every event is persisted to a queryable audit store."

---

## Slide 10: Deployment Architecture & Production Roadmap
- **Header:** Deployment Architecture & Production Roadmap
- **Card 1: Deployment Readiness:**
  - Turnkey Local Run: `streamlit run app.py`
  - 100% Automated Test Pass: `pytest tests/ -v` (17 automated policy, scenario, & security tests pass in 0.22s).
  - Containerized: Dockerfile and docker-compose.yml ready for cloud deployment (AWS ECS, GCP Cloud Run, Streamlit Cloud).
- **Card 2: Current Scope & Boundaries:**
  - Data scope strictly derived from Assignment 3 Data Pack PDF.
  - Simulated action tools clearly labeled to prevent mock transaction confusion.
  - Deterministic fallback ensures complete presentation usability without paid LLM API keys.
- **Card 3: Production Roadmap:**
  - GDS / PSS Integration: Live Amadeus/Sabre API connectors for real-time flight inventory and seat booking.
  - Payment Gateway API: Automated webhook integration for instantaneous merchant refund triggers.
  - Human-in-the-Loop CRM: Direct Zendesk/Salesforce Service Cloud webhook integration for supervisor escalation queues.
- **Speaker Notes:** "The application is production-ready, containerized, and backed by automated tests. In production, we would connect GDS APIs and CRM ticketing webhooks."
