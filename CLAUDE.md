# NyayaMitra — AI Legal Document Drafting System

## What This Is
Multi-agent legal document generator for Indian users. User describes their situation in casual Hindi/English, 4 AI agents collaborate to produce a print-ready legal document (FIR, legal notice, consumer complaint, cheque bounce notice, tenant eviction notice).

## Indian Law Update (Effective 1 July 2024)
Three major criminal law codes were replaced. All agents, templates, and corpus must use the NEW codes:

| Old Law | New Law | Effective |
|---------|---------|-----------|
| Indian Penal Code (IPC), 1860 | **Bharatiya Nyaya Sanhita (BNS), 2023** | 1 Jul 2024 |
| Code of Criminal Procedure (CrPC), 1973 | **Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023** | 1 Jul 2024 |
| Indian Evidence Act, 1872 | **Bharatiya Sakshya Adhiniyam (BSA), 2023** | 1 Jul 2024 |

Laws that remain **unchanged**: NI Act 1881 (cheque bounce, Section 138), Consumer Protection Act 2019, Transfer of Property Act 1882, state Rent Control Acts.

Never cite IPC or CrPC section numbers in generated documents — always use BNS / BNSS / BSA equivalents.

## Subagent Routing
This project uses two subagents. Route ALL work accordingly:
- **backend-engineer**: Everything in backend/ — Python, FastAPI, agents, RAG, PDF, SSE, data files
- **frontend-engineer**: Everything in frontend/ — React, Tailwind, components, hooks, API integration

When a task touches both frontend and backend (e.g., "wire up the SSE connection"), spawn BOTH subagents in parallel:
- backend-engineer handles the SSE endpoint
- frontend-engineer handles the useSSE hook and component updates

## Architecture
- 5 agents in sequential pipeline: Intake -> LegalResearch -> Drafter -> Verifier -> FilingAssistant
- Groq API — two models:
  - **Llama 3.3 70B** (MODEL_LARGE): Intake, Drafter, Verifier — quality-critical agents
  - **Llama 3.1 8B Instant** (MODEL_FAST): Research, FilingAssistant — utility agents, 500K TPD limit
- ChromaDB 0.5.23 for RAG over Indian legal corpus (1,423 real sections indexed):
  - Bharatiya Nyaya Sanhita (BNS) 2023 — 351 sections
  - Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 — 528 sections
  - Bharatiya Sakshya Adhiniyam (BSA) 2023 — 165 sections
  - Consumer Protection Act 2019 — 63 sections
  - Negotiable Instruments Act 1881 — 143 sections
  - Transfer of Property Act 1882 — 113 sections
  - Delhi Rent Control Act 1958 — 60 sections
- Indexing: seed_chroma.py parses .txt law files by section boundary regex (^\d{1,3}\. Title.—body), deduplicates TOC vs body, stores real section numbers. Pass 2 PDFs skipped if .txt covers the act.
- Embedding model: all-MiniLM-L6-v2 (local ONNX, cosine similarity)
- ChromaDB metadata schema per section: {act, section, title, use_cases, source_file}
- SQLite for document templates
- SSE streaming for real-time agent status to frontend
- ReportLab for bilingual PDF generation

## Tech Stack
- Backend: Python 3.12, FastAPI, ChromaDB 0.5.23, SQLite, ReportLab, sentence-transformers, pypdf
- Frontend: React 18 + Vite + Tailwind CSS + @paper-design/shaders-react
- LLM: Groq API with Llama 3.3 70B
- Deploy: Vercel (frontend) + Railway (backend)

## Key Constraints
- ALL services must be free tier
- No authentication needed
- Hindi + English bilingual support throughout
- Agent pipeline must stream status updates via SSE
- Always use BNS/BNSS/BSA — never IPC/CrPC/Evidence Act

## API Contract (shared between subagents)
- POST /pipeline — {doc_type: str, description: str, session_id: str}
- GET /stream/{session_id} — SSE events: {agent: str, status: str, data: dict}
- GET /download-pdf/{session_id} — serves PDF
- GET /health — {status, agents, laws_indexed}

