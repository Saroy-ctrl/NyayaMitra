"""
main.py -- FastAPI application entry point for NyayaMitra.

Routes:
  POST /pipeline              -- kicks off the 4-agent sequential pipeline
  GET  /stream/{session_id}   -- SSE endpoint; streams agent status events
  GET  /download-pdf/{session_id} -- serves the generated PDF for a session
  GET  /health                -- liveness + stats (agents count, laws indexed)

CORS is configured wide-open for development; lock down for production.
"""

import json
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any other imports so GROQ_API_KEY is available
load_dotenv()

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from schemas import PipelineRequest
from services.sse import close_stream, create_sse_generator, push_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="NyayaMitra API", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS -- wide open for hackathon; lock down for production
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# PDF output directory
# ---------------------------------------------------------------------------
PDF_OUTPUT_DIR = Path(__file__).parent / "generated_pdfs"
PDF_OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Document templates -- loaded once at startup from db/templates.json
# ---------------------------------------------------------------------------
TEMPLATES_PATH = Path(__file__).parent / "db" / "templates.json"
_templates: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Session store -- holds pipeline results keyed by session_id
# ---------------------------------------------------------------------------
session_store: dict[str, dict] = {}


@app.on_event("startup")
async def _load_templates() -> None:
    """Load document templates from db/templates.json at startup."""
    global _templates
    if TEMPLATES_PATH.exists():
        with open(TEMPLATES_PATH, encoding="utf-8") as f:
            templates_list = json.load(f)
        # Support both list-of-dicts and plain dict formats
        if isinstance(templates_list, list):
            _templates = {t["doc_type"]: t for t in templates_list}
        else:
            _templates = templates_list
        logger.info("Loaded %d document templates", len(_templates))
    else:
        logger.warning("templates.json not found at %s -- using empty template set", TEMPLATES_PATH)


# ---------------------------------------------------------------------------
# Valid document types
# ---------------------------------------------------------------------------
VALID_DOC_TYPES = {
    "fir",
    "legal_notice",
    "consumer_complaint",
    "cheque_bounce",
    "tenant_eviction",
}


# ---------------------------------------------------------------------------
# Pipeline orchestration (background task)
# ---------------------------------------------------------------------------
async def run_pipeline(doc_type: str, description: str, session_id: str) -> None:
    """
    Execute the 4-agent pipeline sequentially, pushing SSE events at each step.

    Agents:
      1. IntakeAgent          -- extract structured case JSON
      2. LegalResearchAgent   -- RAG query over ChromaDB legal corpus
      3. DrafterAgent         -- bilingual document generation (plain text)
      4. VerifierAgent        -- completeness + quality check

    Results in a PDF saved to generated_pdfs/nyayamitra_{session_id}.pdf.
    All intermediate results are stored in session_store[session_id].

    Lazy imports inside the function body prevent startup errors if optional
    dependencies are not yet installed.
    """
    try:
        # ------------------------------------------------------------------
        # Agent 1: Intake -- extract structured case data from raw description
        # ------------------------------------------------------------------
        from agents.intake import run_intake
        intake_result = await run_intake(description, doc_type, session_id)

        # ------------------------------------------------------------------
        # Agent 2: Legal Research -- RAG over Indian legal corpus
        # ------------------------------------------------------------------
        from agents.research import run_research
        research_result = await run_research(intake_result, session_id)

        # ------------------------------------------------------------------
        # Agent 3: Drafter -- generate bilingual formal legal document
        # ------------------------------------------------------------------
        from agents.drafter import run_drafter
        draft = await run_drafter(intake_result, research_result, doc_type, session_id)

        # ------------------------------------------------------------------
        # Agent 4: Verifier -- quality and completeness check
        # ------------------------------------------------------------------
        from agents.verifier import run_verifier
        verification = await run_verifier(draft, intake_result, research_result, session_id)

        # ------------------------------------------------------------------
        # Generate PDF
        # ------------------------------------------------------------------
        from services.pdf_generator import generate_pdf
        pdf_path = await generate_pdf(draft, session_id)
        logger.info("PDF generated: %s", pdf_path)

        # ------------------------------------------------------------------
        # Agent 5: Filing Assistant -- generate portal + filing instructions
        # ------------------------------------------------------------------
        from agents.filing_assistant import run_filing_assistant
        filing = await run_filing_assistant(doc_type, intake_result, draft, session_id)

        # ------------------------------------------------------------------
        # Store results in session_store for later retrieval
        # ------------------------------------------------------------------
        session_store[session_id] = {
            "intake": intake_result,
            "sections": research_result,
            "draft": draft,
            "verification": verification,
            "pdf_path": str(pdf_path),
            "filing": filing,
        }

        # Push final completion event -- includes draft and verification so
        # the frontend can render results without a separate API call
        await push_event(
            session_id,
            "system",
            "complete",
            {
                "pdf_ready": True,
                "draft": draft,
                "verification": verification,
                "filing": filing,
            },
        )

    except Exception as exc:
        logger.exception("Pipeline failed for session %s", session_id)
        await push_event(session_id, "system", "error", {"error": str(exc)})

    finally:
        await close_stream(session_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/pipeline")
async def start_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):
    """
    Validate input and kick off the 4-agent pipeline as a background task.

    The client should immediately connect to GET /stream/{session_id} to
    receive real-time agent status events via SSE.
    """
    if req.doc_type not in VALID_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid doc_type '{req.doc_type}'. "
                f"Must be one of: {sorted(VALID_DOC_TYPES)}"
            ),
        )

    background_tasks.add_task(run_pipeline, req.doc_type, req.description, req.session_id)

    return {
        "status": "started",
        "session_id": req.session_id,
        "message": "Pipeline started. Connect to /stream/{session_id} for updates.",
    }


@app.get("/stream/{session_id}")
async def stream_events(session_id: str):
    """
    SSE endpoint -- streams agent status events for a pipeline run.

    The client connects here after POST /pipeline and receives events:
      data: {"agent": "intake",  "status": "running",   "data": {}}
      data: {"agent": "intake",  "status": "complete",  "data": {"summary": "..."}}
      data: {"agent": "system",  "status": "complete",  "data": {"pdf_ready": true}}
    """
    return EventSourceResponse(create_sse_generator(session_id))


@app.get("/download-pdf/{session_id}")
async def download_pdf(session_id: str):
    """Serve the generated PDF for a completed pipeline session."""
    pdf_path = PDF_OUTPUT_DIR / f"nyayamitra_{session_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF not found. The pipeline may still be running or may have failed.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"NyayaMitra_{session_id[:8]}.pdf",
    )


@app.get("/health")
async def health():
    """Liveness check. Returns agent count and number of laws indexed in ChromaDB."""
    try:
        from services.chroma_service import get_indexed_count
        laws_count = get_indexed_count()
    except Exception as exc:
        logger.warning("Health check: ChromaDB unavailable -- %s", exc)
        laws_count = 0

    return {
        "status": "ok",
        "agents": 4,
        "laws_indexed": laws_count,
        "doc_types": sorted(VALID_DOC_TYPES),
    }
