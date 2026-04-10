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

_SYSTEM_PROMPT = """You are an Indian law expert. Given a legal case and relevant law sections, select the most applicable sections and explain why each applies.

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
- Include only sections that genuinely apply
- Maximum 6 sections
- Prefer BNS 2023 over IPC 1860, BNSS 2023 over CrPC 1973
- Never cite IPC or CrPC sections -- always use BNS/BNSS/BSA equivalents
- Exception: Negotiable Instruments Act 1881 Section 138 (cheque bounce) is unchanged -- cite as-is
- Exception: Consumer Protection Act 2019 is unchanged -- cite as-is
- If a section identifier in the retrieved list looks like 'chunk_N' (a raw chunk ID, not a real section number), examine the text content to extract the actual section number. Look for patterns like 'Section N', 'N.' at the start, or 'Chapter N'. Output only real section numbers (e.g. '64', '138', '12'). NEVER output a chunk identifier as a section number.
- If you cannot identify a real section number from the text, skip that entry entirely.
- Return ONLY JSON array, no explanation
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


async def run_research(incident_json: dict[str, Any], session_id: str) -> list[dict]:
    """
    Retrieve and rank applicable Indian law sections for the case.

    Args:
        incident_json: Output from IntakeAgent.
        session_id:    SSE session identifier.

    Returns:
        List of section dicts: [{section, act, title, reason}, ...]
    """
    await push_event(session_id, "research", "running", {"message": "Searching legal corpus..."})

    try:
        # Build query components from incident_json
        incident_type = incident_json.get("incident_type", "")
        key_claims = incident_json.get("key_claims", [])
        sequence = incident_json.get("sequence_of_events", [])
        description_parts = list(key_claims) + list(sequence)
        description = " ".join(str(p) for p in description_parts)

        # Query ChromaDB
        chunks = await query_laws(incident_type, description, top_k=10)

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

        raw = await call_groq(_SYSTEM_PROMPT, user_message, max_tokens=600)
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
