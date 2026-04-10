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
# Cheque bounce handler (Section 138 NI Act)
# ---------------------------------------------------------------------------

def _handle_cheque_bounce(incident_json: dict) -> dict[str, Any]:
    parties = incident_json.get("parties", [])
    complainant = _extract_party(parties, "complainant")
    respondent = _extract_party(parties, "respondent")

    # Extract cheque-specific fields from case JSON
    cheque_number = incident_json.get("cheque_number", complainant.get("cheque_number", "[FILL IN]"))
    cheque_date = incident_json.get("cheque_date", "[FILL IN]")
    cheque_amount = incident_json.get("cheque_amount", "[FILL IN]")
    bank_name = incident_json.get("bank_name", "[FILL IN]")
    return_memo_date = incident_json.get("return_memo_date", "[FILL IN]")
    drawer_name = incident_json.get("drawer_name", respondent.get("name", "[FILL IN]"))

    fields_mapping = [
        {"field": "Cheque Number",       "value": cheque_number,    "hint": "Printed on the face of the cheque"},
        {"field": "Cheque Date",         "value": cheque_date,      "hint": "Date written on the cheque"},
        {"field": "Cheque Amount",       "value": cheque_amount,    "hint": "Amount for which the cheque was drawn"},
        {"field": "Bank Name",           "value": bank_name,        "hint": "Bank on which the cheque was drawn"},
        {"field": "Return Memo Date",    "value": return_memo_date, "hint": "Date on the bank's dishonour memo"},
        {"field": "Drawer Name",         "value": drawer_name,      "hint": "Name of the person who issued the cheque"},
        {"field": "Complainant Name",    "value": complainant.get("name", "[FILL IN]"),    "hint": "Payee — the person who received the cheque"},
        {"field": "Complainant Contact", "value": complainant.get("contact", "[FILL IN]"), "hint": "Mobile number or email for court notices"},
    ]

    steps = [
        {
            "en": "Step 1: Send a legal notice to the drawer via Registered Post (RPAD) within 30 days of receiving the bank return memo.",
            "hi": "Step 1: Bank return memo milne ke 30 din ke andar drawer ko Registered Post (RPAD) se legal notice bhejein.",
        },
        {
            "en": "Step 2: Wait 15 days after delivery of the notice for the drawer to make payment.",
            "hi": "Step 2: Notice delivery ke baad drawer ko payment karne ke liye 15 din ka intezaar karein.",
        },
        {
            "en": "Step 3: If the amount remains unpaid after 15 days, file a criminal complaint in the Magistrate Court within 30 days of expiry of the notice period.",
            "hi": "Step 3: 15 din baad bhi payment na ho to notice period khatam hone ke 30 din ke andar Magistrate Court mein criminal complaint file karein.",
        },
        {
            "en": "Step 4: Attach to the complaint: original cheque, bank return memo, copy of legal notice, postal receipt, and a sworn affidavit of facts.",
            "hi": "Step 4: Complaint ke saath yeh attach karein: original cheque, bank return memo, legal notice ki copy, postal receipt, aur facts ka sworn affidavit.",
        },
        {
            "en": "Step 5: Submit the complaint at the Magistrate Court filing counter and obtain an acknowledgement / case number.",
            "hi": "Step 5: Magistrate Court ke filing counter par complaint submit karein aur acknowledgement / case number lein.",
        },
    ]

    return {
        "portal_name": "Local Magistrate Court (Section 138 NI Act)",
        "portal_url": "",
        "filing_mode": "court",
        "portal_note": "Cheque bounce complaints under Section 138 of the Negotiable Instruments Act 1881 are filed at the Magistrate Court having jurisdiction over the place where the cheque was presented.",
        "steps": steps,
        "fields_mapping": fields_mapping,
        "required_documents": [
            "Original dishonoured cheque",
            "Bank return memo (with reason for dishonour)",
            "Copy of legal notice sent to drawer",
            "Registered post receipt / speed post tracking proof",
            "Affidavit of facts",
            "Complainant ID proof",
        ],
        "warnings": [
            "Notice must be sent within 30 days of receiving the cheque return memo — missing this deadline forfeits your right to prosecute under Section 138.",
            "Complaint must be filed within 30 days of expiry of the 15-day notice period — this is a strict limitation.",
            "Ensure the cheque was issued for an enforceable debt or liability, not as a gift or security deposit (Section 138 NI Act requirement).",
        ],
    }


# ---------------------------------------------------------------------------
# Legal notice handler
# ---------------------------------------------------------------------------

