# Conversational Intake Agent & Verifier Agent Plan

## 1. Plan for a Conversational Intake Agent

To make the existing `IntakeAgent` conversational, you need to transition from a single-shot "extract everything at once" model to a stateful, iterative multi-turn workflow. 

### Architecture & State Management
- **Persistent Memory**: Instead of executing extraction in one go, maintain a `conversation_history` context alongside a central `extracted_data` state object in your backend.
- **Iterative Extraction Process**:
  1. **Initial Assessment**: The user provides a narrative. The agent extracts preliminary data and identifies the `doc_type`.
  2. **Rule Loading**: Once `doc_type` is determined, the agent fetches the specific "Make or Break" mandatory requirements for that document.
  3. **Gap Analysis**: The programmatic router compares `extracted_data` against `mandatory_fields`. It identifies exactly what is missing.
  4. **Conversational Turn**: The LLM is prompted to ask 1 or 2 polite, natural questions to fill the specific gaps (e.g., "I see you paid ₹50,000 to the mechanic. Did you try contacting their customer service first? If so, do you have a ticket number?").
  5. **Completion**: Once all requirements are fulfilled, transition the state to "Drafting" and invoke the next agent.

### Prompting Strategy for the Agent
Refactor `intake.py` to output a state struct containing both the populated JSON *and* a conversational reply. 

**System Prompt Example:**
```text
You are a conversational, precise Indian legal intake specialist. Your goal is to gather facts from the user to construct a comprehensive legal document.

DOCUMENT TYPE: {doc_type}

You MUST collect the following "Make or Break" facts before we can draft:
{doc_type_rules}

CURRENT EXTRACTED FACTS:
{current_state_json}

INSTRUCTIONS:
1. Parse the user's latest message and update the extracted facts.
2. Check if ALL mandatory rules for {doc_type} are met.
3. If facts are MISSING: set "is_complete" to false, and draft a polite "agent_reply" asking a specific question to get the missing details. DO NOT ask for more than 2 things at once.
4. If a Cheque Bounce date indicates it has been >30 days since the return memo, you MUST warn them in "agent_reply" that the legal window has expired.
5. If EVERYTHING is collected: set "is_complete" to true and use "agent_reply" to inform the user that you are drafting their document.

OUTPUT SCHEMA (Return ONLY valid JSON):
{{
  "extracted_data": {{ ... }},
  "is_complete": false,
  "missing_fields": ["str"],
  "agent_reply": "str"
}}
```

### Injecting the Mandatory Rules
Inject these specific rules directly into the `{doc_type_rules}` placeholder based on the active document:

- **FIR**: Must include Complainant details, Exact Time/Place, Narrative, and Accused details , if accused details unknown then write unknown male / female or unknown etc. **Conditionals**: If theft, demand specific stolen items list (e.g. IMEI/Reg numbers). If assault, ask for physical injuries and if an MLC (medical checkup) was done.
- **Legal Notice**: Must include Sender/Recipient details, Relationship, and Grievance chronology. **Strict requirements**: Must clearly extract The Demand (exact amount or action) and The Deadline (e.g. 15 or 30 days). Let the user decide the demand, do not guess.
- **Consumer Complaint**: Must include Parties, Transaction Proof (Invoice/Date/Amt), and Defect description. **Strict requirements**: Must confirm Prior Contact (ticket num/date of complaint to company) and the specific breakdown of Relief Sought (refund + compensation).
- **Cheque Bounce Notice**: Must include Drawer/Payee details, description of the Enforceable Debt, and Cheque particulars (Number/Date/Bank). **Strict requirements**: The Return Memo Date and the Return Reason. Apply explicit logic: if Return Memo is older than 30 days, trigger a legal expiry warning.
- **Tenant Eviction Notice**: Must include Landlord/Tenant details, Property Address, Origin of Tenancy & Rent Amt. **Strict requirements**: Must extract valid Legal Grounds (Unpaid Rent duration/amount, Personal Need, Lease Expiry, or Subletting details).

---

