# NyayaMitra — Architecture Deep Dive

> **न्यायमित्र** = *Justice Friend* | AI legal document drafting for every Indian citizen, free.

---

## The Problem in One Line

50 million+ pending cases in India — not because courts are full, but because most citizens never start: a lawyer charges ₹3,000–₹15,000 just to draft a basic FIR or legal notice, legal language is opaque English, and post-July 2024 even many lawyers still cite **repealed laws** (IPC/CrPC — replaced by BNS/BNSS 2023).

---

## What NyayaMitra Does

User speaks/types in Hindi or Hinglish → 5 AI agents collaborate → print-ready English PDF + bilingual filing guide → in under 30 seconds, at ₹0.

---

## The 5-Agent Pipeline

```
User (Hindi / Hinglish / Bengali / Marathi / Tamil / English)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. IntakeAgent                              [Llama 3.3 70B] │
│  Multi-turn chat — collects all mandatory facts per doc type │
│  Replies in user's selected language (EN/HI/BN/MR/TA)        │
│  If chat pre-collected data → pipeline skips re-parsing       │
│  Anomaly detection: flags implausible stolen items at public  │
│  spaces (e.g., TV reported stolen from a market)              │
│  Output: structured JSON (parties, dates, location, claims)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LegalResearchAgent                       [Llama 3.1 8B]  │
│  Semantic search over 1,423 real Indian law sections          │
│  all-MiniLM-L6-v2 embeddings (local ONNX) + ChromaDB        │
│  FIR: hard-filters to BNS 2023 only (excludes BNSS/BSA)      │
│  Section accuracy rules: BNS 304 only if force from person;  │
│  BNS 305 only inside dwelling/vehicle; BNS 317 never victim  │
│  Hard max 4 sections — quality over quantity                  │
│  Output: [{section, act, title, reason}]                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. DrafterAgent                             [Llama 3.3 70B] │
│  Dedicated template per doc type (5 types)                   │
│  English-only output (no Hindi/Devanagari in document)       │
│  Auto-injects current date/time (no placeholder for time)    │
│  For theft/robbery: stolen items list + assailant description │
│  Cites only sections that directly apply — omits if unsure   │
│  Format: "Section X BNS 2023: Title" — no prose              │
│  Output: complete formal English legal document              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. VerifierAgent                            [Llama 3.3 70B] │
│  Completeness check: all mandatory fields present?           │
│  Reality rules: public place → reject dwelling-house sects   │
│  Semantic rules: BNS 304/305/317 misuse flagged              │
│  Output: quality score (0-100) + issues + recommendations    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. FilingAssistantAgent                     [Llama 3.1 8B]  │
│  Dedicated static handler per doc type — no Groq for routing │
│  FIR: 10-state e-FIR portal routing + violence gate          │
│  Consumer: e-Daakhil field mapping + 8-item doc checklist    │
│  Legal Notice: RPAD guide + delivery-date deadline calc      │
│  Cheque Bounce: Section 138 NI Act — 30-day/15-day deadlines │
│  Tenant Eviction: Rent Control Authority / Tis Hazari        │
│  Steps translated into user's language via Groq (_translate_ │
│  _steps): steps carry both .en and .[lang] text fields       │
│  Output: portal URL + multilingual steps + warnings          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  ReportLab PDF
             (English, generated_pdfs/)
```

Every step streams its status live to the frontend via **Server-Sent Events (SSE)**.

---

## Why This Tech Stack

### LLM: Groq + Llama (Free Tier)

| Agent | Model | Why |
|-------|-------|-----|
| Intake, Drafter, Verifier | Llama 3.3 70B | Quality-critical — needs reasoning + instruction following |
| Research, FilingAssistant | Llama 3.1 8B Instant | Utility tasks — fast, 500K TPD free limit |

**Why Groq over OpenAI/Gemini**: Entirely free. Sub-second latency on 70B. No credit card needed. Crucial for a zero-cost hackathon build.

### Vector DB: ChromaDB 0.5.23

- Persistent local storage (`chroma_db/`) — no managed service needed
- 1,423 real Indian law sections, indexed at section granularity
- `all-MiniLM-L6-v2` embeddings (local ONNX — no embedding API cost)
- Cosine similarity search, top-10 results, re-ranked by agent rules

**Why ChromaDB over Pinecone/Weaviate**: Runs fully local on Railway free tier. No API keys. No usage limits.