## Document Types
1. FIR (First Information Report) — cites BNS + BNSS sections
2. Legal Notice — cites BNS sections
3. Consumer Complaint — cites Consumer Protection Act 2019
4. Cheque Bounce Notice — cites NI Act Section 138 (unchanged)
5. Tenant Eviction Notice — cites Transfer of Property Act + local Rent Control Act

## Current Build Status
- [x] Dependencies installed (with Windows workarounds — see below)
- [x] ChromaDB seeded with 1,423 real sections from 7 .txt law files (section-level, real section numbers)
- [x] Agent modules written: intake.py, research.py, drafter.py, verifier.py, filing_assistant.py
- [x] Services fully implemented: chroma_service.py, groq_client.py, pdf_generator.py, sse.py
- [x] schemas.py — Pydantic v2 models: PipelineRequest, IncidentJSON, LegalSection, VerificationResult, PipelineEvent
- [x] main.py — all 4 routes wired: POST /pipeline, GET /stream/{sid}, GET /download-pdf/{sid}, GET /health
- [x] run_pipeline() — chains all 5 agents as BackgroundTask with SSE events at each step
- [x] Frontend: all components + useSSE hook + API client + FilingAssistant component
- [x] Frontend UI revamp: 5-view state machine (LANDING → SELECT_DOC → INPUT_CASE → PROCESSING → VIEW_RESULTS)
- [x] LandingPage.jsx: hero (न्यायमित्र), stats, how-it-works, doc preview strip, dual CTAs
- [x] ShaderBackground.jsx: WebGL MeshGradient via @paper-design/shaders-react, dark zinc/amber palette
- [x] SpaceParticles.jsx: pure-canvas ambient amber particles (landing page)
- [x] Animations: fadeInUp view transitions, cardReveal stagger, amberGlow pipeline pulse, statReveal, float headline
- [x] ProcessingPage.jsx: full-screen pipeline view with spinner
- [x] ResultsPage.jsx: stacked draft + verifier + filing guide + PDF download
- [x] All 15 Playwright MCP assertions verified in Chrome
- [x] intake.py captures incident_time and parties[].contact
- [x] drafter.py: stolen items list for theft/robbery, assailant description, CCTV request, [bracketed placeholders]
- [x] filing_assistant.py: FIR (10-state e-FIR routing, violence detection), consumer_complaint (_handle_consumer_complaint: e-Daakhil field mapping from case JSON, required_documents checklist, dedicated Groq prompt), post guide for notices
- [x] groq_client.py: dual-model (70B for quality agents, 8B for utility agents), per-agent max_tokens
- [x] backend/.env created (GROQ_API_KEY placeholder — fill in real key)
- [ ] GROQ_API_KEY filled in backend/.env
- [ ] End-to-end pipeline test
- [ ] Frontend-backend SSE integration test

## Windows-Specific Setup Notes
These issues were encountered on Windows with Python 3.12.7 (64-bit) in an Anaconda environment:

### chroma-hnswlib build failure
`chromadb==0.5.23` pins `chroma-hnswlib==0.7.6` which has **no prebuilt Windows wheel** and requires Microsoft Visual C++ 14.0+ to compile. Workaround:
```bash
pip install chroma-hnswlib --only-binary=:all:   # installs 0.7.5 prebuilt
pip install chromadb==0.5.23 --no-deps            # skip the strict 0.7.6 pin
# then install chromadb's sub-deps manually
```
The 0.7.5 wheel works identically at runtime despite the version mismatch warning.

### Keras 3 / tf-keras error
The `transformers` library (pulled in by `sentence-transformers`) may throw:
`ValueError: Your currently installed version of Keras is Keras 3, but this is not yet supported in Transformers.`
Fix: `pip install tf-keras`

### Unicode console encoding
Windows `cp1252` console cannot render Unicode characters like arrows, checkmarks, etc.
`seed_chroma.py` was patched to use ASCII-safe print output.
**Rule**: Do not use Unicode symbols in print() statements — use ASCII equivalents.