def _handle_legal_notice(incident_json: dict) -> dict[str, Any]:
    parties = incident_json.get("parties", [])
    complainant = _extract_party(parties, "complainant")
    respondent = _extract_party(parties, "respondent")

    sender_name = incident_json.get("sender_name", complainant.get("name", "[FILL IN]"))
    recipient_name = incident_json.get("recipient_name", respondent.get("name", "[FILL IN]"))
    demand_amount = incident_json.get("demand_amount", "[FILL IN]")
    demand_deadline = incident_json.get("demand_deadline", "[FILL IN]")

    fields_mapping = [
        {"field": "Sender Name",       "value": sender_name,      "hint": "Your full name as it should appear on the notice"},
        {"field": "Recipient Name",    "value": recipient_name,   "hint": "Full name of the person / company receiving the notice"},
        {"field": "Demand Amount",     "value": demand_amount,    "hint": "Total amount or remedy being demanded"},
        {"field": "Demand Deadline",   "value": demand_deadline,  "hint": "Number of days given to comply (typically 15 or 30)"},
        {"field": "Recipient Address", "value": respondent.get("contact", "[FILL IN]"), "hint": "Complete postal address of recipient for RPAD delivery"},
    ]

    steps = [
        {
            "en": "Step 1: Print the notice on plain paper or advocate letterhead (advocate stamp is recommended for added legal weight).",
            "hi": "Step 1: Notice ko plain paper ya advocate letterhead par print karein (advocate stamp se notice ka zyada asar hota hai).",
        },
        {
            "en": "Step 2: Send it via Registered Post with Acknowledgement Due (RPAD) to the respondent's address.",
            "hi": "Step 2: Ise Registered Post with Acknowledgement Due (RPAD) se respondent ke address par bhejein.",
        },
        {
            "en": "Step 3: Keep the postal receipt safely and track delivery on indiapost.gov.in using the consignment number.",
            "hi": "Step 3: Postal receipt sambhal kar rakhein aur consignment number se indiapost.gov.in par delivery track karein.",
        },
        {
            "en": "Step 4: Also send a copy via email to create a digital timestamp as supporting evidence.",
            "hi": "Step 4: Digital timestamp evidence ke liye ek copy email se bhi bhejein.",
        },
        {
            "en": "Step 5: Wait for the demand deadline stated in the notice (15 or 30 days from date of delivery).",
            "hi": "Step 5: Notice mein likhe demand deadline tak (delivery date se 15 ya 30 din) intezaar karein.",
        },
        {
            "en": "Step 6: If there is no response or compliance, proceed to file a civil suit or escalate as per the terms of the notice.",
            "hi": "Step 6: Agar koi jawab ya compliance nahi milti, to civil suit file karein ya notice ki shartein anusaar aage karwaai karein.",
        },
    ]

    return {
        "portal_name": "Registered Post / Speed Post (No court portal)",
        "portal_url": "https://www.indiapost.gov.in/",
        "filing_mode": "post",
        "portal_note": "Legal notices do not require a court portal. They are served by Registered Post (RPAD). Track your consignment on indiapost.gov.in.",
        "steps": steps,
        "fields_mapping": fields_mapping,
        "required_documents": [
            "Signed copy of legal notice",
            "Registered post receipt (RPAD)",
            "Proof of respondent's address",
            "Supporting documents (agreement, invoice, photos, etc.)",
            "Copy of any prior correspondence",
        ],
        "warnings": [
            "Always keep the postal receipt — it is your primary proof of service.",
            "Email copy alone is not legally sufficient — registered post (RPAD) is mandatory for legal standing.",
            "The response deadline starts from the date of delivery to the recipient, not the date you sent it.",
        ],
    }


# ---------------------------------------------------------------------------
# Tenant eviction handler
# ---------------------------------------------------------------------------

