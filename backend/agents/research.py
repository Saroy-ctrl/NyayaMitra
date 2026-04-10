"""
research.py -- LegalResearchAgent: finds applicable law sections via RAG + Groq reranking.
"""

import json
import logging
from typing import Any

from services.chroma_service import query_laws
from services.groq_client import call_groq
from services.sse import push_event

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_DEFAULT = """You are an Indian law expert. Given a legal case and relevant law sections, select the most applicable sections and explain why each applies.

Return ONLY valid JSON array:
[
  {
    "section": "section number",
    "act": "full act name",
    "title": "section title or description",
    "reason": "one sentence why this section applies to the case"
  }
]

Rules:
- Include ONLY sections that directly and clearly apply to this specific case — if unsure, omit
- Quality over quantity: 1-2 accurate sections is better than 6 vague ones
- Hard maximum: 4 sections
- Prefer BNS 2023 over IPC 1860, BNSS 2023 over CrPC 1973
- Never cite IPC or CrPC sections -- always use BNS/BNSS/BSA equivalents
- Exception: Negotiable Instruments Act 1881 Section 138 (cheque bounce) is unchanged -- cite as-is
- Exception: Consumer Protection Act 2019 is unchanged -- cite as-is
- If a section identifier in the retrieved list looks like 'chunk_N' (a raw chunk ID, not a real section number), examine the text content to extract the actual section number. Look for patterns like 'Section N', 'N.' at the start, or 'Chapter N'. Output only real section numbers (e.g. '64', '138', '12'). NEVER output a chunk identifier as a section number.
- If you cannot identify a real section number from the text, skip that entry entirely.
- Return ONLY JSON array, no explanation
"""

_SYSTEM_PROMPT_FIR = """You are an Indian law expert. Given an FIR case and relevant law sections, select the most applicable substantive offence sections.

Return ONLY valid JSON array:
[
  {
    "section": "section number",
    "act": "full act name",
    "title": "section title or description",
    "reason": "one sentence why this section applies to the case"
  }
]

Rules:
- Include ONLY sections that directly and clearly apply to this specific crime — if unsure, omit
- Quality over quantity: 1-2 accurate sections is better than 6 vague ones
- Hard maximum: 4 sections
- For FIR documents: use ONLY Bharatiya Nyaya Sanhita (BNS) 2023 sections — BNSS (Bharatiya Nagarik Suraksha Sanhita) governs police procedure and must NOT be cited in an FIR for the offence
- Never cite IPC or CrPC sections — always use BNS equivalents
- If a section identifier in the retrieved list looks like 'chunk_N' (a raw chunk ID, not a real section number), examine the text content to extract the actual section number. Look for patterns like 'Section N', 'N.' at the start, or 'Chapter N'. Output only real section numbers (e.g. '64', '138', '12'). NEVER output a chunk identifier as a section number.
- If you cannot identify a real section number from the text, skip that entry entirely.
- Return ONLY JSON array, no explanation

CRITICAL SECTION ACCURACY RULES — apply these before selecting any section:
- BNS Section 304 (Snatching): ONLY cite if the theft involved sudden force or grabbing directly from a person's hands/body. Do NOT cite for unattended property theft (parked vehicle, empty shop, etc.).
- BNS Section 305 (Theft in dwelling house / means of transportation / place of worship): ONLY cite if theft occurred inside a home, inside a vehicle being used for travel, or inside a place of worship. A public parking lot is NOT a dwelling house or means of transportation.
- BNS Section 317 (Stolen property): This section criminalises RECEIVING or retaining stolen property. Do NOT cite this for the victim — it applies to the receiver/fence, not the complainant.
- BNS Section 303 (Theft): The correct base section for all simple theft cases including vehicle theft from a parking lot.
- BNS Section 309 (Robbery): Only cite if there was violence or threat of violence during the theft.
"""


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        raw = "\n".join(lines)
    return raw.strip()


async def run_research(incident_json: dict[str, Any], session_id: str, doc_type: str = "") -> list[dict]:
    """
    Retrieve and rank applicable Indian law sections for the case.

    Args:
        incident_json: Output from IntakeAgent.
        session_id:    SSE session identifier.
        doc_type:      Document type — used to apply FIR-specific constraints.

    Returns:
        List of section dicts: [{section, act, title, reason}, ...]
    """
    await push_event(session_id, "research", "running", {"message": "Searching legal corpus..."})

    # Resolve doc_type from incident_json if not explicitly passed
    if not doc_type:
        doc_type = incident_json.get("doc_type_confirmed", "")

    is_fir = doc_type == "fir"
    system_prompt = _SYSTEM_PROMPT_FIR if is_fir else _SYSTEM_PROMPT_DEFAULT

    try:
        # Build query components from incident_json
        incident_type = incident_json.get("incident_type", "")
        key_claims = incident_json.get("key_claims", [])
        sequence = incident_json.get("sequence_of_events", [])
        description_parts = list(key_claims) + list(sequence)
        description = " ".join(str(p) for p in description_parts)

        # For FIR: filter ChromaDB to BNS 2023 sections only (substantive offence law)
        act_filter = {"act": "Bharatiya Nyaya Sanhita 2023"} if is_fir else None

        # Query ChromaDB
        chunks = await query_laws(incident_type, description, top_k=10, where=act_filter)

        if not chunks:
            logger.warning("No ChromaDB results for session %s", session_id[:8])
            await push_event(
                session_id,
                "research",
                "complete",
                {"summary": "No matching law sections found", "section_count": 0, "acts": []},
            )
            return []

        # Format sections for Groq prompt
        formatted_lines = []
        for i, chunk in enumerate(chunks, start=1):
            act = chunk.get("act", "")
            section = chunk.get("section_number", "")
            title = chunk.get("title", "")
            text = chunk.get("text", "")[:300]
            if str(section).startswith("chunk_"):
                formatted_lines.append(f"[{i}] {act} (section unknown): {title} -- {text}")
            else:
                formatted_lines.append(f"[{i}] {act} Section {section}: {title} -- {text}")
        formatted_sections = "\n".join(formatted_lines)

        user_message = (
            f"Case details:\n{json.dumps(incident_json, ensure_ascii=False, indent=2)}\n\n"
            f"Retrieved law sections:\n{formatted_sections}\n\n"
            f"Select the most applicable sections."
        )

        raw = await call_groq(system_prompt, user_message, max_tokens=600)
        cleaned = _strip_code_fences(raw)
        sections: list[dict] = json.loads(cleaned)

        # Ensure it's a list
        if isinstance(sections, dict):
            sections = [sections]

        # Strip any chunk_ identifiers that Groq failed to resolve
        sections = [s for s in sections if not str(s.get("section", "")).startswith("chunk_")]

        unique_acts = list({s.get("act", "") for s in sections if s.get("act")})

        await push_event(
            session_id,
            "research",
            "complete",
            {
                "summary": f"Found {len(sections)} applicable section(s)",
                "section_count": len(sections),
                "acts": unique_acts,
            },
        )
        return sections

    except json.JSONDecodeError as exc:
        logger.warning("ResearchAgent JSON parse failed: %s", exc)
        await push_event(
            session_id,
            "research",
            "complete",
            {"summary": "Research complete (parse fallback)", "section_count": 0, "acts": []},
        )
        return []

    except Exception as exc:
        await push_event(session_id, "research", "error", {"error": str(exc)})
        raise