### RAG Corpus: 7 Indian Acts (1,423 Sections)

| Act | Sections | Why Included |
|-----|----------|--------------|
| Bharatiya Nyaya Sanhita (BNS) 2023 | 351 | Replaced IPC — all criminal offences |
| Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 | 528 | Replaced CrPC — procedure, FIR filing |
| Bharatiya Sakshya Adhiniyam (BSA) 2023 | 165 | Replaced Evidence Act |
| Consumer Protection Act 2019 | 63 | Consumer complaints |
| Negotiable Instruments Act 1881 | 143 | Cheque bounce (Section 138, unchanged) |
| Transfer of Property Act 1882 | 113 | Tenant eviction |
| Delhi Rent Control Act 1958 | 60 | Tenant eviction (Delhi routing) |

**The BNS/BNSS advantage**: On 1 July 2024, India replaced three colonial-era laws. Most AI tools and some lawyers still cite old IPC. A document citing repealed IPC sections can be challenged in court. NyayaMitra's corpus is built entirely from the new texts.

**Indexing strategy**: `seed_chroma.py` uses a two-pass regex parser (`^\d{1,3}\. Title.—body`) to parse `.txt` law files at real section boundaries, deduplicates TOC entries vs body text, and stores real section numbers in metadata — not chunk IDs.

### Backend: FastAPI + Python 3.12

- **Why FastAPI**: Native async support (all 5 agent calls are `async`), SSE via `sse-starlette`, automatic OpenAPI docs, Pydantic v2 validation
- **SSE over WebSockets**: One-directional streaming is enough for pipeline updates; SSE is simpler, reconnects automatically, works through proxies
- **Background tasks**: `BackgroundTasks` runs the pipeline after the HTTP response is sent — client immediately gets a session ID and connects to SSE

### Frontend: React 18 + Vite + Tailwind

- **Why Vite over CRA**: Near-instant dev server, fast HMR, smaller bundles
- **Why Tailwind**: Utility-first = fast iteration in a hackathon; no CSS file bloat
- **@paper-design/shaders-react**: WebGL MeshGradient shader — gives a premium visual feel with zero custom WebGL code

### i18n: Plain JS object lookup (no library)

`lib/i18n.js` exports three objects:
- `LANGUAGES` — 5 entries with `{ code, label, speechCode }` (speechCode drives Web Speech API locale)
- `STRINGS` — all UI labels keyed by `lang` then string key; components call `STRINGS[lang].key`
- `WELCOME_MESSAGES` — language-specific opening message for the intake chat

**Why no i18n library**: The string count is small and static. Adding react-i18next or similar would be over-engineering for a hackathon; a plain object lookup is zero-dependency and instantly readable.

The `lang` value is held in App state, passed as a prop to `CaseInput` and `ResultsPage → FilingAssistant`, and sent as a `lang` field in the `POST /pipeline` body so the backend can thread it through to the intake and filing agents.

### PDF: ReportLab

- Pure Python, no external service
- Generates print-ready English PDFs to `generated_pdfs/`
- No cloud storage — served directly from Railway's filesystem

### Deploy: Railway (backend) + Vercel (frontend)

- Both free tiers
- Railway: persistent filesystem for ChromaDB + generated PDFs
- Vercel: CDN-cached React build

---

## File Map

