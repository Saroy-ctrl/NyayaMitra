"""
agents/intake.py -- IntakeAgent: extracts structured case JSON from user description.
Also provides ConversationalIntakeAgent for multi-turn chat-based intake.
"""

import json
import logging
from typing import Any

from services.groq_client import call_groq, MODEL_LARGE
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
  "summary": "one sentence summary of the case in English",
  "clarification_needed": "a specific question to ask the user, or null if no clarification needed"
}}

Rules:
- doc_type_confirmed must match the requested doc_type: {doc_type}
- If parties are unnamed, use "Complainant" and "Respondent"
- Return ONLY JSON, no explanation

Anomaly Detection — run these checks AFTER extracting all fields:
- If the incident involves theft/robbery/snatching AND the location is a public commercial space (mall, plaza, market, shop, road, street, bus stand, railway station, parking lot): cross-check the stolen items list. If any item is large or implausible to carry in a public space (e.g. television, TV, refrigerator, fridge, sofa, furniture, washing machine, air conditioner, AC), set clarification_needed to a specific question asking the user to confirm whether the item was stolen from inside their home/vehicle or from the public location. Example: "You mentioned a [item] was stolen at a [location]. Could you clarify — was this item taken from your vehicle/home nearby, or directly from the public space?" — adapt the wording to the actual item and location.
- In all other cases, set clarification_needed to null.
"""


def _extract_json(raw: str) -> str:
    """
    Robustly extract the first complete JSON object from raw LLM output.
    Handles markdown fences, leading/trailing prose, and nested braces.
    """
    raw = raw.strip()
    # Strip code fences first
    if raw.startswith("```"):
        lines = raw.splitlines()
        end = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), None)
        raw = "\n".join(lines[1:end] if end else lines[1:]).strip()

    # Find the first { and the matching closing }
    start = raw.find("{")
    if start == -1:
        return raw
    depth = 0
    for i, ch in enumerate(raw[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    return raw[start:]


# Keep old name as alias for backward compat
def _strip_code_fences(raw: str) -> str:
    return _extract_json(raw)


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
            "clarification_needed": None,
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


# ---------------------------------------------------------------------------
# Conversational Intake Agent
# ---------------------------------------------------------------------------

_DOC_TYPE_RULES: dict[str, str] = {
    "fir": (
        "Must include ALL of these — do not proceed without them: "
        "(1) Complainant full name, (2) Complainant's complete residential address, "
        "(3) Complainant contact number, (4) Exact date of incident, (5) Exact time of incident, "
        "(6) Place/location of incident, (7) Narrative of what happened, "
        "(8) Accused details (if unknown write 'unknown male/female with description'). "
        "CONDITIONALS: If theft -- demand specific stolen items list. Ask for IMEI ONLY for mobile phones and laptops. "
        "For vehicles, ask for registration number and chassis/engine number. "
        "For jewellery, ask weight/description. For cash, ask exact amount. Do NOT ask for IMEI for appliances, jewellery, or clothing. "
        "If assault -- ask about physical injuries and whether an MLC (Medico-Legal Certificate) was obtained. "
        "ALWAYS ask for complainant address and time of incident — these are mandatory for FIR registration."
    ),
    "legal_notice": (
        "Must include: Sender full name/address, recipient full name/address, their relationship, "
        "chronological grievance. STRICT: Extract the exact Demand (amount or specific action required) "
        "-- DO NOT guess, ask the user. Extract the Deadline (15 or 30 days). Let the user decide."
    ),
    "consumer_complaint": (
        "Must include: Complainant and Opposite Party details, transaction proof (invoice number, "
        "date, amount paid), description of defect/deficiency. STRICT: Confirm prior contact with "
        "company (ticket number or date). Extract specific relief sought: refund amount + "
        "compensation amount separately."
    ),
    "cheque_bounce": (
        "Must include: Drawer (who gave cheque) full details, Payee (who received) full details, "
        "description of enforceable debt/liability, cheque details (number, date, bank, amount). "
        "STRICT: Return Memo Date and Return Reason from bank. LOGIC: If return memo date is older "
        "than 30 days from today (2026-04-10), trigger warning that the 30-day legal notice window "
        "under NI Act Section 138 has expired."
    ),
    "eviction_notice": (
        "Must include: Landlord name/address, Tenant name/address, complete property address, "
        "how tenancy originated (agreement/verbal), monthly rent amount. STRICT: Extract valid legal "
        "grounds -- one of: unpaid rent (how many months, total amount), landlord's personal need "
        "(details), lease expiry date, or unauthorized subletting."
    ),
    "tenant_eviction": (
        "Must include: Landlord name/address, Tenant name/address, complete property address, "
        "how tenancy originated (agreement/verbal), monthly rent amount. STRICT: Extract valid legal "
        "grounds -- one of: unpaid rent (how many months, total amount), landlord's personal need "
        "(details), lease expiry date, or unauthorized subletting."
    ),
}

_CONVERSATIONAL_SYSTEM_PROMPT = """You are a precise Indian legal intake specialist helping draft a {doc_type} document.

LANGUAGE RULE (CRITICAL — override everything else):
- The user has explicitly selected language: {lang_label}.
- You MUST write "agent_reply" in {lang_label} ONLY. No exceptions.
- {lang_instruction}

