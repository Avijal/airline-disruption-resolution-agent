# Data Sources, Strict Boundaries & Operational Assumptions

## 1. Single Source of Truth
This implementation strictly adheres to the rule:
> **The supplied assignment data pack (`Assignment 3_DataPack_CustomerResolutionAgent.pdf`) is the ONLY business source of truth.**

No outside airline regulations, compensation schemes (e.g. EU261, DGCA CAR Section 3), ungrounded payment methods, or flight numbers have been invented or assumed.

---

## 2. Segregation of Information
The system maintains strict physical and logical boundaries between four distinct categories of data:
1. **Customer Profiles (`data/customers.json`)**:
   - Contains identity, loyalty tier, contact, and past 12-month travel history.
   - Evaluated dynamically as runtime input; never embedded into conditional branching logic.
2. **Flight Bookings (`data/bookings.json`)**:
   - Contains PNR, flight number, origin/destination, dates, disruption status, and payment method.
3. **Service Rules (`data/policies.json`)**:
   - Explicit operational policies defining delay compensation thresholds (<3h, 3-5h, >5h), cancellation rights, refund timeframes (7 business days to original payment method), and fare difference waiver caps (₹1,500).
4. **Tone & Style Guidelines (`data/tone_guidelines.json`)**:
   - Distilled strictly from Section 5 ("Sample Prior Conversations").
   - These conversations are used exclusively to guide empathy, calm tone, and concise phrasing. They are never treated as facts or policy entitlements for Priya, Arvind, or Meher.

---

## 3. Operational Assumptions & Boundaries

### A. Flight Inventory & Rebooking
- **Assumption:** The Data Pack states that passengers on airline-cancelled flights are entitled to free rebooking on the next available flight within 24 hours. However, no flight inventory or timetable of alternative flight numbers is provided in the Data Pack.
- **Operational Rule:** The system strictly **refuses to hallucinate flight numbers** (e.g., creating fake flights like "SK-999"). The agent explains priority rebooking eligibility and informs the customer that seat assignment requires operational flight inventory dispatch from the airline's reservation system.

### B. Hotel Accommodation Scope
- **Assumption:** Under the Delay Compensation Rule, delays exceeding 5 hours qualify for hotel accommodation "covering only the delayed hours (not a full night's stay)".
- **Operational Rule:** Any customer request for an overnight or full-night hotel stay is explicitly narrowed or denied to cover transit/day-room hours corresponding to the delay.

### C. Fare Difference Waiver Limit
- **Assumption:** Under the Fare Difference Rule, passengers voluntarily choosing higher-fare flights must pay the difference. Agents cannot waive differences exceeding ₹1,500 without supervisor approval.
- **Operational Rule:** Any waiver request exceeding ₹1,500 (such as Meher Kaur's ₹2,000 difference) automatically halts autonomous resolution and triggers a structured supervisor escalation ticket.

### D. Legal & Formal Complaints
- **Assumption:** Section 4 lists handling threats of legal action or formal complaints as strictly prohibited for automated agents.
- **Operational Rule:** Immediate escalation to the Specialist Support Team is triggered, bypassing standard resolution flows.

### E. Simulated Tools
- **Assumption:** In this recruitment demonstration, live integrations with airline GDS systems (Amadeus, Sabre) or payment merchant gateways are simulated.
- **Operational Rule:** All external actions are explicitly prefixed with `[SIMULATED]` in the UI, responses, and audit records to maintain total transparency.