## 2. Verifier Agent Grading Parameters

Based on `backend/agents/verifier.py`, the Verifier Agent evaluates the finalized draft against specific legal & structural criteria. It computes the following parameters:

1. **`score`**: An overall numerical rating from 0 to 10.
2. **`is_complete`**: A boolean flag determining if all core elements constitute a legally valid document.
3. **`overall_quality`**: Categorized broadly as `"good"` (score 8-10), `"acceptable"` (score 5-7), or `"poor"` (score 1-4).
4. **`issues`**: An array of specific localized defects. Each issue details:
    - **`field`**: Where the error occurred (e.g., "Remedy Section").
    - **`severity`**: `"high"`, `"medium"`, or `"low"`.
    - **`suggestion`**: Actionable feedback to rectify the error.
5. **`missing_fields`**: Any legally mandatory clauses/headers (like a verification clause) that are missing.
6. **`recommendations`**: Soft improvements to strengthen the draft (e.g. formatting).
7. **`law_accuracy`**: `"correct"`, `"needs_review"`, or `"incorrect"`.
8. **`language_quality`**: `"formal"`, `"acceptable"`, or `"informal"`. It enforces standard legal terminology over colloquialisms.

### Specific Compliance Checks
While establishing the above factors, the verification systematically checks for:
- Completeness of Parties, location, and clear specific relief.
- Correct, updated penal sections (e.g., checking it used **BNS instead of IPC**, and **BNSS instead of CrPC**).
- Absolute prevention of hallucinated/fabricated legal section numbers.
- Bilingual elements handled smoothly if the user requested them.
- General adherence to Indian legal petition/notice structuring.

---

## 3. Frontend Chatbox Implementation Plan

To support the conversational nature of the redesigned Intake Agent, the React frontend must transition `CaseInput.jsx` from a static single-input form to a dynamic, animated, multi-turn chat interface. 

### Architecture & API Integration
Currently, `CaseInput` simply calls `startPipeline` directly. To support a conversational turn:
1. **New API Call**: Create a new API handler (e.g., `chatWithIntake`) that makes a standard asynchronous fetch request to an `/api/chat/intake` endpoint.
2. **Payload**: The payload should include `docType`, `sessionId`, and a `messages` array representing the entire conversation thread so the backend can maintain context.
3. **Response Handling**: The backend returns the `agent_reply` and `is_complete` boolean. 
4. **Pipeline Trigger**: The frontend only triggers the heavy SSE `startPipeline` or transitions to `PROCESSING` once the backend responds with `is_complete: true`.

### State Management (`CaseInput.jsx`)
Update the inner state to manage the new chat workflow:
- **`messages`**: `[{ role: 'user' | 'agent', content: 'string' }]` — Array storing the conversation history.
- **`isTyping`**: Boolean — Used to show an animated typing indicator or Loader while waiting for the Intake Agent's response.
- **`isComplete`**: Boolean — Tracks when the user is done with the intake phase.

### UI / UX Design Additions
- **Chat History View**: Add a scrollable container above the textarea to render the `messages` array.
    - **Agent Bubbles**: Style with the NyayaMitra UI (amber/zinc theme), giving it a more formal, assistant-like appearance.
    - **User Bubbles**: Style with a subtle zinc/gray background aligned to the right. 
- **Bottom Input Bar**: Keep the animated Framer Motion textarea card, but dock it to the bottom. Once `isComplete` is true, the input bar dissolves and is replaced by a prominent "Proceed to Drafting ->" button.
- **Auto-Scroll**: Implement a `useRef` pointing to the bottom of the chat view. Trigger `scrollIntoView({ behavior: 'smooth' })` every time the `messages` array updates so the latest question is always in view.

### Error Handling & Edge Cases
- Provide a clear "Retry" button if the intake API call times out or fails mid-conversation.
- Allow users to edit their last message if the agent misunderstood them.
- Introduce a "Skip/Force Proceed" button if the user cannot provide an obscure detail and wants the drafting agent to generate a draft with empty blanks anyway.
