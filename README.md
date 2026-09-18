# SkyResolve — Airline Disruption Customer Resolution Agent

**AIONOS Recruitment Assignment 3: Customer-Facing Resolution Agent**  
*Role:* Lead AI Engineer  
*Focus Area:* Airline Flight Disruption Customer Support  
*Source Data:* Strict adherence to `Assignment 3_DataPack_CustomerResolutionAgent.pdf`  

---

## 1. Problem Statement
Airline operational disruptions (flight cancellations and multi-hour delays) create high-stress situations where passengers demand immediate financial relief, alternative flights, meals, lounge access, and hotel stays.
Support centers experience massive inbound surges. Conventional LLM chatbots fail in this setting because they frequently **hallucinate flight numbers, invent unauthorized compensation, or grant policy waivers**, creating financial and legal exposure. Conversely, hardcoded decision trees are brittle and fail to empathize with frustrated travelers.

---

## 2. Solution Overview
**SkyResolve** is an enterprise-grade, policy-grounded resolution agent that decouples natural language understanding from deterministic policy enforcement:
- **Zero Hallucination Business Decisions:** All entitlement checks (refunds, rebooking windows, meal vouchers, lounge passes, transit hotel rooms, and fare difference caps) are evaluated by a pure Python `PolicyEngine` strictly implementing the rules from the assignment Data Pack.
- **Empathetic Dialogue:** An `IntentAgent` recognizes customer emotions (e.g. "furious", "ruined my trip") and responds calmly and concisely without over-apologizing or making empty promises.
- **Generic Data-Driven Architecture (No Hardcoding):** Customer profiles, booking records, service rules, and actions are segregated into separate JSON files. Adding a 4th customer requires zero modifications to Python code.
- **Safe Simulated Tool Execution:** Executes generic action tools (vouchers, refunds, priority rebooking queues) clearly labeled as `[SIMULATED]`.
- **First-Class Escalation & Audit Trail:** Automatically generates structured escalation tickets for human supervisors when requests exceed agent authority (e.g. fare differences > ₹1,500, legal threats, cabin upgrades). Logs every event to a queryable audit record.

---

