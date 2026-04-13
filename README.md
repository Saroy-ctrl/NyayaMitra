# NyayaMitra — Hackathon Overview

> **न्यायमित्र** = *Justice Friend*
> AI-powered legal document drafting for every Indian citizen — in Hindi or English, for free.

---

## The Problem

India has **1.4 billion people** and a **judicial backlog of 50 million+ pending cases**. The core issue is not lack of courts — it is that most citizens never even begin the legal process because:

| Barrier | Reality |
|--------|---------|
| **Cost** | A lawyer charges ₹3,000–₹15,000 just to draft a basic FIR complaint or legal notice |
| **Language** | Legal documents are in dense English; most Indians think in Hindi or their mother tongue |
| **Knowledge gap** | Citizens don't know which sections apply — and post-July 2024, even many lawyers still cite the **old IPC/CrPC** which were replaced |
| **Access** | Rural and semi-urban users have no easy access to legal aid |

Result: Snatching victims don't file FIRs. Consumer fraud victims swallow the loss. Cheque bounce cases go unpursued. Tenants face illegal evictions.

---
    
## The Solution — NyayaMitra

A user describes their situation in **plain Hindi or Hinglish** — by typing or speaking. NyayaMitra produces a **complete, print-ready, legally correct English document** in under 30 seconds — citing the right law, with the right sections, at zero cost.

### What It Generates

| Document | Cites |
|----------|-------|
| FIR (First Information Report) | BNS 2023 + BNSS 2023 |
| Legal Notice | BNS 2023 |
| Consumer Complaint | Consumer Protection Act 2019 |
| Cheque Bounce Notice | NI Act 1881 §138 |
| Tenant Eviction Notice | Transfer of Property Act + Delhi Rent Control Act |

---

## How It Works — The 5-Agent Pipeline

```
User types in Hindi/English
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1 — IntakeAgent                          [Llama 3.3 70B] │
│  Multi-turn conversational chat collects all mandatory facts  │
│  FIR requires: name, address, contact, date, time, location  │
│  IMEI only for phones/laptops; vehicle → reg + chassis no.   │
│  Anomaly detection: flags implausible items at public spaces  │
│  If chat already collected data → run_intake SKIPPED,        │
│  extracted_data passed directly (no re-parsing via LLM)      │
│  Output: structured JSON                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2 — LegalResearchAgent                   [Llama 3.1 8B]  │
│  Queries ChromaDB (1,423 real sections from 7 Indian acts)   │
│  all-MiniLM-L6-v2 embeddings, cosine similarity, top-10      │
│  FIR: hard-filters to BNS 2023 only (excludes BNSS)          │
│  Section accuracy rules: BNS 304 only if force from person;  │
│  BNS 305 only inside dwelling/vehicle/worship; BNS 317       │
│  (stolen property) never cited for victim — applies to fence │
│  Output: [{section, act, title, reason}]                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3 — DrafterAgent                         [Llama 3.3 70B] │
│  Takes structured case JSON + ranked law sections            │
│  Produces complete formal English-only legal document        │
│  For theft/robbery: includes stolen items list               │
│  For assault: physical description of accused section        │
│  Current date/time auto-injected (no placeholder for time)   │
│  Only cites sections that directly apply — omits if unsure   │
│  Cites ONLY BNS/BNSS/BSA — never old IPC/CrPC               │
│  Output: print-ready document text (English only)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4 — VerifierAgent                        [Llama 3.3 70B] │
│  Checks: correct sections cited? all fields present?         │
│  FIR: flags missing address or time as high-severity         │
│  Reality rules: public place → reject dwelling-house sects;  │
│  clothing-only accused → reject organised crime citations;   │
│  semantic check: BNS 304/305/317 misuse flagged              │
│  Output: quality score + improvement suggestions             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5 — FilingAssistantAgent                 [Llama 3.1 8B]  │
│  Dedicated handler per doc type:                             │
│  FIR → detects state, checks violence keywords,              │
│         routes to e-FIR portal (10 states) or offline        │
│  Consumer Complaint → e-Daakhil (edaakhil.nic.in),           │
│         maps 8 form fields from case JSON, returns           │
│         required_documents checklist (8 items)               │
│  Legal Notice → RPAD (registered post) + email guide,        │
│         demand deadline tracking, proof-of-service advice    │
│  Cheque Bounce → Magistrate Court filing, Section 138 NI     │
│         Act procedure, 30-day notice + 15-day wait logic,    │
│         deadline-critical warnings                           │
│  Tenant Eviction → Rent Control Authority / Civil Court,     │
│         Delhi Tis Hazari routing, grounds-based procedure,   │
│         illegal eviction warning (BNS 2023)                  │
│  Generates numbered bilingual steps for each path            │
│  Output: portal URL + steps + field mapping +                │
│          required_documents + warnings (all 5 doc types)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  PDF Download
          (ReportLab — English document)
```