def _handle_tenant_eviction(incident_json: dict) -> dict[str, Any]:
    parties = incident_json.get("parties", [])
    complainant = _extract_party(parties, "complainant")
    respondent = _extract_party(parties, "respondent")

    landlord_name = incident_json.get("landlord_name", complainant.get("name", "[FILL IN]"))
    tenant_name = incident_json.get("tenant_name", respondent.get("name", "[FILL IN]"))
    property_address = incident_json.get("property_address", incident_json.get("location", "[FILL IN]"))
    eviction_grounds = incident_json.get("eviction_grounds", "[FILL IN]")
    unpaid_months = incident_json.get("unpaid_months", "[FILL IN]")

    fields_mapping = [
        {"field": "Landlord Name",      "value": landlord_name,     "hint": "Your full name as owner of the property"},
        {"field": "Tenant Name",        "value": tenant_name,       "hint": "Full name of the tenant to be evicted"},
        {"field": "Property Address",   "value": property_address,  "hint": "Complete address of the rented premises"},
        {"field": "Grounds for Eviction", "value": eviction_grounds, "hint": "Legal ground: non-payment, expiry of lease, subletting, damage, etc."},
        {"field": "Unpaid Months",      "value": str(unpaid_months), "hint": "Number of months rent is outstanding (if applicable)"},
        {"field": "Tenant Contact",     "value": respondent.get("contact", "[FILL IN]"), "hint": "Tenant's address for RPAD delivery of notice"},
    ]

    steps = [
        {
            "en": "Step 1: Send an eviction notice to the tenant via Registered Post (RPAD) clearly stating the grounds for eviction.",
            "hi": "Step 1: Tenant ko Registered Post (RPAD) se eviction notice bhejein jisme eviction ke karan saaf-saaf likhe hon.",
        },
        {
            "en": "Step 2: Wait for the tenant's response, typically 15 to 30 days as stated in the notice.",
            "hi": "Step 2: Tenant ke jawab ka intezaar karein, aam taur par notice mein likhe 15 se 30 din tak.",
        },
        {
            "en": "Step 3: If the tenant does not vacate, file an eviction petition at the local Rent Control Authority or Civil Court.",
            "hi": "Step 3: Agar tenant nahi nikalta, to local Rent Control Authority ya Civil Court mein eviction petition file karein.",
        },
        {
            "en": "Step 4: For Delhi specifically, file at the Delhi Rent Control Tribunal at Tis Hazari Courts.",
            "hi": "Step 4: Delhi ke liye, Tis Hazari Courts ke Delhi Rent Control Tribunal mein file karein.",
        },
        {
            "en": "Step 5: Attach: rent agreement, ownership proof, copy of eviction notice, postal receipt, and rent payment history.",
            "hi": "Step 5: Yeh saath mein lagaein: rent agreement, ownership proof, eviction notice ki copy, postal receipt, aur rent payment ka record.",
        },
    ]

    return {
        "portal_name": "Rent Control Authority / Civil Court (state-dependent)",
        "portal_url": "",
        "filing_mode": "court",
        "portal_note": "Tenant eviction petitions are filed at the local Rent Control Authority or Civil Court depending on your state's applicable Rent Control Act.",
        "steps": steps,
        "fields_mapping": fields_mapping,
        "required_documents": [
            "Rent agreement / lease deed",
            "Property ownership proof (registry / sale deed)",
            "Copy of eviction notice sent",
            "Registered post receipt",
            "Rent payment history / ledger",
            "ID proof of landlord",
        ],
        "warnings": [
            "Grounds for eviction must match one of the valid legal grounds under the applicable state Rent Control Act — arbitrary eviction is not permitted.",
            "If the tenant has been in possession for over 5 years, eviction proceedings are more complex — consult an advocate.",
            "Do not cut off utilities or attempt forcible eviction — this constitutes illegal eviction and is a criminal offence under BNS 2023.",
        ],
    }


# ---------------------------------------------------------------------------
# FIR handler (static — no Groq call to avoid truncation)
# ---------------------------------------------------------------------------

