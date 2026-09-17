# 5-8 Minute Turnkey Demonstration Script

**Project:** SkyResolve — Airline Disruption Customer Resolution Agent  
**Assignment:** AIONOS Recruitment Assignment 3  
**Presenter:** AI Engineer Lead  

---

## 00:00 – 01:00 | Introduction & Architecture Overview
- **Visual:** Open browser at `http://localhost:8501`.
- **Spoken Script:**
  > "Hello everyone. Today I'm demonstrating SkyResolve, an autonomous, policy-grounded resolution agent built for AIONOS Recruitment Assignment 3.
  > 
  > When airlines face operational disruptions, customer support teams are overwhelmed with complex requests—from full refunds and rebookings to hotel accommodations and fare waivers. Unconstrained LLM chatbots often fail here by hallucinating compensation or inventing flights.
  > 
  > SkyResolve solves this by decoupling linguistic comprehension from policy execution:
  > - An intent parser understands customer emotion and requests.
  > - A 100% deterministic Policy Engine enforces the exact rules from the assignment Data Pack.
  > - Generic action tools execute simulated operations with zero flight number hallucinations.
  > - Human escalation dossiers and structured audit logs are generated automatically in real time."

---

## 01:00 – 02:45 | Scenario 1: Priya Nair (Gold) — Cancellation & Upgrade
- **Visual:** In the sidebar, select `Scenario 1: Priya Nair (Gold)`.
- **Point out:**
  - Customer Card shows: Priya Nair, Tier: Gold, PNR: SK4821X, Flight SK-204 Cancelled (operational reasons).
- **Action:** Click `Prompt 1` or type:
  > *"My flight was cancelled and I am furious! I want a full cash refund and a free business class upgrade on my return flight."*
- **Observe Agent Response:**
  1. **Tone Handling:** Empathetic acknowledgment of her frustration without over-apologizing.
  2. **Allowed Action:** Full refund initiated to original credit card within 7 business days per Refund Processing Rule.
  3. **Policy Boundary & Escalation:** Explains that Gold tier grants priority rebooking, not free cabin upgrades. Free business upgrade demand is escalated to the Specialist Support Team.
  4. **Executed Action Banner:** `[SIMULATED] Full refund REF-TXN-XXXX initiated to original payment method (Original Credit Card).`
- **Visual:** Click the **Grounding** tab to show exact citations:
  - `Service Rules § Cancellation Rebooking Rule`
  - `Service Rules § Refund Processing Rule`
  - `Allowed vs. Prohibited Actions § Prohibited (Item 1)`
- **Visual:** Click the **Escalation** tab to show the formal escalation ticket generated.

---

## 02:45 – 04:15 | Scenario 2: Arvind Kulkarni (Silver) — 4-Hour Delay & Hotel
- **Visual:** In the sidebar, switch to `Scenario 2: Arvind Kulkarni (Silver)`.
- **Point out:**
  - Flight SK-118 Delayed 4 hours (Scheduled: 07:10, New Departure: 11:10).
- **Action:** Click `Prompt 1` or type:
  > *"My flight is delayed 4 hours. Since it's been such a long delay, I ask for hotel accommodation."*
- **Observe Agent Response:**
  1. **Eligibility Enforcement:** Policy states delays of 3 to 5 hours receive a meal voucher and airport lounge access.
  2. **Hotel Rejection:** Explains that hotel accommodation requires a delay exceeding 5 hours.
  3. **Executed Tools:** Both ₹500 meal voucher (`MEAL-VCH-XXXX`) and airport lounge access pass (`LNG-PASS-XXXX`) are issued.
  4. **Status:** Status remains `RESOLVED` (no escalation needed, policy correctly clarified).
- **Visual:** Check **Decision Log** tab to see `ineligible_requests`: "Hotel accommodation: Flight delay is 4.0 hours. Policy requires a delay of more than 5 hours to qualify for hotel accommodation."

---

## 04:15 – 05:45 | Scenario 3: Meher Kaur (Platinum) — 6-Hour Delay, Full-Night Hotel & Fare Waiver
- **Visual:** In the sidebar, switch to `Scenario 3: Meher Kaur (Platinum)`.
- **Point out:**
  - Flight SK-305 Delayed 6 hours (Scheduled: 14:00, New Departure: 20:00).
- **Action:** Click `Prompt 1` or type:
  > *"My flight is delayed 6 hours. I want a full night's hotel stay, and I want to be moved to a different higher-fare flight with a ₹2,000 fare difference."*
- **Observe Agent Response:**
  1. **Hotel Scope Distinction:** Approves transit hotel accommodation strictly covering the 6 delayed hours (`HTL-STAY-XXXX`), while politely rejecting the full night's stay.
  2. **Fare Difference Escalation:** Explains that under the Fare Difference Rule, agents cannot waive fare differences exceeding ₹1,500 without supervisor approval.
  3. **Supervisor Escalation:** Case is escalated to `supervisor` with recommended human action.
  4. **Status:** Visible badge turns red: `🚨 Status: ESCALATED`.
- **Visual:** Show **Escalation** tab displaying ticket routed to `supervisor` for ₹2,000 waiver approval.

---

## 05:45 – 06:45 | Proof of Extensibility & Zero Hardcoding
- **Visual:** Switch demonstration mode to `Custom PNR / Extensible Customer`.
- **Spoken Script:**
  > "A core requirement from AIONOS is that this must NOT be a hardcoded chatbot for just three names.
  > If we add a 4th customer to the JSON files, the generic PolicyEngine resolves them immediately without altering a single line of Python code."
- **Action:** Open terminal and run:
  ```bash
  pytest tests/test_extensibility.py -v
  ```
- **Spoken Script:**
  > "Here, our automated extensibility test programmatically adds 'Karan Roy' (Bronze tier, 2-hour delay) to the data layer. The test passes 100%, proving true data-driven architecture."

---

## 06:45 – 07:45 | Audit Trail & Test Suite Verification
- **Visual:** Click the **Audit Trail** tab in the UI.
- **Point out:**
  - Show the JSON audit event for each turn: timestamp, conversation ID, customer, PNR, intent, policies used, executed actions, status, and reason.
- **Action:** In terminal, run the complete test suite:
  ```bash
  pytest tests/ -v
  ```
- **Point out:**
  - 17 out of 17 tests passing in ~0.2 seconds.
- **Visual:** Point to generated presentation in `outputs/AIONOS_Assignment3_ResolutionAgent.pptx`.

---

## 07:45 – 08:00 | Conclusion & Wrap-Up
- **Spoken Script:**
  > "To summarize: SkyResolve delivers a fully working, policy-grounded, extensible resolution agent for airline disruptions. It honors the assignment Data Pack as the single source of truth, avoids flight hallucinations, executes safe simulated tools, and produces a complete audit trail.
  > 
  > The codebase includes a Dockerfile, automated test suite, 10-slide PowerPoint, and comprehensive documentation. Thank you!"