Every step **streams its status live** to the frontend via **Server-Sent Events (SSE)** — the user sees each agent light up in real time.

---

## Why This Is Better Than Alternatives

| Approach | Problem |
|----------|---------|
| **Hiring a lawyer** | Expensive, slow, inaccessible in rural areas |
| **Generic ChatGPT/Gemini** | No Indian legal corpus, cites old IPC sections, no structured output, no PDF, no filing guide |
| **Government legal aid portals** | Static form-fills, no NLP, English-only, no AI assistance |
| **NyayaMitra** | Free, Hindi-first, voice input, 5-agent pipeline, RAG over current Indian law (BNS 2023), clean English PDF, bilingual filing guide, guides user all the way to actual filing |

### The BNS/BNSS Advantage

On **1 July 2024**, India replaced three colonial-era laws with new codes. **Most AI tools, websites, and even some lawyers still cite the old IPC**. NyayaMitra's RAG corpus is built entirely from the **new BNS/BNSS/BSA 2023 texts** — so every document it generates is legally current. A document citing repealed IPC sections can be rejected or challenged in court.

### Voice-First Accessibility

Users can speak their situation in Hindi or English directly into the chat — no typing required. The browser's native Web Speech API transcribes speech in real time and appends it to the message box. This makes NyayaMitra accessible to users with low digital literacy or those more comfortable speaking than typing.

### End-to-End — Not Just a Draft

Most tools stop at generating a document. NyayaMitra's FilingAssistant takes the user all the way to submission:
- **Violence detected** → offline in-person guide with what to bring to the police station
- **Non-violent theft/snatching** → direct link to that state's e-FIR portal with exact form field pre-fills
- **Consumer complaint** → NCDRC e-Daakhil portal: 8 form fields pre-filled from case JSON (complainant name, OP name, transaction date, relief sought etc.), checklist of 8 required documents to upload, bilingual step-by-step guide including filing fee info (free under ₹5 lakh)
- **Legal notice** → RPAD registered post guide, email timestamp backup, delivery-date deadline calculation
- **Cheque bounce** → Magistrate Court Section 138 NI Act procedure — 30-day notice window + 15-day payment wait + complaint filing steps; deadline-critical warnings
- **Tenant eviction** → Rent Control Authority / Civil Court routing (Delhi: Tis Hazari), grounds-based procedure, required documents checklist, warning against illegal eviction

---

## Technical Architecture

```
Frontend (React 18 + Vite + Tailwind + @paper-design/shaders-react)
    │
    ├── 5-view state machine (no React Router):
    │   LANDING → SELECT_DOC → INPUT_CASE → PROCESSING → VIEW_RESULTS
    │
    ├── Visual layer:
    │   ShaderBackground (WebGL MeshGradient, zinc/amber)
    │   SpaceParticles (canvas, landing only)
    │   Animations: fadeInUp, cardReveal stagger, amberGlow pipeline, float headline
    │
    ├── Voice input (Web Speech API — no external API):
    │   Mic button in chat toolbar, hi-IN / en-US based on selected language
    │   Appends transcript to textarea, amber glow + red dot while recording
    │   Graceful degradation: hidden if browser unsupported (Firefox/Safari)
    │
    │  POST /pipeline
    │  GET  /stream/{session_id}  ← SSE real-time updates
    │  GET  /download-pdf/{session_id}
    ▼
Backend (Python 3.12 + FastAPI)
    │
    ├── agents/
    │   ├── intake.py            ← Llama 3.3 70B  (JSON extraction)
    │   ├── research.py          ← Llama 3.1 8B   (RAG + re-ranking)
    │   ├── drafter.py           ← Llama 3.3 70B  (document generation)
    │   ├── verifier.py          ← Llama 3.3 70B  (quality check)
    │   └── filing_assistant.py  ← Llama 3.1 8B   (portal routing + steps)
    │
    ├── services/
    │   ├── chroma_service.py   ← 1,423 law sections, cosine similarity
    │   ├── groq_client.py      ← async, 3-retry exponential backoff
    │   ├── pdf_generator.py    ← ReportLab English PDF
    │   └── sse.py              ← asyncio.Queue per session
    │
    └── data/laws/
        ├── BNS 2023    — 351 sections
        ├── BNSS 2023   — 528 sections
        ├── BSA 2023    — 165 sections
        ├── Consumer Protection Act — 63 sections
        ├── NI Act 1881             — 143 sections
        ├── Transfer of Property Act — 113 sections
        └── Delhi Rent Control Act  —  60 sections
```

