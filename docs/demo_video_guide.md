# Turnkey Demo Video Recording Guide & Screenplay

**Project:** SkyResolve — Airline Disruption Customer-Facing Resolution Agent  
**Assignment:** AIONOS Recruitment Assignment 3  
**Requirement:** 5 to 8-minute demo video hosted on Google Drive with open access  

---

## 🎥 Part 1: How to Record on Windows (No Extra Software Needed)

You can record your screen and microphone directly using Windows built-in tools:

### Option A: Windows Game Bar (Built-in to Windows 10/11)
1. Open your browser with the app running at `http://localhost:8501`.
2. Press **`Win + G`** on your keyboard to open the Xbox Game Bar.
3. Make sure your microphone is enabled (click the microphone icon in the Capture widget).
4. Press **`Win + Alt + R`** to start recording.
5. Follow the screenplay in **Part 2** below.
6. Press **`Win + Alt + R`** again to stop recording.
7. Your MP4 video will be saved in: `C:\Users\91989\Videos\Captures`.

### Option B: Loom or OBS Studio (Free)
- **Loom** (Chrome extension or desktop app): One-click recording with camera bubble and screen.
- **OBS Studio**: Free, open-source screen recorder.

---

## 🎬 Part 2: 5 to 7-Minute Turnkey Screenplay

Follow this exact sequence while recording:

| Time | On-Screen Action | What to Say (Word-for-Word Voiceover) |
| :--- | :--- | :--- |
| **00:00 - 00:45** | Show `http://localhost:8501` (Dashboard Header & FIDS strip). | *"Hello everyone. Today I am demonstrating SkyResolve, an autonomous, policy-grounded resolution agent built for AIONOS Recruitment Assignment 3. When airlines face disruptions, unconstrained chatbots often hallucinate flights or unauthorized refunds. SkyResolve decouples natural language understanding from deterministic policy enforcement to guarantee 100% compliance with airline service rules."* |
| **00:45 - 01:30** | Point out the Sidebar: Passenger Selection (`Priya Nair`, Gold, PNR `SK4821X`, flight `SK-204` Cancelled). | *"Notice our decoupled data architecture: all customer profiles, bookings, and policies are stored in separate JSON files. Here, Priya Nair's flight SK-204 is cancelled due to operational reasons."* |
| **01:30 - 02:45** | **Scenario 1 (Priya):**<br>1. Type `hi` -> Show natural greeting without premature tools.<br>2. Type: `What are my options for this cancelled flight?` -> Show priority rebooking & refund options.<br>3. Type: `Please issue my full refund to my card and give me a complimentary business class upgrade on my return flight.` | *"Watch how the agent responds. On a simple greeting, it greets Priya warmly without executing any premature vouchers. When she asks for options, it explains priority rebooking and refund. When she requests the refund and demands a free business-class upgrade, the agent approves and executes the refund under the Refund Processing Rule, but strictly rejects the cabin upgrade under Prohibited Item 1, immediately escalating the exception to a human supervisor."* |
| **02:45 - 03:15** | Click the **Grounding** and **Escalation** tabs in the right inspector. | *"In the inspector tab on the right, you can see the exact citations from the Assignment Data Pack, along with a formal Escalation Dossier detailing the PNR, policy boundary, and recommended human action."* |
| **03:15 - 04:30** | **Scenario 2 (Arvind):**<br>Switch sidebar to `Arvind Kulkarni` (Silver, PNR `TR1190B`, 4h delay).<br>Type: `My flight is delayed by 4 hours. Can I get a hotel room?` | *"Now we switch to Arvind Kulkarni. His flight is delayed 4 hours. Arvind requests a hotel room. Under the Service Rules, delays between 3 and 5 hours receive a ₹500 meal voucher and lounge access, but hotel accommodation strictly requires a delay of more than 5 hours. The agent issues the meal voucher and lounge pass, while politely declining the hotel room with the exact policy citation."* |
| **04:30 - 05:45** | **Scenario 3 (Meher):**<br>Switch sidebar to `Meher Kaur` (Platinum, PNR `WL7742`, 6h delay).<br>Type: `I want a full night hotel and waive a ₹2,000 fare difference for another flight.` | *"Next, Meher Kaur has a 6-hour delay. She asks for a full-night hotel and a ₹2,000 fare difference waiver. The agent correctly distinguishes between transit hotel accommodation covering the 6 delayed hours—which it approves—and a full-night stay, which it declines. Furthermore, because the ₹2,000 fare difference exceeds the ₹1,500 agent waiver ceiling, it automatically generates a supervisor escalation ticket."* |
| **05:45 - 06:45** | **Extensibility Test (Zero Hardcoding):**<br>Open the sidebar expander `➕ Add New Customer`.<br>Enter `Karan Roy`, PNR `KR8899`, delay `4.0` hours, click `Save & Select`. | *"A mandatory requirement from AIONOS is that the system must NOT be a hardcoded chatbot. Here, I add a brand-new 4th passenger, Karan Roy, through our extensibility interface. With zero changes to Python code, the generic Policy Engine immediately manages this new passenger according to service policies."* |
| **06:45 - 07:30** | Open terminal and run:<br>`pytest tests/ -v` | *"Finally, our automated test suite contains 17 comprehensive unit, integration, security, and extensibility tests, including tests proving zero flight number hallucinations and zero credential leakage. All 17 tests pass 100%."* |
| **07:30 - 07:50** | Click `📥 Download Session Record (JSON)` in the sidebar. | *"Every interaction is logged in an immutable, real-time audit trail that can be exported with one click for compliance review. Thank you!"* |

---

## ☁️ Part 3: Uploading to Google Drive with Open Access

As required by the assignment brief:
1. Go to **[drive.google.com](https://drive.google.com)** and sign in.
2. Drag and drop your recorded MP4 video into your Drive.
3. Right-click the uploaded video file and select **Share** → **Share**.
4. Under **General access**, change **Restricted** to:
   👉 **"Anyone with the link"** (Role: **Viewer**).
5. Click **"Copy link"**.
6. Paste this link into your submission form and in your project `README.md`.