def _handle_fir(incident_json: dict) -> dict[str, Any]:
    parties = incident_json.get("parties", [])
    location = incident_json.get("location", "")
    incident_type = incident_json.get("incident_type", "")
    key_claims = incident_json.get("key_claims", [])
    complainant = _extract_party(parties, "complainant")

    state = _detect_state(location)
    is_violent = _is_violent_incident(incident_type, key_claims)
    is_efir_crime = _is_efir_eligible_crime(incident_type, key_claims)

    if not is_violent and is_efir_crime and state in _STATE_EFIR_PORTALS:
        portal = _STATE_EFIR_PORTALS[state]
        portal_name = portal["name"]
        portal_url = portal["url"]
        portal_note = portal["note"]
        filing_mode = "online"
        steps = [
            {"en": "Step 1: Visit the e-FIR portal linked above and register or log in with your mobile number.", "hi": "Step 1: ऊपर दिए e-FIR portal पर जाएं और अपने mobile number से register या login करें।"},
            {"en": "Step 2: Select 'File FIR' or 'Lodge Complaint' and choose the correct offence category (Theft / Snatching / Vehicle Theft).", "hi": "Step 2: 'File FIR' या 'Lodge Complaint' चुनें और सही offence category चुनें (Theft / Snatching / Vehicle Theft)।"},
            {"en": "Step 3: Fill in complainant details exactly as they appear on your Aadhaar card.", "hi": "Step 3: Complainant का विवरण बिल्कुल Aadhaar card के अनुसार भरें।"},
            {"en": "Step 4: Enter incident details — date, time, exact location, and description of what was stolen.", "hi": "Step 4: घटना का विवरण भरें — तारीख, समय, सही जगह, और क्या चोरी हुआ।"},
            {"en": "Step 5: Upload a scanned copy of this generated FIR document as supporting reference.", "hi": "Step 5: इस generated FIR document की scanned copy supporting reference के रूप में upload करें।"},
            {"en": "Step 6: Submit and note down the FIR / complaint number for future reference.", "hi": "Step 6: Submit करें और FIR / complaint number note कर लें।"},
        ]
        warnings = [
            "e-FIR is available only for non-violent property offences (theft, snatching, vehicle theft).",
            "If police refuse to register your FIR online, you can approach the Superintendent of Police or file a complaint under BNSS Section 173.",
        ]
    else:
        portal_name = "Nearest Police Station (In-Person Filing)"
        portal_url = ""
        filing_mode = "offline"
        portal_note = (
            "This incident involves violence or a serious offence — e-FIR is not available. You must file in person at the police station."
            if is_violent else
            "e-FIR is not available for your state/offence type. Please file in person at the nearest police station."
        )
        steps = [
            {"en": "Step 1: Go to the nearest police station (preferably the one with jurisdiction over the incident location).", "hi": "Step 1: नजदीकी police station जाएं (जहां घटना हुई उस area का police station)।"},
            {"en": "Step 2: Take a printout of this generated FIR document and carry it with you.", "hi": "Step 2: इस generated FIR document का printout लें और साथ ले जाएं।"},
            {"en": "Step 3: Submit the complaint at the duty officer's desk and request FIR registration.", "hi": "Step 3: Duty officer के desk पर complaint submit करें और FIR registration की मांग करें।"},
            {"en": "Step 4: Carry original ID proof (Aadhaar), and any evidence (photos, CCTV footage, witness contacts).", "hi": "Step 4: Original ID proof (Aadhaar) और कोई भी evidence (photos, CCTV footage, गवाहों के contacts) साथ लाएं।"},
            {"en": "Step 5: If police refuse to register the FIR, request a written refusal. You may then approach the Superintendent of Police or a Magistrate.", "hi": "Step 5: अगर police FIR register करने से मना करे, तो लिखित refusal मांगें। फिर SP या Magistrate से शिकायत कर सकते हैं।"},
            {"en": "Step 6: Collect a copy of the registered FIR — this is your legal right under BNSS 2023.", "hi": "Step 6: Registered FIR की copy लें — यह BNSS 2023 के तहत आपका कानूनी अधिकार है।"},
        ]
        warnings = [
            "Police are legally bound to register your FIR — refusal is an offence under BNSS 2023.",
            "If violence is involved, seek medical attention first and obtain an MLC (Medico-Legal Certificate) from the hospital before filing.",
            "Do not leave the police station without a copy of your registered FIR.",
        ]

    fields_mapping = [
        {"field": "Complainant Name",    "value": complainant.get("name", "[FILL IN]"),    "hint": "As per Aadhaar card"},
        {"field": "Complainant Contact", "value": complainant.get("contact", "[FILL IN]"), "hint": "Mobile number for police to reach you"},
        {"field": "Incident Location",   "value": location or "[FILL IN]",                 "hint": "Exact address where the incident occurred"},
        {"field": "Incident Date/Time",  "value": f"{incident_json.get('dates', ['[FILL IN]'])[0] if incident_json.get('dates') else '[FILL IN]'} {incident_json.get('incident_time', '')}".strip(), "hint": "Date and time of the incident"},
    ]

    return {
        "portal_name": portal_name,
        "portal_url": portal_url,
        "filing_mode": filing_mode,
        "portal_note": portal_note,
        "steps": steps,
        "fields_mapping": fields_mapping,
        "required_documents": [
            "Printout of this generated FIR document",
            "Original ID proof (Aadhaar card / Voter ID)",
            "Any evidence available (photos, screenshots, CCTV footage)",
            "List of stolen/missing items with approximate values",
            "Witness names and contact numbers (if any)",
        ],
        "warnings": warnings,
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
            result = _handle_fir(incident_json)
            await push_event(session_id, "filing_assistant", "complete", {"filing": result})
            return result

        elif doc_type == "consumer_complaint":
            result = await _handle_consumer_complaint(incident_json, draft)
            await push_event(session_id, "filing_assistant", "complete", {"filing": result})
            return result

        elif doc_type == "cheque_bounce":
            result = _handle_cheque_bounce(incident_json)
            await push_event(session_id, "filing_assistant", "complete", {"filing": result})
            return result

        elif doc_type == "legal_notice":
            result = _handle_legal_notice(incident_json)
            await push_event(session_id, "filing_assistant", "complete", {"filing": result})
            return result

        elif doc_type == "tenant_eviction":
            result = _handle_tenant_eviction(incident_json)
            await push_event(session_id, "filing_assistant", "complete", {"filing": result})
            return result

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