```
backend/
├── main.py                  FastAPI app — 5 routes, run_pipeline() orchestrator
├── schemas.py               Pydantic v2 models (PipelineRequest incl. lang, IncidentJSON, etc.)
├── seed_chroma.py           Two-pass law parser — builds ChromaDB from .txt files
├── requirements.txt
├── .env                     GROQ_API_KEY (fill before running)
│
├── agents/
│   ├── intake.py            IntakeAgent + ConversationalIntakeAgent (chat_intake)
│   │                        lang param → dynamic language instruction in system prompt
│   ├── research.py          LegalResearchAgent — RAG + BNS-only filter for FIR
│   ├── drafter.py           DrafterAgent — 5 doc-type templates, English-only
│   ├── verifier.py          VerifierAgent — quality score + reality rules
│   └── filing_assistant.py  FilingAssistantAgent — 5 dedicated static handlers
│                            + _translate_steps() for regional language step translation
│
├── services/
│   ├── chroma_service.py    Lazy singleton: init_chroma(), query_laws()
│   ├── groq_client.py       AsyncGroq wrapper, dual-model, 3-retry backoff
│   ├── pdf_generator.py     ReportLab PDF → generated_pdfs/
│   └── sse.py               asyncio.Queue per session, push_event(), create_sse_generator()
│
├── data/laws/               7 .txt law files + 7 PDFs (BNS, BNSS, BSA, CPA, NI, TPA, DRCA)
├── chroma_db/               Persistent ChromaDB storage (1,423 sections)
└── generated_pdfs/          PDF output (auto-created)

frontend/src/
├── App.jsx                  5-view state machine: LANDING → SELECT_DOC → INPUT_CASE → PROCESSING → VIEW_RESULTS
│                            selectedLang state; language selector in header; lang threaded to pipeline POST
├── index.css                Tailwind base + keyframes (fadeInUp, cardReveal, amberGlow, float)
│
├── components/
│   ├── LandingPage.jsx      Hero (emblem watermark), stats, how-it-works, pricing section, CTAs
│   │                        Pricing: Free (₹0/5 docs), Premium (₹249/30 docs), Add-on (₹199 lawyer verify)
│   ├── DocTypeSelector.jsx  5 doc-type cards with hover glow + stagger reveal
│   ├── CaseInput.jsx        Conversational intake chat; lang prop → i18n strings + speech locale
│   ├── ProcessingPage.jsx   Full-screen pipeline view + AgentPipeline stepper
│   ├── ResultsPage.jsx      Draft + verifier + filing guide + PDF download
│   │                        + lawyer verification upsell card → PaymentModal
│   ├── PaymentModal.jsx     Simulated ₹199 lawyer-review payment (UPI/card, idle→processing→success)
│   ├── AgentPipeline.jsx    5-agent stepper, animated connectors, amberGlow on active
│   ├── DraftPreview.jsx     White paper card, serif font, section refs amber
│   ├── VerifierFlags.jsx    Score circle, issues list, recommendations
│   ├── FilingAssistant.jsx  Portal card, steps (EN + regional), field mapping, language toggle
│   ├── PDFDownload.jsx      Blob download button + spinner
│   ├── ShaderBackground.jsx WebGL MeshGradient (zinc/amber), -z-10 fixed
│   └── SpaceParticles.jsx   Canvas 60-dot amber particles (landing only)
│
├── hooks/useSSE.js          EventSource hook — tracks all 5 agent events + filingData
└── lib/
    ├── api.js               startPipeline() (sends lang field), downloadPdf(), generateSessionId()
    └── i18n.js              LANGUAGES (5 configs + speechCode), STRINGS (all UI text × 5 langs),
                             WELCOME_MESSAGES (intake greeting × 5 langs)
```

---

## Data Flow — End to End

```
1. User selects language (header dropdown — EN/HI/BN/MR/TA)
2. User selects doc type (DocTypeSelector)
3. User types/speaks case description (CaseInput — Web Speech API, locale = selected language)
4. OR: multi-turn chat via /api/chat/intake (ConversationalIntakeAgent — replies in selected lang)
5. Frontend calls POST /pipeline with {doc_type, description, session_id, extracted_data?, lang}
6. Backend returns {status: "started"} immediately
7. Frontend opens EventSource on GET /stream/{session_id}
8. Backend runs run_pipeline() as BackgroundTask (lang threaded throughout):
   a. IntakeAgent → push_event("intake", "complete", {summary})
   b. LegalResearchAgent → push_event("research", "complete", {sections})
   c. DrafterAgent → push_event("drafter", "complete", {draft})
   d. VerifierAgent → push_event("verifier", "complete", {score, issues})
   e. PDF generated
   f. FilingAssistantAgent → _translate_steps() if lang != "en" → push_event("filing_assistant", "complete", {steps, portal})
   g. push_event("system", "complete", {pdf_ready, draft, verification, filing})
9. Frontend transitions to VIEW_RESULTS — renders all panels
10. FilingAssistant shows translated steps; language toggle switches between EN and regional text
11. User clicks "Verify — ₹199" → PaymentModal (demo payment flow)
12. User clicks Download PDF → GET /download-pdf/{session_id} → blob save
```

---

## Key Design Decisions

### Why skip re-parsing when chat intake is used

