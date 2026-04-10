"""
agents/drafter.py -- DrafterAgent: generates the full bilingual legal document.
"""

import json
import logging
from typing import Any

from services.groq_client import call_groq
from services.sse import push_event

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Doc-type labels
# ---------------------------------------------------------------------------
_DOC_TYPE_LABELS: dict[str, str] = {
    "fir": "First Information Report (FIR)",
    "legal_notice": "Legal Notice",
    "consumer_complaint": "Consumer Complaint",
    "cheque_bounce": "Cheque Dishonour Legal Notice (Section 138 NI Act)",
    "tenant_eviction": "Tenant Eviction Notice",
}

# ---------------------------------------------------------------------------
# Doc-type specific formatting instructions appended to the user message
# ---------------------------------------------------------------------------
_DOC_TYPE_INSTRUCTIONS: dict[str, str] = {
    "fir": """Format as First Information Report with:
- Police Station, District, State (use location from case)
- Date of complaint (use today's date); Time of complaint (use the current time — do NOT leave as placeholder)
- Complainant details: Name, Address (ask user if not provided), Contact Number (use parties[].contact if available, else write [Complainant's Contact Number])
- Accused details: Name (Unknown if not identified), physical description if mentioned (approximate age, height, build, clothing colour, any distinguishing features), last seen direction if mentioned
- Incident description: exact date, exact time (use incident_time if provided, else [Time of the incident]), exact location, detailed narrative of what happened
- If the incident involves theft, robbery, or snatching: include a numbered "List of Stolen/Missing Items" section listing items the complainant reported stolen. For each item include: description, approximate value if mentioned, any identifying details (IMEI, serial number etc.). If specific items not stated, use placeholders: [Cash amount], [Mobile phone - brand/model/IMEI], [Identity documents - Aadhaar, PAN etc.], [Bank cards], [Other valuables]
- If incident involves physical assault: include "Nature of Injuries" section
- Sections of law invoked (use BNS/BNSS sections provided -- cite as real section numbers only)
- Request for investigation: specifically mention any available evidence e.g. CCTV cameras at the location, eyewitnesses, digital evidence
- Relief sought: register FIR and investigate
- Declaration by complainant
- Signature block: Name, Contact Number, Date
- Do not include any Hindi text or subtitles
- For any information not provided by the user, use [bracketed placeholder] text so complainant can fill it in -- do NOT fabricate details or skip sections entirely""",

    "legal_notice": """Format as Legal Notice with:
- From: [Complainant name, address]
- To: [Respondent name, address]
- Date
- Subject (in English only)
- Opening: "LEGAL NOTICE"
- Facts in numbered paragraphs
- Legal basis: cite only the provided sections that directly apply
- Demand/Relief with specific deadline (15 days)
- Consequence of non-compliance
- Closing with advocate's signature block
- No Hindi text anywhere""",

    "consumer_complaint": """Format as Consumer Complaint to District Consumer Disputes Redressal Commission with:
- Forum name and address
- Complainant details
- Opposite Party (OP) details
- Jurisdiction (Consumer Protection Act 2019)
- Brief facts (numbered)
- Cause of action
- Legal provisions (Consumer Protection Act sections)
- Relief claimed (compensation amount, replacement, refund)
- Prayer/Conclusion
- Declaration
- No Hindi text anywhere""",

    "cheque_bounce": """Format as Cheque Bounce Legal Notice under NI Act Section 138 with:
- From: [Payee/Complainant]
- To: [Drawer/Accused]
- Date
- Subject: Legal Notice under Section 138 NI Act
- Cheque details (number, date, bank, amount)
- Date of dishonour
- Date of receipt of memo of dishonour
- Demand: pay within 15 days of receipt
- Warning: criminal complaint u/s 138 NI Act if unpaid
- No Hindi text anywhere""",

    "tenant_eviction": """Format as Tenant Eviction Notice with:
- From: [Landlord/Lessor]
- To: [Tenant/Lessee]
- Date
- Subject: Notice to Vacate
- Property description (address, type)
- Grounds for eviction (cite Transfer of Property Act / Delhi Rent Control Act sections)
- Facts supporting grounds
- Demand: vacate within 30 days (or as per applicable notice period)
- Warning: legal proceedings if not vacated
- No Hindi text anywhere""",
}