## 🎯 Mandatory Assignment Deliverables
| Deliverable | Location / Access | Description |
|---|---|---|
| **Clickable Web Prototype** | Run `streamlit run app.py` at `http://localhost:8501` | Executive aviation dashboard with live chat, scenario switcher, grounding inspector & audit log |
| **10-Slide Presentation (.pptx)** | [`https://docs.google.com/presentation/d/1kPUlWZRR5YqSGKDBaMacMfbFK2MSWTeJ/edit?usp=sharing&ouid=111284376624057233679&rtpof=true&sd=true`](outputs/AIONOS_Assignment3_ResolutionAgent.pptx) | Professional 16:9 widescreen slide deck |
| **Slide Deck Guide & Speaker Notes** | [`docs/presentation_slides.md`](docs/presentation_slides.md) | Full slide-by-slide transcription and 15-minute defense speaker notes |
| **Demo Video Link (Google Drive)** | [Watch / Download Video (Google Drive)](https://drive.google.com/file/d/170zxXne-fI2pkfRjc7nwK5ozCXg1scDg/view?usp=sharing) | Public open-access video recording of the prototype walkthrough |
| **Automated Test Suite** | Run `pytest tests/ -v` | 17 tests (100% passing) verifying policy boundaries, security & extensibility |

---

## 3. System Architecture

```
                                Customer / Reviewer
                                         │
                                         ▼
                            Streamlit Web UI (app.py)
                                         │
                                         ▼
                    AirlineSupportWorkflow Manager (agents/workflow.py)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     Perception & Intent Layer                       Data Service Layer
     (agents/intent_agent.py)                     (services/data_service.py)
     - Entity & PNR Extraction                    - data/customers.json
     - Frustration & Tone Detection               - data/bookings.json
     - Legal / Formal Interceptor                 - data/policies.json
                 │                                - data/actions.json
                 └───────────────────────┬───────────────────────┘
                                         ▼
                      Deterministic Policy Engine (core/policy_engine.py)
                      - Delay Compensation Rule (<3h, 3-5h, >5h)
                      - Cancellation Rebooking & Refund Rule
                      - Fare Difference Rule (₹1,500 Waiver Ceiling)
                      - Loyalty Tier Priority Rule
                                         │
                                         ▼
                      Decision Engine (core/decision_engine.py)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ [Allowed Actions]                             │ [Authority Exceeded / Prohibited]
                 ▼                                               ▼
         Resolution Tools (tools/)                     Escalation Dispatcher
         - simulate_rebooking                          - create_escalation_record
         - simulate_issue_meal_voucher                 - dispatch_escalation
         - simulate_grant_lounge_access                          │
         - simulate_arrange_hotel                                │
         - simulate_initiate_refund                              │
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                     Response Agent & LLM Provider (agents/response_agent.py)
                     - Synthesizes empathetic response
                     - Injects exact Data Pack source citations
                     - Works offline with DeterministicFallbackProvider or OpenAI/Anthropic/Gemini
                                         │
                                         ▼
                     Structured Audit Logger (core/audit.py)
                     - Appends immutable event to data/audit_log.json
```

---

## 4. Strict Grounding & No-Hardcoding Guarantee

### Single Source of Truth
All business facts, policies, and actions originate solely from the supplied **Assignment 3 Data Pack PDF**:
1. **Cancellation Rebooking Rule:** Free rebooking on the next available flight within 24 hours OR full refund to original payment within 7 business days.
2. **Delay Compensation Rule:**
   - `< 3 hours`: ₹500 meal voucher.
   - `3 to 5 hours`: Meal voucher + airport lounge access.
   - `> 5 hours`: Meal voucher + lounge access + hotel accommodation covering delayed hours only (not a full night's stay).
3. **Fare Difference Rule:** Customers choosing higher-fare flights must pay the difference. Agents cannot waive differences above ₹1,500 without supervisor approval.
4. **Loyalty Tier Rule:** Gold and Platinum members receive priority rebooking access, but no additional compensation beyond standard policy.
5. **Prohibited Actions:** No excess compensation, no fare waiver > ₹1,500, no non-airline disruption exceptions, no refunds to non-original payment methods, and immediate escalation for legal threats or formal complaints.
6. **Sample Prior Conversations:** Used solely to calibrate tone and empathy guidelines (`data/tone_guidelines.json`). They are never used as customer facts or policy rules.

### How Hardcoding is Prevented
There is **zero** customer-specific logic (e.g. `if customer == 'Priya'`) anywhere in the application.
- Profiles live in `data/customers.json`.
- Bookings live in `data/bookings.json`.
- Rules live in `data/policies.json`.
- Adding a 4th customer and booking allows the agent to immediately evaluate and resolve requests using the exact same generic logic. This is verified by `tests/test_extensibility.py`.

---

## 5. Verification of the Three Required Scenarios

| Scenario | Customer & Status | Customer Request | Policy-Grounded Agent Resolution | Status |
|---|---|---|---|---|
| **Scenario 1** | **Priya Nair** (Gold)<br>Flight SK-204 Cancelled | Full cash refund + free upgrade to business class on return flight | • Approves and initiates full refund to original card within 7 business days.<br>• Declines free cabin upgrade (Gold tier grants priority rebooking only).<br>• Escalates upgrade request to Specialist Support. | 🚨 `ESCALATED` |
| **Scenario 2** | **Arvind Kulkarni** (Silver)<br>Flight SK-118 Delayed 4h | Hotel accommodation for long delay | • Issues ₹500 meal voucher and activates airport lounge pass.<br>• Rejects hotel request: policy requires delay > 5 hours to qualify.<br>• Cites Delay Compensation Rule. | ✅ `RESOLVED` |
| **Scenario 3** | **Meher Kaur** (Platinum)<br>Flight SK-305 Delayed 6h | Full night's hotel stay + move to higher-fare flight (₹2,000 difference) | • Approves transit hotel accommodation covering the 6 delayed hours.<br>• Declines full-night stay per policy boundary.<br>• Flags ₹2,000 fare difference as exceeding agent ₹1,500 waiver limit.<br>• Escalates to supervisor for waiver approval. | 🚨 `ESCALATED` |

---

## 6. Project Structure

```
airline_resolution_agent/
│
├── app.py                     # Interactive Streamlit Web Application
├── requirements.txt           # Production dependencies
├── .env.example               # Environment configuration template
├── .gitignore                 # Secrets, cache, and log exclusions
├── Dockerfile                 # Containerized deployment specification
├── .dockerignore              # Docker build exclusions
│
├── data/                      # Segregated pure data storage
│   ├── customers.json         # Customer profiles & loyalty tiers
│   ├── bookings.json          # Flight segments, disruption statuses, payments
│   ├── policies.json          # Strict disruption service rules & thresholds
│   ├── actions.json           # Whitelist of allowed vs prohibited actions
│   ├── source_metadata.json   # Citation references from Data Pack
│   └── tone_guidelines.json   # Tone & empathy standards from sample chats
│
├── core/                      # Core decision & policy engines
│   ├── policy_engine.py       # 100% deterministic rule evaluation
│   ├── decision_engine.py     # Orchestrates policies with concrete tools
│   ├── escalation.py          # Structured escalation record generator
│   └── audit.py               # Append-only structured JSON audit logger
│
├── tools/                     # Generic action & escalation tools
│   ├── customer_tools.py      # Customer profile retrieval
│   ├── booking_tools.py       # Booking status retrieval
│   ├── resolution_tools.py    # [SIMULATED] generic action execution
│   └── escalation_tools.py    # Escalation ticket dispatcher
│
├── agents/                    # Conversational agent modules
│   ├── intent_agent.py        # Intent parser & frustration detector
│   ├── response_agent.py      # Grounded response synthesizer
│   ├── resolution_agent.py    # End-to-end conversation coordinator
│   └── workflow.py            # Multi-turn session state manager
│
├── services/                  # Infrastructure & provider services
│   ├── data_service.py        # Hot-reloading data access layer
│   └── llm_provider.py        # LLM abstraction (OpenAI, Gemini, Offline)
│
├── tests/                     # Comprehensive automated pytest suite
│   ├── test_policy_engine.py  # 10 rule & threshold validation tests
│   ├── test_scenarios.py      # End-to-end Priya, Arvind, Meher tests
│   ├── test_security.py       # Guardrails, legal threats, zero-flight-hallucination
│   └── test_extensibility.py  # Zero-code 4th customer insertion test
│
├── scripts/                   # Automation scripts
│   └── generate_ppt.py        # Programmatic 10-slide PowerPoint generator
│
├── outputs/                   # Deliverables
│   └── AIONOS_Assignment3_ResolutionAgent.pptx  # 10-slide presentation deck
│
└── docs/                      # Complete assignment documentation
    ├── architecture.md        # Architectural blueprint & mermaid diagram
    ├── presentation_slides.md # Slide deck content & speaker notes
    ├── demo_script.md         # Turnkey 5-8 minute demonstration script
    └── assumptions.md         # Data boundaries & zero-hallucination rules
```

---

## 7. Setup & Local Run Instructions

### Prerequisites
- Python 3.11+
- pip

### Step 1: Clone or Navigate to Directory
```bash
cd airline_resolution_agent
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Automated Tests
```bash
pytest tests/ -v
```
*Expected Result:* All 17 unit, scenario, security, and extensibility tests pass in < 0.5s.

### Step 4: Launch Interactive Streamlit UI
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 8. Environment Variables & Model Configuration

Copy `.env.example` to `.env` if you wish to configure live LLM APIs:
```bash
cp .env.example .env
```

| Variable | Options / Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `deterministic` (default), `openai`, `anthropic`, `gemini` | Model provider to use |
| `LLM_MODEL` | e.g. `gpt-4o`, `claude-3-5-sonnet`, `gemini-1.5-flash` | Specific model identifier |
| `LLM_API_KEY` | *(Optional)* | API key for external provider |

> **Note on Offline Independence:** If no API key is provided, SkyResolve seamlessly defaults to `DeterministicFallbackProvider`. The application remains **100% functional, policy-accurate, and fully testable without external API keys or internet access**.

---

## 9. Docker Deployment

To build and run as a Docker container:
```bash
docker build -t skyresolve-agent:latest .
docker run -d -p 8501:8501 --name skyresolve skyresolve-agent:latest
```
Access the application at `http://localhost:8501`.

---

## 10. AI Tools Used

### Development Phase
- **Antigravity (DeepMind Agentic Pair Programmer):** Used for architectural planning, test generation, modular refactoring, and automated validation.
- **Python-pptx:** Programmatic generation of the 10-slide widescreen presentation deck.

### Runtime Architecture
- **Perception:** Regex and NLP entity extraction for deterministic intent identification.
- **Decisioning:** 100% deterministic pure-Python policy engine (`core/policy_engine.py`).
- **Response Generation:** Pluggable `LLMProvider` abstraction constrained by strict system prompts, backed by a deterministic fallback generator.

---

## 11. Known Limitations & Production Enhancements
1. **Live GDS Integration:** In this prototype, flight rebooking is simulated with zero flight hallucination. In production, connect live Amadeus/Sabre APIs for real-time inventory checks.
2. **Merchant Refund Webhooks:** Refunds are staged and logged as simulated records. In production, integrate Stripe/Razorpay refund webhooks.
3. **Supervisor CRM Queue:** Escalations generate structured records; in production, dispatch directly to Zendesk/Salesforce tickets.
