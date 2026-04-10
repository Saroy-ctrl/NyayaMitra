"""
agents/filing_assistant.py -- FilingAssistantAgent: guides user to file the generated document.

Given doc_type, structured case JSON, and generated document text, returns:
  - portal_name / portal_url
  - step_by_step_instructions (bilingual EN + HI)
  - required_fields_mapping (form fields -> extracted values)
  - warnings (missing info, offline requirements)
"""

import json
import logging
import re
from typing import Any

from services.groq_client import call_groq
from services.sse import push_event

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State -> e-FIR portal map
# Only states with confirmed working e-FIR portals listed.
# ---------------------------------------------------------------------------
_STATE_EFIR_PORTALS: dict[str, dict] = {
    "delhi": {
        "name": "Delhi Police e-FIR Portal",
        "url": "https://efir.delhipolice.gov.in/",
        "note": "Available for theft, snatching, vehicle theft, lost documents",
    },
    "maharashtra": {
        "name": "Maharashtra Police Citizen Portal",
        "url": "https://citizen.mahapolice.gov.in/",
        "note": "Available for theft and vehicle theft cases",
    },
    "uttar pradesh": {
        "name": "UP Police Online Complaint Portal",
        "url": "https://uppolice.gov.in/",
        "note": "Available for theft and lost property",
    },
    "karnataka": {
        "name": "Karnataka State Police Portal",
        "url": "https://ksp.karnataka.gov.in/",
        "note": "Available for theft and cybercrime",
    },
    "rajasthan": {
        "name": "Rajasthan Police Citizen Portal",
        "url": "https://police.rajasthan.gov.in/",
        "note": "Available for theft and vehicle theft",
    },
    "tamil nadu": {
        "name": "Tamil Nadu Police Online Complaint",
        "url": "https://www.tnpolice.gov.in/",
        "note": "Available for theft and vehicle theft",
    },
    "telangana": {
        "name": "Telangana Police Online Complaint",
        "url": "https://tspolice.gov.in/",
        "note": "Available for theft and cybercrime",
    },
    "andhra pradesh": {
        "name": "AP Police Online Complaint",
        "url": "https://appolice.gov.in/",
        "note": "Available for theft",
    },
    "gujarat": {
        "name": "Gujarat Police Citizen Portal",
        "url": "https://gujaratpolice.gov.in/",
        "note": "Available for theft and vehicle theft",
    },
    "haryana": {
        "name": "Haryana Police Online Portal",
        "url": "https://haryanapoliceonline.gov.in/",
        "note": "Available for theft and lost documents",
    },
}

# Crime types that are NOT eligible for e-FIR (need in-person filing)
_VIOLENT_KEYWORDS = [
    "assault", "attack", "hit", "beat", "hurt", "injury", "injuries",
    "rape", "sexual", "murder", "abduct", "kidnap", "robbery", "dacoity",
    "domestic violence", "mob", "riot"
]

# Crime types that typically qualify for e-FIR
_EFIR_KEYWORDS = [
    "theft", "stolen", "snatching", "missing", "lost", "vehicle theft",
    "bike theft", "mobile theft", "phone theft", "cybercrime", "online fraud"
]

_CONSUMER_PORTAL = {
    "name": "e-Daakhil — NCDRC Consumer Complaint Portal",
    "url": "https://edaakhil.nic.in/",
    "note": "Official online portal for filing consumer complaints with District/State/National Commissions",
}

# Fixed documents required for every consumer complaint on e-Daakhil
_CONSUMER_REQUIRED_DOCS = [
    "Purchase receipt / invoice / bill",
    "Proof of payment (bank statement, UPI screenshot, or credit card slip)",
    "Any warranty or guarantee card (if applicable)",
    "Copies of emails, letters, or messages sent to the company",
    "Company's reply or proof that they did not respond (for cause of action)",
    "Identity proof — Aadhaar card or PAN card",
    "Address proof — Aadhaar / utility bill",
    "Passport-size photograph of complainant",
]

