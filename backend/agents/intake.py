"""
agents/intake.py -- IntakeAgent: extracts structured case JSON from user description.
"""

import json
import logging
from typing import Any

from services.groq_client import call_groq
from services.sse import push_event

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """You are a legal intake specialist for Indian law. Extract structured case details from the user's description (which may be in Hindi, Hinglish, or English).

Return ONLY valid JSON with exactly these fields:
{{
  "incident_type": "brief type e.g. cheque_bounce / theft / consumer_dispute / tenant_eviction / legal_notice",
  "parties": [{{"name": "...", "role": "complainant|accused|witness|respondent", "contact": "phone/email/address if mentioned or null"}}],
  "dates": ["list of relevant dates mentioned"],
  "incident_time": "time of incident if mentioned e.g. '22:00', '10:30 PM', or null",
  "location": "place where incident occurred",
  "sequence_of_events": ["ordered list of what happened"],
  "language_preference": "hindi|english|bilingual",
  "urgency": "high|medium|low",
  "key_claims": ["main legal claims or grievances"],
  "doc_type_confirmed": "fir|legal_notice|consumer_complaint|cheque_bounce|tenant_eviction",
  "summary": "one sentence summary of the case in English"
}}

Rules:
- doc_type_confirmed must match the requested doc_type: {doc_type}
- If parties are unnamed, use "Complainant" and "Respondent"
- Return ONLY JSON, no explanation
"""


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences (```json ... ```) if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        # Drop the first line (```json or ```) and the last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        raw = "\n".join(lines)
    return raw.strip()


async def run_intake(description: str, doc_type: str, session_id: str) -> dict[str, Any]:
    """
    Extract structured case data from a free-text description.

    Args:
        description: Raw user input (Hindi/English/Hinglish).
        doc_type:    One of fir | legal_notice | consumer_complaint |
                     cheque_bounce | tenant_eviction.
        session_id:  Used to push SSE status events.

    Returns:
        Parsed case dict with structured fields.
    """
    await push_event(session_id, "intake", "running", {"message": "Extracting case details..."})

    try:
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(doc_type=doc_type)
        user_message = f"Document type requested: {doc_type}\n\nUser description:\n{description}"

        from services.groq_client import MODEL_LARGE
        raw = await call_groq(system_prompt, user_message, max_tokens=700, model=MODEL_LARGE)
        cleaned = _strip_code_fences(raw)
        result: dict[str, Any] = json.loads(cleaned)

        await push_event(
            session_id,
            "intake",
            "complete",
            {"summary": result.get("summary", "Case details extracted")},
        )
        return result

    except json.JSONDecodeError as exc:
        logger.warning("IntakeAgent JSON parse failed: %s — returning fallback dict", exc)
        fallback: dict[str, Any] = {
            "incident_type": doc_type,
            "parties": [{"name": "Complainant", "role": "complainant", "contact": None}, {"name": "Respondent", "role": "respondent", "contact": None}],
            "dates": [],
            "incident_time": None,
            "location": "Unknown",
            "sequence_of_events": [description],
            "language_preference": "bilingual",
            "urgency": "medium",
            "key_claims": [description],
            "doc_type_confirmed": doc_type,
            "summary": description[:200],
        }
        await push_event(
            session_id,
            "intake",
            "complete",
            {"summary": "Case details extracted (fallback mode)"},
        )
        return fallback

    except Exception as exc:
        await push_event(session_id, "intake", "error", {"error": str(exc)})
        raise