MANDATORY FACTS TO COLLECT:
{doc_type_rules}

ALREADY COLLECTED:
{current_state_json}

STRICT OUTPUT RULES — YOU MUST FOLLOW THESE:
- Output ONLY a single JSON object. No explanation, no preamble, no prose outside the JSON.
- Do NOT write "Here is the JSON" or any other text before or after.
- The JSON must have exactly these four keys: extracted_data, is_complete, missing_fields, agent_reply.

ANOMALY CHECK (run before asking any follow-up questions):
- If the stolen items list contains any large/implausible item (washing machine, TV, television, refrigerator, fridge, sofa, AC, air conditioner, furniture) AND the location is a public space (metro station, railway station, bus stand, market, mall, road, plaza, park): do NOT ask for other missing facts yet. Instead, set agent_reply to ONLY a clarifying question: "You mentioned a [item] was stolen at [location]. Could you clarify — was it taken from a nearby vehicle/home, or directly from that public place?" Set is_complete=false and missing_fields=["clarification: implausible item at public location"].

PROCESSING STEPS:
1. Parse the user message (supports Hindi, Hinglish, English). Extract all facts mentioned.
2. Run ANOMALY CHECK above first.
3. Merge with ALREADY COLLECTED facts — never lose previously collected data.
4. Check which mandatory facts are still missing.
5. If missing: set is_complete=false, ask for at most 2 missing things in agent_reply (in Hindi if user used Hindi/Hinglish).
6. If cheque bounce return memo is >30 days old: warn about expired legal window.
7. If all mandatory facts collected: set is_complete=true, tell user you are ready to draft (in their language).

OUTPUT (JSON ONLY, no other text):
{{"extracted_data": {{}}, "is_complete": false, "missing_fields": ["example"], "agent_reply": "your reply here"}}"""


async def chat_intake(
    doc_type: str,
    messages: list[dict[str, str]],
    lang: str = "en",
) -> dict[str, Any]:
    """
    Multi-turn conversational intake.

    Args:
        doc_type: One of fir | legal_notice | consumer_complaint |
                  cheque_bounce | tenant_eviction.
        messages: Full conversation history as list of
                  {"role": "user"|"agent", "content": "..."} dicts.

    Returns:
        Dict with keys: extracted_data, is_complete, missing_fields, agent_reply.
    """
    rules = _DOC_TYPE_RULES.get(doc_type, "Collect all relevant facts needed for the document.")

    # Derive current_state_json from the last agent message that contains JSON,
    # so the LLM has continuity on already-extracted data.
    current_state: dict[str, Any] = {}
    for msg in reversed(messages):
        if msg.get("role") == "agent":
            try:
                candidate = _strip_code_fences(msg["content"])
                parsed = json.loads(candidate)
                if "extracted_data" in parsed:
                    current_state = parsed["extracted_data"]
                    break
            except (json.JSONDecodeError, KeyError):
                continue

    lang_label = "Hindi (Devanagari script)" if lang == "hi" else "English"
    lang_instruction = (
        "Write in clear Hindi using Devanagari script. Do not use Roman/Latin script for Hindi words."
        if lang == "hi" else
        "Write in clear English. You may include Hindi legal terms in parentheses where helpful."
    )
    system_prompt = _CONVERSATIONAL_SYSTEM_PROMPT.format(
        doc_type=doc_type,
        doc_type_rules=rules,
        current_state_json=json.dumps(current_state, ensure_ascii=False, indent=2),
        lang_label=lang_label,
        lang_instruction=lang_instruction,
    )

    # Build Groq messages list: system + alternating user/assistant turns.
    # "agent" role maps to "assistant" in the OpenAI/Groq message format.
    groq_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        role = "assistant" if msg.get("role") == "agent" else "user"
        groq_messages.append({"role": role, "content": msg["content"]})

    import asyncio
    from groq import RateLimitError
    from services.groq_client import get_client
    client = get_client()

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = await client.chat.completions.create(
                model=MODEL_LARGE,
                messages=groq_messages,  # type: ignore[arg-type]
                temperature=0.1,
                max_tokens=900,
            )
            raw = response.choices[0].message.content or ""
            break
        except RateLimitError as exc:
            last_exc = exc
            if attempt < 3:
                await asyncio.sleep(2 ** attempt)
        except Exception as exc:
            last_exc = exc
            if attempt < 3:
                await asyncio.sleep(2 ** attempt)
    else:
        raise last_exc  # type: ignore[misc]

    cleaned = _extract_json(raw)
    try:
        result: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError:
        # Detect if user was speaking Hinglish/Hindi so fallback reply matches
        fallback_reply = (
            "क्षमा करें, मुझे थोड़ी परेशानी हुई। कृपया अपनी स्थिति फिर से बताइए — क्या हुआ, कब हुआ, और कहाँ हुआ?"
            if lang == "hi" else
            "Sorry, I had trouble understanding that. Could you describe what happened, when, and where?"
        )
        result = {
            "extracted_data": current_state,
            "is_complete": False,
            "missing_fields": ["details"],
            "agent_reply": fallback_reply,
        }

    # Ensure all expected keys are present
    result.setdefault("extracted_data", current_state)
    result.setdefault("is_complete", False)
    result.setdefault("missing_fields", [])
    result.setdefault("agent_reply", "Please provide more details.")

    return result
