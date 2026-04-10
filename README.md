# NyayaMitra — AI Legal Document Drafting System

> "Nyaya" (न्याय) = Justice · "Mitra" (मित्र) = Friend

NyayaMitra helps ordinary Indian citizens draft legally sound documents by simply describing their situation in Hindi or English. A 4-agent AI pipeline transforms casual descriptions into print-ready legal documents.

## ⚠️ New Indian Criminal Laws (Effective 1 July 2024)

This project uses the **new criminal law codes** that replaced the colonial-era laws:

| Replaced | New Law | Short Name |
|----------|---------|------------|
| Indian Penal Code (IPC), 1860 | Bharatiya Nyaya Sanhita, 2023 | **BNS** |
| Code of Criminal Procedure (CrPC), 1973 | Bharatiya Nagarik Suraksha Sanhita, 2023 | **BNSS** |
| Indian Evidence Act, 1872 | Bharatiya Sakshya Adhiniyam, 2023 | **BSA** |

The NI Act 1881 (cheque bounce), Consumer Protection Act 2019, and Transfer of Property Act 1882 remain in force unchanged.

## Supported Document Types
| # | Document | Key Laws Cited |
|---|----------|----------------|
| 1 | FIR | BNS 2023 + BNSS 2023 |
| 2 | Legal Notice | BNS 2023 |
| 3 | Consumer Complaint | Consumer Protection Act 2019 |
| 4 | Cheque Bounce Notice | NI Act 1881 §138 (unchanged) |
| 5 | Tenant Eviction Notice | Transfer of Property Act + Rent Control Act |

## Agent Pipeline
```
User Input (Hindi/English)
        |
[1] IntakeAgent         — extracts structured case JSON
        |
[2] LegalResearchAgent  — RAG over BNS/BNSS/BSA corpus in ChromaDB
        |
[3] DrafterAgent        — generates formal bilingual document (BNS/BNSS citations)
        |
[4] VerifierAgent       — completeness check, flags missing fields
        |
PDF Download (bilingual, print-ready)
```

## Tech Stack
- **Backend**: Python 3.12 · FastAPI · Groq (Llama 3.3 70B) · ChromaDB 0.5.23 · SQLite · ReportLab · pypdf
- **Frontend**: React 18 · Vite · Tailwind CSS
- **Deploy**: Railway (backend) · Vercel (frontend)

## Quick Start

### Backend

```bash
cd backend
```

#### 1. Install dependencies

**On Windows** (no C++ Build Tools):
```bash
# Install chroma-hnswlib prebuilt wheel first (avoids C++ compiler requirement)
pip install chroma-hnswlib --only-binary=:all:

# Install chromadb without auto-resolving the hnswlib pin
pip install chromadb==0.5.23 --no-deps

# Install everything else
pip install -r requirements.txt

# Install remaining chromadb sub-dependencies
pip install build importlib-resources "kubernetes>=28.1.0" "mmh3>=4.0.1" \
  "onnxruntime>=1.14.1" "opentelemetry-api>=1.2.0" \
  "opentelemetry-exporter-otlp-proto-grpc>=1.2.0" \
  "opentelemetry-instrumentation-fastapi>=0.41b0" \
  "opentelemetry-sdk>=1.2.0" "posthog>=2.4.0" "pypika>=0.48.9" "bcrypt>=4.0.1"

# If you hit a Keras 3 / tf-keras error from sentence-transformers:
pip install tf-keras
```

**On macOS / Linux** (or Windows with C++ Build Tools installed):
```bash
pip install -r requirements.txt
```

#### 2. Configure environment
```bash
cp .env.example .env      # add your GROQ_API_KEY
```

#### 3. Seed the legal corpus
```bash
# Place PDF files in backend/data/laws/ first (see Legal Corpus Setup below)
# IMPORTANT: Run from the backend/ directory, not from data/laws/
python seed_chroma.py     # one-time, ~2 min
```

#### 4. Start the server
```bash
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
# create .env.local with: VITE_API_URL=http://localhost:8000
npm run dev
```

## Legal Corpus Setup

Place the following **PDF files** in `backend/data/laws/` before running `seed_chroma.py`:

