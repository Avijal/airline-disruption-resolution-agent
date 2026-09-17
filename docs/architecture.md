# SkyResolve System Architecture Blueprint

## Architectural Overview

SkyResolve is designed around a strict principle: **Linguistic understanding is probabilistic; business policy enforcement must be deterministic.**

```mermaid
flowchart TD
    User([Customer / Reviewer]) <--> UI[Streamlit Interactive UI]
    UI <--> Workflow[AirlineSupportWorkflow Manager]
    
    subgraph PerceptionLayer [1. Perception & Intent Layer]
        Workflow --> IntentAgent[IntentAgent]
        IntentAgent --> Frustration[Frustration & Tone Detector]
        IntentAgent --> EntityExtractor[Regex & Entity Extractor]
        IntentAgent --> GuardrailCheck{Legal Threat or Formal Complaint?}
    end

    GuardrailCheck -->|Yes| ImmediateEscalate[Immediate Specialist Escalation]
    GuardrailCheck -->|No| ContextRetrieval

    subgraph DataLayer [2. Data Storage Layer]
        ContextRetrieval[DataService Context Fetch]
        ContextRetrieval --> CustDB[(customers.json)]
        ContextRetrieval --> BookDB[(bookings.json)]
        ContextRetrieval --> PolDB[(policies.json)]
        ContextRetrieval --> ActDB[(actions.json)]
    end

    subgraph CoreEngine [3. Deterministic Decision Layer]
        ContextRetrieval --> PolicyEngine[Deterministic PolicyEngine]
        PolicyEngine --> RulesEvaluator[Service Rules Evaluator]
        RulesEvaluator --> DelayRules[Delay Thresholds: <3h, 3-5h, >5h]
        RulesEvaluator --> CancelRules[Cancellation: Free Rebook vs Refund]
        RulesEvaluator --> FareRules[Fare Waiver Ceiling: max ₹1,500]
        RulesEvaluator --> LoyaltyRules[Loyalty: Priority Access Only]
        PolicyEngine --> DecisionEngine[DecisionEngine]
    end

    subgraph ExecutionLayer [4. Execution & Escalation Layer]
        DecisionEngine -->|Allowed Actions| ActionTools[Resolution Tools]
        ActionTools --> Act1[[SIMULATED] Rebook Priority Flight]
        ActionTools --> Act2[[SIMULATED] Issue Meal Voucher]
        ActionTools --> Act3[[SIMULATED] Grant Lounge Access]
        ActionTools --> Act4[[SIMULATED] Arrange Transit Hotel]
        ActionTools --> Act5[[SIMULATED] Initiate Refund]
        
        DecisionEngine -->|Prohibited / Authority Exceeded| EscalationQueue[Escalation Dispatcher]
        ImmediateEscalate --> EscalationQueue
        EscalationQueue --> EscDossier[Structured Escalation Record]
    end

    subgraph ResponseSynthesis [5. Grounded Response & Audit Layer]
        ActionTools --> ResponseAgent[ResponseAgent]
        EscalationQueue --> ResponseAgent
        ResponseAgent --> LLMChoice{LLM Configured?}
        LLMChoice -->|API Key Present| LiveLLM[OpenAI / Anthropic / Gemini Provider]
        LLMChoice -->|Offline / Default| DeterministicGen[Deterministic Fallback Generator]
        LiveLLM --> Citations[Source Citation Injection]
        DeterministicGen --> Citations
        Citations --> AuditLog[(Structured AuditLogger / audit_log.json)]
        AuditLog --> UI
    end
```

---

## Architectural Layers

### 1. Presentation & State Layer (`app.py`, `agents/workflow.py`)
- **Multi-Turn Session State**: Tracks chat history, current active customer, PNR binding, and the latest evaluation outcome.
- **Scenario Quick-Loader**: Enables instant loading of Priya, Arvind, or Meher data into the generic agent without hardcoded logic.
- **Real-Time Grounding Panel**: Displays exact source citations, internal policy evaluations, escalation dossiers, and audit JSON events.

### 2. Perception & Intent Layer (`agents/intent_agent.py`)
- **Entity Extraction**: Dynamically parses flight references, PNRs, requested actions, and monetary figures (e.g. ₹2,000 fare difference).
- **Tone & Frustration Detection**: Identifies emotional sentiment (e.g. "furious", "ruined") to calibrate conversational empathy.
- **Safety Interceptor**: Immediately short-circuits to human specialist escalation when legal threats or formal complaints are detected.

### 3. Data Service Layer (`services/data_service.py`)
- Strictly segregates customer records (`data/customers.json`), booking statuses (`data/bookings.json`), policies (`data/policies.json`), and actions (`data/actions.json`).
- Supports zero-code extensibility: appending a 4th customer to the JSON files enables instant resolution without Python code changes.

### 4. Deterministic Policy Layer (`core/policy_engine.py`, `core/decision_engine.py`)
- Pure Python logic executing the exact business rules from the Data Pack.
- Evaluates disruption status against mathematical thresholds:
  - `< 3 hours`: ₹500 meal voucher only.
  - `3 to 5 hours`: Meal voucher + airport lounge access pass.
  - `> 5 hours`: Meal voucher + lounge pass + hotel accommodation covering delayed hours only.
  - `Cancellation`: Free rebooking within 24 hours OR full refund to original payment within 7 business days.
  - `Fare Waiver Ceiling`: Agents cannot waive fare differences exceeding ₹1,500 without supervisor approval.
  - `Loyalty Priority`: Gold and Platinum members receive priority rebooking queue placement, but zero additional compensation beyond standard policy.

### 5. Action Execution Layer (`tools/resolution_tools.py`, `tools/escalation_tools.py`)
- Executes data-driven resolution actions tagged clearly as `[SIMULATED]`.
- Enforces strict operational honesty: does NOT hallucinate flight numbers when external inventory is unavailable.

### 6. Response & Audit Layer (`agents/response_agent.py`, `services/llm_provider.py`, `core/audit.py`)
- Synthesizes empathetic replies citing exact sections of the Data Pack.
- Works offline via `DeterministicFallbackProvider` or connects to live LLMs via `LLMProvider`.
- Appends immutable structured JSON audit records to `data/audit_log.json`.