If the user goes through conversational intake (`/api/chat/intake`), the frontend already holds a fully structured `extracted_data` JSON. Passing it to `POST /pipeline` lets `run_pipeline()` bypass the IntakeAgent's LLM call entirely — the data is already clean. This eliminates the `[bracketed placeholder]` bug where the LLM re-parsed a description and introduced unknowns.

### Why BNS-only filter for FIR in ResearchAgent

FIR documents should cite criminal offence sections (BNS), not procedural sections (BNSS). Without the filter, ChromaDB returned procedural BNSS sections about FIR *filing procedure* — which don't belong in the document body. Hard filter: `where act == "Bharatiya Nyaya Sanhita 2023"`.

### Why static handlers in FilingAssistant

The original design called Groq for all 5 doc types. Under test, the 8B model JSON-truncated long filing guides. Switching to deterministic Python handlers (one per doc type) eliminated the truncation bug, cut latency, and saved TPD quota for the Research agent.

Translation is still done via Groq (`_translate_steps()`), but only after the deterministic handler has already produced the stable English output — so the LLM only handles the narrow, well-defined task of translation, not the full structure generation.

### Why freemium UI is frontend-only (currently)

The pricing section (Free/Premium tiers) and `PaymentModal` are UI scaffolding for the product vision. Actual quota tracking and payment processing are not yet wired to the backend. The header badge ("Premium • 12/30 Docs Used") is hardcoded. This is intentional for a hackathon demo — the architecture for enforcement (session-level doc count, auth token) is straightforward to add without restructuring the existing pipeline.

### Why English-only documents

Indian courts accept documents in English. Bilingual output in the same document caused formatting issues in ReportLab and confused the Verifier's completeness check. The filing guide is separately bilingual (EN/HI toggle in FilingAssistant.jsx).

### Why anomaly detection in IntakeAgent

A theft FIR mentioning a TV stolen from a market is almost certainly a mistake (confusion of location) or fraud. The agent flags this with a clarification question before the pipeline continues — preventing a nonsensical document from being generated and surfaced to the user.

---

## Indian Law Context (Critical)

On **1 July 2024**, India replaced three colonial-era laws:

| Repealed | New Code | Effective |
|----------|----------|-----------|
| Indian Penal Code (IPC) 1860 | Bharatiya Nyaya Sanhita (BNS) 2023 | 1 Jul 2024 |
| CrPC 1973 | Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 | 1 Jul 2024 |
| Indian Evidence Act 1872 | Bharatiya Sakshya Adhiniyam (BSA) 2023 | 1 Jul 2024 |

**All agents, templates, and the RAG corpus use the new codes exclusively.** A document citing IPC Section 379 (theft) instead of BNS Section 303 can be challenged in court. This is NyayaMitra's primary legal accuracy advantage over generic AI tools.

Laws **unchanged**: NI Act 1881 (Section 138 cheque bounce), Consumer Protection Act 2019, Transfer of Property Act 1882, state Rent Control Acts.

---

## Cost Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| LLM inference (70B + 8B) | Groq free tier | ₹0 |
| Vector DB | ChromaDB local | ₹0 |
| Embeddings | all-MiniLM-L6-v2 ONNX local | ₹0 |
| Backend hosting | Railway free tier | ₹0 |
| Frontend hosting | Vercel free tier | ₹0 |
| PDF generation | ReportLab (Python lib) | ₹0 |
| **Total** | | **₹0 / $0** |

---

## Windows Dev Setup Notes

| Issue | Fix |
|-------|-----|
| `chroma-hnswlib` no Windows wheel | `pip install chroma-hnswlib --only-binary=:all:` then `pip install chromadb==0.5.23 --no-deps` |
| Keras 3 / tf-keras error from sentence-transformers | `pip install tf-keras` |
| Unicode in print() breaks cp1252 console | Use ASCII equivalents in all `print()` calls |
| Posthog telemetry warnings | Harmless — posthog API version mismatch with chromadb 0.5.23 |


AI Agents — the 5 pipeline modules (Intake, Research, Drafter, Verifier, FilingAssistant). Each is an agent: it takes input, uses tools/LLMs, produces structured output.

Agentic AI — the system behavior: agents act sequentially, each step's output feeds the next, decisions are made autonomously (BNS filter, anomaly detection, state-based e-FIR routing) without human intervention mid-pipeline.

So: NyayaMitra is built with AI agents, and exhibits agentic behavior — the pipeline runs end-to-end autonomously once triggered.