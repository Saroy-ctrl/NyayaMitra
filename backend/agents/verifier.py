"""
agents/verifier.py -- VerifierAgent: quality checks the generated document.
"""

import json
import logging
from typing import Any

from services.groq_client import call_groq
from services.sse import push_event

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an Indian legal document quality checker. Review the draft document and provide a detailed quality assessment.

Return ONLY valid JSON:
{
  "score": 7,
  "is_complete": true,
  "overall_quality": "good",
  "issues": [
    {
      "field": "field name or section",
      "severity": "high|medium|low",
      "suggestion": "specific suggestion to fix"
    }
  ],
  "missing_fields": ["list of required fields that are absent"],
  "recommendations": ["list of actionable improvements"],
  "law_accuracy": "correct|needs_review|incorrect",
  "language_quality": "formal|acceptable|informal"
}

Check for:
1. All required fields present (parties, dates, location, legal basis, relief)
2. For FIR specifically: complainant's residential address AND time of complaint are MANDATORY — flag as "high" severity if either is a placeholder like "[Complainant's Address]" or "[Time of complaint]"
3. Legal sections cited correctly (BNS not IPC, BNSS not CrPC)
4. Relief/remedy clearly stated
5. Formal legal language used
6. No fabricated section numbers
7. Bilingual elements where appropriate
8. Document structure follows Indian legal conventions
9. Section semantic accuracy: BNS 304 (Snatching) only if force from person's body; BNS 305 only if inside dwelling/vehicle/place of worship; BNS 317 (Stolen property) must NOT be cited for the victim — it applies to receivers of stolen goods

Reality-Check Rules (apply these after the standard checks above):
- Rule A (Location vs Section Mismatch): If the crime location stated in the case facts is a public place (market, plaza, road, mall, office, shop, bus stand, railway station, street, parking lot), and the draft cites any section related to "dwelling house", "house trespass", or "criminal trespass into a building" — flag it as an issue with severity "high", field "legal_sections", suggestion "The cited section applies to dwelling/house trespass but the crime occurred in a public space — replace with the correct open-area offence section."
- Rule B (Organised Crime Evidence Gate): If the only evidence linking the accused is a clothing/appearance description (e.g. "black hoodie", "red jacket man", "unknown male in blue shirt") with no other identifying information, and the draft cites any section related to organised crime, gang activity, or petty organised crime (e.g. BNS Section 112 Petty Organised Crime) — flag it as an issue with severity "high", field "legal_sections", suggestion "Insufficient evidence for organised crime citation — a clothing description alone does not establish gang membership or organised criminal activity. Remove this section."

overall_quality: "good" (score 8-10), "acceptable" (5-7), "poor" (1-4)
Return ONLY JSON, no explanation.
"""

_DEFAULT_RESULT: dict[str, Any] = {
    "score": 6,
    "is_complete": True,
    "overall_quality": "acceptable",
    "issues": [],
    "missing_fields": [],
    "recommendations": ["Manual review recommended"],
    "law_accuracy": "needs_review",
    "language_quality": "acceptable",
}


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


async def run_verifier(
    draft: str,
    incident_json: dict[str, Any],
    legal_sections: list[dict],
    session_id: str,
) -> dict[str, Any]:
    """
    Verify the drafted document for completeness and quality.

    Args:
        draft:          Plain text document output from DrafterAgent.
        incident_json:  Output from IntakeAgent.
        legal_sections: Output from LegalResearchAgent.
        session_id:     SSE session identifier.

    Returns:
        Verification report dict with score, issues, recommendations.
    """
    await push_event(session_id, "verifier", "running", {"message": "Verifying document quality..."})

    try:
        doc_type = incident_json.get("doc_type_confirmed", "unknown")

        user_message = (
            f"Document type: {doc_type}\n\n"
            f"Draft document:\n{draft[:3000]}\n\n"
            f"Case facts for cross-check:\n{json.dumps(incident_json, ensure_ascii=False, indent=2)[:1000]}\n\n"
            f"Legal sections that should be cited:\n{json.dumps(legal_sections, ensure_ascii=False)[:500]}"
        )

        from services.groq_client import MODEL_LARGE
        raw = await call_groq(_SYSTEM_PROMPT, user_message, max_tokens=700, model=MODEL_LARGE)
        cleaned = _strip_code_fences(raw)
        result: dict[str, Any] = json.loads(cleaned)

        await push_event(
            session_id,
            "verifier",
            "complete",
            {
                "score": result.get("score", 0),
                "is_complete": result.get("is_complete", False),
                "issue_count": len(result.get("issues", [])),
            },
        )
        return result

    except json.JSONDecodeError as exc:
        logger.warning("VerifierAgent JSON parse failed: %s -- returning default result", exc)
        await push_event(
            session_id,
            "verifier",
            "complete",
            {
                "score": _DEFAULT_RESULT["score"],
                "is_complete": _DEFAULT_RESULT["is_complete"],
                "issue_count": 0,
            },
        )
        return _DEFAULT_RESULT.copy()

    except Exception as exc:
        await push_event(session_id, "verifier", "error", {"error": str(exc)})
        raise