# e-Daakhil exact form field names -> how to extract from incident_json
_EDAAKHIL_FIELDS = [
    ("Complainant Name",           lambda j, c, r: c.get("name", "[FILL IN]"),          "Your full name as per Aadhaar"),
    ("Complainant Mobile Number",  lambda j, c, r: c.get("contact", "[FILL IN]"),        "Active mobile number for OTP"),
    ("Complainant Address",        lambda j, c, r: j.get("location", "[FILL IN]"),       "Full postal address with PIN code"),
    ("Opposite Party (OP) Name",   lambda j, c, r: r.get("name", "[FILL IN]"),           "Company / seller / service provider name"),
    ("Opposite Party Address",     lambda j, c, r: r.get("contact", "[FILL IN]"),        "Registered office address of OP"),
    ("Nature of Complaint",        lambda j, c, r: j.get("incident_type", "[FILL IN]"),  "Defective product / deficient service / unfair trade practice"),
    ("Date of Transaction",        lambda j, c, r: j.get("dates", ["[FILL IN]"])[0] if j.get("dates") else "[FILL IN]", "Date of purchase or service availed"),
    ("Relief/Compensation Sought", lambda j, c, r: "; ".join(j.get("key_claims", ["[FILL IN]"]))[:120], "Amount or remedy you want from OP"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_state(location: str) -> str:
    """Extract state name from location string (lowercase)."""
    loc = location.lower()
    state_keywords = {
        "delhi": "delhi",
        "new delhi": "delhi",
        "janakpuri": "delhi",
        "dwarka": "delhi",
        "rohini": "delhi",
        "mumbai": "maharashtra",
        "pune": "maharashtra",
        "nagpur": "maharashtra",
        "lucknow": "uttar pradesh",
        "noida": "uttar pradesh",
        "agra": "uttar pradesh",
        "kanpur": "uttar pradesh",
        "bangalore": "karnataka",
        "bengaluru": "karnataka",
        "mysore": "karnataka",
        "jaipur": "rajasthan",
        "jodhpur": "rajasthan",
        "udaipur": "rajasthan",
        "chennai": "tamil nadu",
        "coimbatore": "tamil nadu",
        "hyderabad": "telangana",
        "warangal": "telangana",
        "vijayawada": "andhra pradesh",
        "visakhapatnam": "andhra pradesh",
        "ahmedabad": "gujarat",
        "surat": "gujarat",
        "vadodara": "gujarat",
        "gurugram": "haryana",
        "gurgaon": "haryana",
        "faridabad": "haryana",
    }
    for keyword, state in state_keywords.items():
        if keyword in loc:
            return state
    # Try direct state name match
    for state in _STATE_EFIR_PORTALS:
        if state in loc:
            return state
    return ""


def _is_violent_incident(incident_type: str, key_claims: list) -> bool:
    """Returns True if incident involves violence -- disqualifies e-FIR."""
    text = (incident_type + " " + " ".join(str(c) for c in key_claims)).lower()
    return any(kw in text for kw in _VIOLENT_KEYWORDS)


def _is_efir_eligible_crime(incident_type: str, key_claims: list) -> bool:
    """Returns True if the crime type can use e-FIR."""
    text = (incident_type + " " + " ".join(str(c) for c in key_claims)).lower()
    return any(kw in text for kw in _EFIR_KEYWORDS)


def _extract_party(parties: list, role: str) -> dict:
    for p in parties:
        if p.get("role") == role:
            return p
    return parties[0] if parties else {}


# ---------------------------------------------------------------------------
# Groq prompts
# ---------------------------------------------------------------------------

_CONSUMER_SYSTEM_PROMPT = """You are a helpful guide for filing consumer complaints on India's e-Daakhil portal (edaakhil.nic.in).

Return ONLY valid JSON with exactly this structure:
{
  "steps": [
    {"en": "Step instruction in simple English", "hi": "Same step in simple Hindi"}
  ],
  "warnings": ["Warning message in English"]
}

Rules:
- Steps must be beginner-friendly, no legal jargon
- Reference exact e-Daakhil portal sections where relevant (e.g. "Click on 'File Complaint' > 'New Complaint'")
- Hindi should be conversational
- Include a step about uploading supporting documents
- Include a step about paying the filing fee (if applicable — free for claims under Rs 5 lakh)
- Minimum 6 steps, maximum 10
- Return ONLY JSON, no explanation
"""

_SYSTEM_PROMPT = """You are a helpful legal filing guide for Indian citizens. Your job is to generate simple, beginner-friendly filing instructions.

Return ONLY valid JSON with exactly this structure:
{
  "steps": [
    {"en": "Step instruction in simple English", "hi": "Same step in simple Hindi"}
  ],
  "fields_mapping": [
    {"field": "Exact form field name", "value": "Extracted value or [FILL IN]", "hint": "Where to find this"}
  ],
  "warnings": ["Warning message in English"]
}

Rules:
- Steps must be numbered in content, simple English, no legal jargon
- Hindi translation should be conversational, not formal
- fields_mapping must use EXACT field names a user would see on the portal/form
- warnings must flag any missing information the user needs to provide
- Maximum 10 steps, minimum 4
- Return ONLY JSON, no explanation
"""


def _strip_code_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        raw = "\n".join(lines)
    return raw.strip()


# ---------------------------------------------------------------------------
# Consumer complaint handler
# ---------------------------------------------------------------------------

async def _handle_consumer_complaint(incident_json: dict, draft: str) -> dict[str, Any]:
    """
    Build e-Daakhil filing guidance for consumer_complaint doc type.
    Returns a result dict matching the standard output structure.
    """
    parties = incident_json.get("parties", [])
    complainant = _extract_party(parties, "complainant")
    respondent = _extract_party(parties, "respondent")

    # Build prefill_data / fields_mapping from case JSON
    fields_mapping = []
    for field_name, extractor, hint in _EDAAKHIL_FIELDS:
        try:
            value = extractor(incident_json, complainant, respondent)
        except Exception:
            value = "[FILL IN]"
        fields_mapping.append({"field": field_name, "value": str(value) if value else "[FILL IN]", "hint": hint})

    # Groq: generate bilingual steps + warnings
    context = {
        "portal": "e-Daakhil (edaakhil.nic.in)",
        "complainant_name": complainant.get("name", "[Name]"),
        "opposite_party": respondent.get("name", "[Company/Seller]"),
        "incident_type": incident_json.get("incident_type", ""),
        "key_claims": incident_json.get("key_claims", []),
        "location": incident_json.get("location", ""),
    }
    user_message = (
        f"Case context:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        f"Document summary:\n{draft[:500]}\n\n"
        f"Generate e-Daakhil filing steps for this consumer complaint."
    )
    raw = await call_groq(_CONSUMER_SYSTEM_PROMPT, user_message, max_tokens=900)
    parsed = json.loads(_strip_code_fences(raw))

    return {
        "portal_name": _CONSUMER_PORTAL["name"],
        "portal_url": _CONSUMER_PORTAL["url"],
        "filing_mode": "online",
        "portal_note": _CONSUMER_PORTAL["note"],
        "steps": parsed.get("steps", []),
        "fields_mapping": fields_mapping,
        "required_documents": _CONSUMER_REQUIRED_DOCS,
        "warnings": parsed.get("warnings", []),
    }


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

async def run_filing_assistant(
    doc_type: str,
    incident_json: dict[str, Any],
    draft: str,
    session_id: str,
) -> dict[str, Any]:
    """
    Determine the correct filing portal and generate step-by-step instructions.

    Returns a dict with:
      portal_name, portal_url, filing_mode ("online" | "offline" | "post"),
      steps, fields_mapping, warnings
    """
    await push_event(session_id, "filing_assistant", "running", {"message": "Preparing filing instructions..."})

    try:
        parties = incident_json.get("parties", [])
        location = incident_json.get("location", "")
        incident_type = incident_json.get("incident_type", "")
        key_claims = incident_json.get("key_claims", [])
        dates = incident_json.get("dates", [])
        incident_time = incident_json.get("incident_time")
        complainant = _extract_party(parties, "complainant")

        # ------------------------------------------------------------------
        # Determine portal and filing mode
        # ------------------------------------------------------------------
        portal_name = ""
        portal_url = ""
        filing_mode = "offline"
        portal_note = ""

        if doc_type == "fir":
            state = _detect_state(location)
            is_violent = _is_violent_incident(incident_type, key_claims)
            is_efir_crime = _is_efir_eligible_crime(incident_type, key_claims)

            if not is_violent and is_efir_crime and state in _STATE_EFIR_PORTALS:
                portal = _STATE_EFIR_PORTALS[state]
                portal_name = portal["name"]
                portal_url = portal["url"]
                portal_note = portal["note"]
                filing_mode = "online"
            else:
                portal_name = "Nearest Police Station (In-Person Filing)"
                portal_url = ""
                filing_mode = "offline"
                if is_violent:
                    portal_note = "This incident involves violence or a serious offence -- e-FIR is not available. You must file in person at the police station."

        elif doc_type == "consumer_complaint":
            result = await _handle_consumer_complaint(incident_json, draft)
            await push_event(session_id, "filing_assistant", "complete", {"filing": result})
            return result

        elif doc_type in ("legal_notice", "cheque_bounce", "tenant_eviction"):
            portal_name = "Speed Post + Email (No online portal required)"
            portal_url = ""
            filing_mode = "post"
            portal_note = "Legal notices must be sent via Registered Post / Speed Post for legal validity."

        # ------------------------------------------------------------------
        # Build context for Groq
        # ------------------------------------------------------------------
        context = {
            "doc_type": doc_type,
            "filing_mode": filing_mode,
            "portal_name": portal_name,
            "portal_url": portal_url,
            "portal_note": portal_note,
            "complainant_name": complainant.get("name", "[Name]"),
            "complainant_contact": complainant.get("contact", ""),
            "location": location,
            "incident_type": incident_type,
            "key_claims": key_claims,
            "dates": dates,
            "incident_time": incident_time,
        }

        # Respondent for legal notice / consumer complaint
        respondent = _extract_party(parties, "respondent")
        if respondent:
            context["respondent_name"] = respondent.get("name", "")
            context["respondent_contact"] = respondent.get("contact", "")

        user_message = (
            f"Filing context:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            f"Case summary from document:\n{draft[:600]}\n\n"
            f"Generate filing instructions for this specific case."
        )

        raw = await call_groq(_SYSTEM_PROMPT, user_message, max_tokens=900)
        parsed = json.loads(_strip_code_fences(raw))

        steps = parsed.get("steps", [])
        fields_mapping = parsed.get("fields_mapping", [])
        warnings = parsed.get("warnings", [])

        result = {
            "portal_name": portal_name,
            "portal_url": portal_url,
            "filing_mode": filing_mode,
            "portal_note": portal_note,
            "steps": steps,
            "fields_mapping": fields_mapping,
            "warnings": warnings,
        }

        await push_event(
            session_id,
            "filing_assistant",
            "complete",
            {"filing": result},
        )
        return result

    except Exception as exc:
        logger.warning("FilingAssistantAgent failed: %s", exc)
        fallback = {
            "portal_name": "Please consult the relevant authority",
            "portal_url": "",
            "filing_mode": "offline",
            "portal_note": "",
            "steps": [],
            "fields_mapping": [],
            "warnings": [str(exc)],
        }
        await push_event(session_id, "filing_assistant", "complete", {"filing": fallback})
        return fallback