_SYSTEM_PROMPT_TEMPLATE = """You are an expert Indian legal document drafter. Generate a formal, complete legal document entirely in English. No Hindi text anywhere in the document.

Document type: {doc_type_label}
Legal sections to cite: {formatted_sections}

Rules:
- English only — do NOT include any Hindi text, Devanagari script, or bilingual phrases anywhere in the document
- Use formal legal language
- Cite BNS/BNSS sections (NOT IPC/CrPC)
- Include all required sections for this document type
- Use Indian legal document conventions
- Never fabricate section numbers — only cite sections from the provided list
- Only cite a section if it genuinely and directly applies to this specific case — if a section does not clearly fit, omit it entirely. Fewer accurate sections is better than more inaccurate ones
- Use the exact incident_time from case details if provided — never invent a time
- Use the complainant's contact info from parties[].contact if available
- Return the document as plain text (not JSON), ready to be printed
- When citing legal sections, use ONLY this format: "Section X BNS 2023: [Section Title]" — no explanation, rationale, or commentary after the title
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


def _format_sections(legal_sections: list[dict]) -> str:
    """Format list of section dicts into a readable string for the prompt."""
    if not legal_sections:
        return "No specific sections retrieved -- use general applicable law."
    lines = []
    for s in legal_sections:
        act = s.get("act", "")
        section = s.get("section", "")
        title = s.get("title", "")
        lines.append(f"- Section {section} {act}: {title}")
    return "\n".join(lines)


async def run_drafter(
    incident_json: dict[str, Any],
    legal_sections: list[dict],
    doc_type: str,
    session_id: str,
) -> str:
    """
    Generate the bilingual formal legal document as plain text.

    Args:
        incident_json:  Output from IntakeAgent.
        legal_sections: Output from LegalResearchAgent (list of section dicts).
        doc_type:       One of fir | legal_notice | consumer_complaint |
                        cheque_bounce | tenant_eviction.
        session_id:     SSE session identifier.

    Returns:
        Draft document as a plain text string.
    """
    await push_event(session_id, "drafter", "running", {"message": "Drafting legal document..."})

    try:
        doc_type_label = _DOC_TYPE_LABELS.get(doc_type, doc_type.replace("_", " ").title())
        formatted_sections = _format_sections(legal_sections)

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            doc_type_label=doc_type_label,
            formatted_sections=formatted_sections,
        )

        doc_instructions = _DOC_TYPE_INSTRUCTIONS.get(doc_type, "")

        from datetime import datetime
        now = datetime.now()
        current_date = f"{now.day} {now.strftime('%B %Y')}"
        current_time = now.strftime("%I:%M %p")

        user_message = (
            f"Today's date: {current_date}\n"
            f"Current time (time of complaint): {current_time}\n\n"
            f"Case details:\n{json.dumps(incident_json, ensure_ascii=False, indent=2)}\n\n"
            f"Document formatting requirements:\n{doc_instructions}\n\n"
            f"Generate the complete {doc_type} document now."
        )

        from services.groq_client import MODEL_LARGE
        raw = await call_groq(system_prompt, user_message, max_tokens=3000, model=MODEL_LARGE)
        draft = _strip_code_fences(raw)

        await push_event(
            session_id,
            "drafter",
            "complete",
            {"doc_type": doc_type, "char_count": len(draft)},
        )
        return draft

    except Exception as exc:
        await push_event(session_id, "drafter", "error", {"error": str(exc)})
        raise