### Posthog telemetry warnings
`Failed to send telemetry event ... capture() takes 1 positional argument but 3 were given`
These are harmless. Caused by a posthog API version mismatch with chromadb 0.5.23.

## File Layout (key files)
```
backend/
  main.py              — FastAPI app: all 4 routes wired, run_pipeline() 5-agent orchestrator
  schemas.py           — Pydantic v2 models (PipelineRequest, IncidentJSON, etc.)
  seed_chroma.py       — Two-pass .txt section parser + PDF fallback (1,423 sections, idempotent, drops+recreates collection on run)
  requirements.txt     — Python deps
  .env                 — GROQ_API_KEY (fill in real key)
  .env.example         — Template
  agents/
    intake.py          — IntakeAgent: extracts structured case JSON (incident_time, parties[].contact) [70B, 700 tokens]
    research.py        — LegalResearchAgent: RAG query over ChromaDB, filters chunk_ IDs [8B, 600 tokens]
    drafter.py         — DrafterAgent: bilingual legal document, stolen items, assailant description [70B, 3000 tokens]
    verifier.py        — VerifierAgent: completeness check [70B, 700 tokens]
    filing_assistant.py — FilingAssistantAgent: dedicated handler per doc type — FIR (10-state e-FIR routing + violence gate), consumer_complaint (_handle_consumer_complaint: e-Daakhil field mapping + required_documents + dedicated Groq prompt), post guide for notices [8B, 900 tokens]
  services/
    chroma_service.py  — Lazy singleton: init_chroma(), query_laws(), get_indexed_count()
    groq_client.py     — AsyncGroq wrapper, dual-model (MODEL_LARGE=70B / MODEL_FAST=8B), 3-retry backoff
    pdf_generator.py   — ReportLab bilingual PDF, output to generated_pdfs/
    sse.py             — asyncio.Queue per session, push_event(), close_stream(), create_sse_generator()
  data/laws/           — 7 .txt law files + 7 PDFs (BNS, BNSS, BSA, CPA, NI, TPA, DRCA)
  chroma_db/           — Persistent ChromaDB storage (1,423 real sections, cosine similarity)
  generated_pdfs/      — PDF output directory (auto-created by main.py)
  db/                  — SQLite schema + templates.json (5 doc types)
frontend/
  src/
    App.jsx            — 5-view state machine: LANDING, SELECT_DOC, INPUT_CASE, PROCESSING, VIEW_RESULTS
    index.css          — Tailwind base + fadeInUp, cardReveal, amberGlow, statReveal, float keyframes
    components/
      LandingPage.jsx      — Hero, stats (50M+/₹3k-15k/₹0), how-it-works, doc preview strip, CTAs
      DocTypeSelector.jsx  — Step 1 of 3, 5 cards with hover glow + stagger reveal, onBack prop
      CaseInput.jsx        — Step 2 of 3, amber doc badge, h-52 textarea, demo fill
      ProcessingPage.jsx   — Full-screen pipeline view with spinner
      ResultsPage.jsx      — Stacked: draft + verifier + filing guide + PDF download
      AgentPipeline.jsx    — 5-agent stepper (incl. filing_assistant), animated connectors, amberGlow on active
      ShaderBackground.jsx — WebGL MeshGradient (fixed -z-10), zinc/amber palette, zinc-950 CSS fallback
      SpaceParticles.jsx   — Canvas particles, 60 amber dots, landing page only
      DraftPreview.jsx     — White paper card, serif font, section refs highlighted amber
      VerifierFlags.jsx    — Score circle, issues list, recommendations
      FilingAssistant.jsx  — Portal card, steps, field mapping, required docs, EN/HI toggle
      PDFDownload.jsx      — Blob download button, spinner state
    hooks/             — useSSE.js (EventSource hook — tracks filingData from filing_assistant events)
    lib/               — api.js (startPipeline, downloadPdf, generateSessionId)
```

###text rules
1.Speak 8-10 words (max)
2.code normally
3.just speak english but less