**Entire stack runs on free tiers** — Groq API (free), Railway (free backend deploy), Vercel (free frontend deploy).

---

## Demo Walkthrough

**Input** (Hindi/Hinglish):
> *"ek fir file karni hai mere dost ke liye, uska naam shreya kumari hai woh janakpuri district centre vishal tower mei uska purse snatching hua hai, phir use ladke ne assault kiya hai"*

**What happens:**
1. **IntakeAgent** — extracts: complainant = Shreya Kumari, location = Janakpuri District Centre Vishal Tower Delhi, incident = purse snatching + assault
2. **ResearchAgent** — finds BNS §304 (Robbery), BNS §115 (Assault), BNSS §173 (FIR procedure) from the 1,423-section corpus
3. **DrafterAgent** — writes complete FIR: stolen items list with placeholders, physical description of accused section, CCTV evidence request, correct BNS citations
4. **VerifierAgent** — confirms all FIR fields present, sections are BNS not IPC, flags any missing details
5. **FilingAssistantAgent** — detects Delhi + assault → **offline filing required** → step-by-step guide: what to bring, which counter to go to, how to get a copy of the FIR

**Output**: Print-ready English PDF + complete bilingual filing guide — ready to walk into Janakpuri Police Station.

---

## Future Upgrades

### Near-term
- **Voice input** — ✅ implemented via Web Speech API (hi-IN / en-US, browser-native, no API cost)
- **More state Rent Control Acts** — currently Delhi only; add Maharashtra, Karnataka, Tamil Nadu
- **WhatsApp bot** — citizen sends a WhatsApp message, receives a PDF back (Twilio / Meta API)
- **Document history** — localStorage-based history, no auth needed

### Medium-term
- **Lawyer review marketplace** — ₹99 advocate review before download
- **Multi-language** — Tamil, Telugu, Marathi, Bengali via IndicTrans2
- **Case status tracker** — save FIR/case number, get court updates via eCourts API
- **More e-FIR portals** — expand FilingAssistant to all 28 states + 8 UTs
- **e-Daakhil auto-fill** — browser extension that injects pre-filled values directly into the portal form

### Long-term / Research
- **Judgment RAG** — index Supreme Court + High Court judgments for precedent citation
- **Outcome prediction** — case success likelihood based on Indian Kanoon data by district
- **Legal chatbot** — ongoing conversation to understand rights before filing
- **Offline mobile app** — quantized Llama 3.2 1B for citizens without reliable internet

---

## Impact Metrics to Track

| Metric | Proxy for |
|--------|-----------|
| Documents generated | Overall reach |
| PDF downloads | Document was useful |
| Filing guide clicks (portal link) | End-to-end completion |
| Document type breakdown | Which legal problems are most common |
| User language ratio | Hindi vs English adoption |
| Geographic spread | Rural vs urban penetration |

---

## Stack Summary

| Layer | Technology |
|-------|-----------|
| LLM (quality agents) | Groq — Llama 3.3 70B (Intake, Drafter, Verifier) |
| LLM (utility agents) | Groq — Llama 3.1 8B Instant (Research, Filing Assistant) |
| Vector DB | ChromaDB 0.5.23 — 1,423 real law sections |
| Embeddings | all-MiniLM-L6-v2 (local, no API cost) |
| Backend | Python 3.12, FastAPI, ReportLab |
| Frontend | React 18, Vite, Tailwind CSS, @paper-design/shaders-react |
| UI Effects | WebGL MeshGradient shader, canvas particles, CSS keyframe animations |
| Streaming | Server-Sent Events (SSE) |
| Deploy | Railway (backend) + Vercel (frontend) |
| Cost | **₹0 / $0 — entirely free tier** |