| Filename | Act | Chunks |
|----------|-----|--------|
| `bns.pdf` | Bharatiya Nyaya Sanhita 2023 | 309 |
| `bnss.pdf` | Bharatiya Nagarik Suraksha Sanhita 2023 | 632 |
| `bsa.pdf` | Bharatiya Sakshya Adhiniyam 2023 | 130 |
| `consumer_protection_act.pdf` | Consumer Protection Act 2019 | 214 |
| `negotiable_instruments_act.pdf` | Negotiable Instruments Act 1881 | 80 |
| `transfer_of_property_act.pdf` | Transfer of Property Act 1882 | 126 |
| `rent_control_act.pdf` | Delhi Rent Control Act 1958 | 84 |
| **Total** | | **1,575** |

All PDFs are freely available from [indiacode.nic.in](https://indiacode.nic.in).

Chunking: 1,500 chars per chunk, 200 char overlap. Embedding model: `all-MiniLM-L6-v2` (runs locally via ONNX).

## Project Structure
```
nyayamitra/
├── backend/
│   ├── agents/            # 4 AI agent modules
│   │   ├── intake.py      # IntakeAgent — structured case extraction
│   │   ├── research.py    # LegalResearchAgent — RAG over legal corpus
│   │   ├── drafter.py     # DrafterAgent — bilingual document generation
│   │   └── verifier.py    # VerifierAgent — completeness check
│   ├── services/          # Groq, ChromaDB, PDF, SSE helpers
│   │   ├── chroma_service.py  # ChromaDB singleton + query_laws()
│   │   ├── groq_client.py     # Groq API wrapper
│   │   ├── pdf_generator.py   # ReportLab bilingual PDF
│   │   └── sse.py             # SSE streaming helpers
│   ├── db/                # SQLite schema + templates
│   ├── data/laws/         # Indian legal act PDF files (add before seeding)
│   ├── chroma_db/         # ChromaDB persistent storage (auto-created by seed)
│   ├── main.py            # FastAPI app entry point
│   └── seed_chroma.py     # One-time ChromaDB indexing script
└── frontend/
    └── src/
        ├── components/    # UI components
        ├── hooks/         # useSSE custom hook
        └── lib/           # API client
```

## Current Status

- [x] Backend dependencies installed (with Windows workarounds)
- [x] Law PDFs collected (7 files — BNS, BNSS, BSA, CPA, NI Act, TPA, Delhi Rent Control)
- [x] ChromaDB seeded — 1,575 chunks, clean single schema, cosine similarity
- [x] Agent modules: intake.py, research.py, drafter.py, verifier.py
- [x] Services: groq_client.py (3-retry backoff), chroma_service.py, pdf_generator.py, sse.py
- [x] schemas.py — Pydantic v2 models for all pipeline data
- [x] main.py — all 4 routes wired + run_pipeline() background orchestrator
- [x] Frontend — all 6 components + useSSE hook + API client
- [x] backend/.env created (add real GROQ_API_KEY to activate)
- [ ] GROQ_API_KEY filled in
- [ ] End-to-end pipeline test

## Environment Variables

### Backend (`backend/.env`)
```
GROQ_API_KEY=your_groq_api_key_here
```

### Frontend (`frontend/.env.local`)
```
VITE_API_URL=http://localhost:8000
```

## Known Issues (Windows)

1. **`chroma-hnswlib` build fails** — `chromadb==0.5.23` pins `chroma-hnswlib==0.7.6` which has no prebuilt Windows wheel. Workaround: install `chroma-hnswlib==0.7.5` (prebuilt) first, then `chromadb --no-deps`. The 0.7.5 wheel works fine at runtime despite the version mismatch.

2. **Keras 3 / tf-keras error** — The `transformers` package may throw `ValueError: Your currently installed version of Keras is Keras 3, but this is not yet supported`. Fix: `pip install tf-keras`.

3. **Unicode console errors** — Windows `cp1252` console can't render certain Unicode characters. The `seed_chroma.py` script uses ASCII-safe characters to avoid this.

4. **Posthog telemetry warnings** — `Failed to send telemetry event ... capture() takes 1 positional argument but 3 were given` — these are harmless and don't affect functionality. Caused by a posthog API version mismatch.

## License
MIT
