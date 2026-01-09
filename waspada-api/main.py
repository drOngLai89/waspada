import os
import re
import json
from datetime import date
from typing import List, Optional, Literal, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---- OpenAI (new SDK) ----
try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None


# ----------------------------
# Models
# ----------------------------
Lang = Literal["EN", "MS", "ZH", "TA"]

Verdict = Literal[
    "HIGH_RISK_INDICATORS",
    "SUSPICIOUS_INDICATORS",
    "UNCLEAR_NEEDS_VERIFICATION",
]

Risk = Literal["HIGH", "MEDIUM", "LOW"]

Scenario = Literal[
    "money_moved",
    "asked_to_pay",
    "otp_password",
    "courier",
    "investment",
    "job",
    "romance",
    "impersonation",
    "other",
]

class AnalyzeIn(BaseModel):
    image_data_url: str = Field(..., description="data:<mime>;base64,...")
    lang: Lang = "EN"

class Source(BaseModel):
    id: str
    title: str
    org: str
    url: str
    notes: Optional[str] = None
    last_verified: Optional[str] = None  # YYYY-MM-DD

class Action(BaseModel):
    step: str
    why: Optional[str] = None
    source_ids: Optional[List[str]] = None

class Contact(BaseModel):
    name: str
    type: Literal["phone", "url", "email"]
    value: str
    notes: Optional[str] = None
    source_ids: Optional[List[str]] = None

class VerifyResult(BaseModel):
    verdict: Verdict
    risk: Risk
    malaysia_relevance: str
    scenario: Scenario
    out_of_scope: Optional[bool] = False

    what_the_screenshot_shows: Optional[List[str]] = None
    analysis: Optional[str] = None
    findings: Optional[List[str]] = None

    recommended_next_actions: Optional[List[Action]] = None
    who_to_contact: Optional[List[Contact]] = None
    evidence_to_save: Optional[List[str]] = None

    caveat: Optional[str] = None
    sources: Optional[List[Source]] = None


# ----------------------------
# App
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def today_str() -> str:
    return date.today().isoformat()


# ----------------------------
# Official Malaysia sources (curated)
# ----------------------------
def official_sources() -> List[Source]:
    # Keep URLs official / authoritative.
    # (You can expand this list anytime.)
    d = today_str()
    return [
        Source(
            id="NFCC_NSRC_997",
            org="NFCC (Prime Minister’s Department)",
            title="National Scam Response Centre (NSRC) — 997",
            url="https://nfcc.jpm.gov.my/index.php/en/about-nsrc",
            notes="Urgent hotline if money moved / online financial fraud. Speed matters.",
            last_verified=d,
        ),
        Source(
            id="PDRM_CCID_EREPORT",
            org="PDRM (Royal Malaysia Police)",
            title="CCID (Commercial Crime) reporting / e-Reporting guidance",
            url="https://rmp.gov.my/",
            notes="Use official PDRM channels for police reports. (Your Resources tab can point to the exact CCID reporting page you chose.)",
            last_verified=d,
        ),
        Source(
            id="SC_INVESTOR_ALERT",
            org="Securities Commission Malaysia",
            title="Investor Alert List",
            url="https://www.sc.com.my/investor-alert-list",
            notes="Check suspicious/unlicensed investment offers before investing/transferring.",
            last_verified=d,
        ),
        Source(
            id="SC_SCAM_GUIDE",
            org="Securities Commission Malaysia",
            title="Beware of Scams (Investor Empowerment)",
            url="https://www.sc.com.my/investor-empowerment/scam",
            notes="Official investor education and scam warnings.",
            last_verified=d,
        ),
        Source(
            id="BNM_CONSUMER_ALERT",
            org="Bank Negara Malaysia",
            title="Financial Consumer Alert (FCA)",
            url="https://www.bnm.gov.my/financial-consumer-alert-list",
            notes="Check if an entity is listed for consumer alerts (useful for suspicious offers).",
            last_verified=d,
        ),
        Source(
            id="MCMC_ADUAN",
            org="MCMC (Malaysian Communications and Multimedia Commission)",
            title="Complaints / consumer channels (Aduan)",
            url="https://www.mcmc.gov.my/en/make-a-complaint/make-a-complaint",
            notes="For telco/SMS/calls/platform issues. Use official complaint channels.",
            last_verified=d,
        ),
    ]


def sources_map(sources: List[Source]) -> Dict[str, Source]:
    return {s.id: s for s in sources}


# ----------------------------
# Redaction helpers (extra safety net)
# ----------------------------
_RE_URL = re.compile(r"\bhttps?://\S+\b", re.IGNORECASE)
_RE_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_RE_PHONE = re.compile(r"(\+?\d[\d\-\s().]{6,}\d)")

def redact_text(s: str) -> str:
    if not s:
        return s
    s = _RE_URL.sub("[redacted link]", s)
    s = _RE_EMAIL.sub("[redacted email]", s)
    s = _RE_PHONE.sub("[redacted number]", s)
    return s

def redact_list(items: Optional[List[str]]) -> Optional[List[str]]:
    if not items:
        return items
    out = []
    for x in items:
        if isinstance(x, str):
            out.append(redact_text(x))
    return out

def redact_actions(actions: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    if not actions:
        return actions
    out = []
    for a in actions:
        if not isinstance(a, dict):
            continue
        step = redact_text(str(a.get("step", "")).strip())
        why = a.get("why")
        why = redact_text(str(why).strip()) if why else None
        source_ids = a.get("source_ids")
        if isinstance(source_ids, list):
            source_ids = [str(x) for x in source_ids if x]
        out.append({"step": step, "why": why, "source_ids": source_ids})
    return out

def redact_contacts(contacts: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    if not contacts:
        return contacts
    out = []
    for c in contacts:
        if not isinstance(c, dict):
            continue
        name = redact_text(str(c.get("name", "")).strip())
        ctype = c.get("type", "url")
        value = str(c.get("value", "")).strip()
        notes = c.get("notes")
        notes = redact_text(str(notes).strip()) if notes else None
        source_ids = c.get("source_ids")
        if isinstance(source_ids, list):
            source_ids = [str(x) for x in source_ids if x]
        out.append({"name": name, "type": ctype, "value": value, "notes": notes, "source_ids": source_ids})
    return out


# ----------------------------
# Prompt (defamation-risk hardened)
# ----------------------------
def system_prompt() -> str:
    return """You are Waspada Verify (Malaysia). You analyse a USER-PROVIDED SCREENSHOT for scam/fraud risk indicators and return cautious, non-identifying, Malaysia-first risk triage.

CRITICAL SAFETY + DEFAMATION GUARDRAILS (MUST FOLLOW):
1) Do NOT accuse, label, or assert criminality as fact. Never say “this is a scam”, “they are scammers”, “fraud”, “criminal”, or “illegal” as a conclusion.
   - Use neutral, pattern-based wording: “high risk indicators”, “suspicious indicators”, “unverified solicitation”, “needs verification”.
2) Do NOT identify parties. Do NOT repeat or quote: company/academy names, personal names, phone numbers, emails, bank account numbers, addresses, handles, or URLs found in the screenshot.
   - Refer generically: “an unknown WhatsApp number”, “an unverified organisation name shown”, “a bank account number is shown”.
3) Privacy: assume the output may be shared. Keep it non-identifying and avoid “naming and shaming”.
4) If the screenshot is not clearly scam-related or text can’t be read reliably:
   - set out_of_scope=true
   - provide safe guidance: suggest contacting official channels in the Resources tab for clarification.

MALAYSIA CONTEXT ONLY:
- Guidance must be Malaysia-first and reference Malaysia official bodies (e.g., NFCC/NSRC, PDRM, SC, BNM, MCMC).

OUTPUT REQUIREMENTS:
Return JSON ONLY matching this schema:

{
  "verdict": "HIGH_RISK_INDICATORS" | "SUSPICIOUS_INDICATORS" | "UNCLEAR_NEEDS_VERIFICATION",
  "risk": "HIGH" | "MEDIUM" | "LOW",
  "scenario": "money_moved" | "asked_to_pay" | "otp_password" | "courier" | "investment" | "job" | "romance" | "impersonation" | "other",
  "out_of_scope": boolean,
  "malaysia_relevance": string,

  "what_the_screenshot_shows": [string],
  "analysis": string,
  "findings": [string],

  "recommended_next_actions": [
    { "step": string, "why": string, "source_ids": [string] }
  ],

  "who_to_contact": [
    { "name": string, "type": "phone"|"url"|"email", "value": string, "notes": string, "source_ids": [string] }
  ],

  "evidence_to_save": [string],

  "caveat": string,

  "sources": [
    { "id": string, "title": string, "org": string, "url": string, "notes": string, "last_verified": "YYYY-MM-DD" }
  ]
}

CONTENT RULES:
- “what_the_screenshot_shows” must not be empty.
- “recommended_next_actions” must be specific and practical.
- Each action/contact must include source_ids that refer to items in sources.
- Always include a caveat:
  - Automated, pattern-based triage; not official diagnosis; may be wrong.
  - If money moved: contact your bank + NSRC 997 immediately.
  - Encourage verification via official lists (SC/BNM).
"""


def build_user_prompt(lang: Lang) -> str:
    # Keep it simple; the system prompt carries the rules.
    if lang == "MS":
        return "Analisis tangkap layar ini. Pulangkan JSON sahaja mengikut skema. Ingat: jangan sebut nama/nombor/URL daripada tangkap layar."
    if lang == "ZH":
        return "请分析这张截图。仅返回符合架构的 JSON。注意：不要重复截图里的姓名/号码/链接。"
    if lang == "TA":
        return "இந்த ஸ்கிரீன்ஷாட்டை பகுப்பாய்வு செய்யவும். ஸ்கீமாவிற்கு ஏற்ப JSON மட்டும் திருப்பவும். கவனம்: பெயர்/எண்/இணைப்பை மீண்டும் சொல்ல வேண்டாம்."
    return "Analyse this screenshot. Return JSON only matching the schema. Remember: do not repeat any names/numbers/links from the screenshot."


def extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly pull the first JSON object from model output.
    """
    if not text:
        raise ValueError("Empty model response")
    text = text.strip()

    # If it is already pure JSON
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    # Try to find a JSON object in the text
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("No JSON found in model response")
    return json.loads(m.group(0))


def ensure_minimum_fields(obj: Dict[str, Any], sources: List[Source]) -> Dict[str, Any]:
    """
    Fill missing fields and enforce safe defaults.
    """
    # Always include sources from our official list (model should reference these IDs)
    obj["sources"] = [s.model_dump() for s in sources]

    # Ensure scenario
    if obj.get("scenario") not in {
        "money_moved","asked_to_pay","otp_password","courier","investment","job","romance","impersonation","other"
    }:
        obj["scenario"] = "other"

    # Ensure verdict/risk
    if obj.get("verdict") not in {"HIGH_RISK_INDICATORS", "SUSPICIOUS_INDICATORS", "UNCLEAR_NEEDS_VERIFICATION"}:
        obj["verdict"] = "UNCLEAR_NEEDS_VERIFICATION"
    if obj.get("risk") not in {"HIGH", "MEDIUM", "LOW"}:
        obj["risk"] = "LOW"

    # Ensure out_of_scope boolean
    if not isinstance(obj.get("out_of_scope"), bool):
        obj["out_of_scope"] = False

    # Ensure what_the_screenshot_shows not empty
    w = obj.get("what_the_screenshot_shows")
    if not isinstance(w, list) or len([x for x in w if isinstance(x, str) and x.strip()]) == 0:
        obj["what_the_screenshot_shows"] = [
            "Couldn’t reliably read enough text from the screenshot to assess. Try a clearer screenshot showing the full message and context."
        ]

    # Ensure caveat
    if not obj.get("caveat"):
        obj["caveat"] = (
            "This is automated, pattern-based guidance from a screenshot and is not an official finding. "
            "It may be wrong or incomplete. Avoid sharing identifiable details publicly. "
            "If money has moved, contact your bank immediately and call NSRC 997 (Malaysia)."
        )

    # Redact anything risky (extra guard)
    obj["malaysia_relevance"] = redact_text(str(obj.get("malaysia_relevance", "") or "Malaysia-first guidance using official channels.").strip())
    obj["analysis"] = redact_text(str(obj.get("analysis", "") or "").strip()) if obj.get("analysis") else obj.get("analysis")
    obj["findings"] = redact_list(obj.get("findings"))
    obj["what_the_screenshot_shows"] = redact_list(obj.get("what_the_screenshot_shows"))
    obj["evidence_to_save"] = redact_list(obj.get("evidence_to_save"))
    obj["recommended_next_actions"] = redact_actions(obj.get("recommended_next_actions"))
    obj["who_to_contact"] = redact_contacts(obj.get("who_to_contact"))

    return obj


def openai_client():
    if OpenAI is None:
        raise RuntimeError("openai package not available")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=OPENAI_API_KEY)


# ----------------------------
# Routes
# ----------------------------
@app.get("/version")
def version():
    return {
        "ok": True,
        "has_key": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL,
        "date": today_str(),
    }


@app.get("/resources")
def resources():
    # You already designed a beautiful resources UI.
    # This endpoint provides the structured list.
    srcs = official_sources()

    categories = [
        {
            "id": "urgent",
            "title": "Urgent (money moved / bank transfer)",
            "items": [
                srcs[0].model_dump(),  # NFCC_NSRC_997
                srcs[1].model_dump(),  # PDRM_CCID_EREPORT (placeholder root; your UI can show the exact portal URL you use)
            ],
        },
        {
            "id": "check_before_pay",
            "title": "Check before you pay (accounts / investment offers)",
            "items": [
                srcs[2].model_dump(),  # SC_INVESTOR_ALERT
                srcs[3].model_dump(),  # SC_SCAM_GUIDE
                srcs[4].model_dump(),  # BNM_CONSUMER_ALERT
            ],
        },
        {
            "id": "telco_platform",
            "title": "Calls / SMS / platforms",
            "items": [
                srcs[5].model_dump(),  # MCMC_ADUAN
            ],
        },
    ]

    return {"result": {"last_verified": today_str(), "categories": categories}}


@app.get("/plan/{scenario}")
def plan(scenario: str):
    """
    Lightweight plan endpoint used by your Toolkit scenario pages.
    This stays non-identifying and Malaysia-first.
    """
    s = scenario.strip().lower()
    scenario_norm: Scenario = "other"  # default
    allowed = {
        "money_moved": "money_moved",
        "asked_to_pay": "asked_to_pay",
        "otp_password": "otp_password",
        "courier": "courier",
        "investment": "investment",
        "job": "job",
        "romance": "romance",
        "impersonation": "impersonation",
        "other": "other",
    }
    if s in allowed:
        scenario_norm = allowed[s]

    srcs = official_sources()
    smap = sources_map(srcs)

    # Minimal per-scenario “When:” text
    when_map = {
        "money_moved": "Immediately",
        "asked_to_pay": "Before paying / transferring",
        "otp_password": "Immediately",
        "courier": "Before paying fees / clicking links",
        "investment": "Before transferring / investing",
        "job": "Before paying fees / sharing documents",
        "romance": "Before sending money or gifts",
        "impersonation": "Immediately",
        "other": "Immediately",
    }

    # Shared building blocks
    def act(step: str, why: str, ids: List[str]) -> Dict[str, Any]:
        return {"step": step, "why": why, "source_ids": ids}

    # Contacts (non-identifying, official)
    contacts = [
        {
            "name": "National Scam Response Centre (NSRC) — 997",
            "type": "phone",
            "value": "997",
            "notes": "If money has moved / urgent online financial fraud.",
            "source_ids": ["NFCC_NSRC_997"],
        },
        {
            "name": "Securities Commission Malaysia — Investor Alert List",
            "type": "url",
            "value": smap["SC_INVESTOR_ALERT"].url,
            "notes": "Check suspicious/unlicensed investment offers.",
            "source_ids": ["SC_INVESTOR_ALERT"],
        },
        {
            "name": "Bank Negara Malaysia — Financial Consumer Alert",
            "type": "url",
            "value": smap["BNM_CONSUMER_ALERT"].url,
            "notes": "Check consumer alert listings.",
            "source_ids": ["BNM_CONSUMER_ALERT"],
        },
        {
            "name": "MCMC — Make a Complaint",
            "type": "url",
            "value": smap["MCMC_ADUAN"].url,
            "notes": "For SMS/calls/platform complaints via official channel.",
            "source_ids": ["MCMC_ADUAN"],
        },
    ]

    # Scenario-specific steps (still general but relevant)
    do_now = []
    next_steps = []
    evidence = [
        "Screenshots of the full conversation (including timestamps).",
        "Phone number(s), usernames, URLs, QR codes shown (store privately).",
        "Bank details / transaction references / receipts (if any).",
        "Any profiles, ads, or pages involved (capture full page).",
    ]

    # Money moved
    if scenario_norm == "money_moved":
        do_now = [
            act("Contact your bank immediately and report unauthorised transfers.", "Speed matters to increase the chance of recovery.", ["NFCC_NSRC_997"]),
            act("Call NSRC 997 as soon as possible.", "NSRC coordinates response for online financial fraud in Malaysia.", ["NFCC_NSRC_997"]),
            act("Make a police report via official PDRM channels if appropriate.", "A report supports investigation and follow-up.", ["PDRM_CCID_EREPORT"]),
        ]
        next_steps = [
            act("Stop further transfers and stop engaging with the other party.", "Scammers often push urgency to trigger more payments.", ["NFCC_NSRC_997"]),
            act("Preserve evidence and share it only with your bank / authorities.", "Evidence supports investigation and dispute handling.", ["NFCC_NSRC_997"]),
        ]

    elif scenario_norm == "investment":
        do_now = [
            act("Do not transfer funds based on promised returns or urgency.", "Guaranteed/high returns and urgency are common scam indicators.", ["SC_SCAM_GUIDE"]),
            act("Check the entity on SC Investor Alert List and BNM FCA before investing.", "Helps identify suspicious/unlicensed entities.", ["SC_INVESTOR_ALERT", "BNM_CONSUMER_ALERT"]),
        ]
        next_steps = [
            act("If you already transferred money, treat it as money moved and call NSRC 997.", "Early reporting improves response options.", ["NFCC_NSRC_997"]),
        ]

    elif scenario_norm == "otp_password":
        do_now = [
            act("Stop engaging. Do not click links, scan QR codes, or install apps requested by the other party.", "Remote-control apps and links are used to take over accounts.", ["NFCC_NSRC_997"]),
            act("Do not share OTP/TAC/passwords. If shared, change passwords immediately and secure accounts.", "OTP/TAC enables rapid account takeover and fund movement.", ["NFCC_NSRC_997"]),
            act("If money has moved, contact your bank immediately and call NSRC 997.", "Speed matters for fraud response.", ["NFCC_NSRC_997"]),
        ]
        next_steps = [
            act("Save evidence (screenshots, chat logs, numbers, URLs) privately.", "Supports bank and authority investigation.", ["NFCC_NSRC_997"]),
        ]

    elif scenario_norm == "courier":
        do_now = [
            act("Do not pay ‘release fees’ or ‘delivery fees’ from unsolicited courier messages.", "Fee-demand tactics are common in courier scams.", ["NFCC_NSRC_997"]),
            act("Avoid clicking links in SMS; verify via official courier/bank sites.", "Links may lead to phishing pages.", ["MCMC_ADUAN"]),
        ]
        next_steps = [
            act("If you entered bank details or paid, treat it as money moved and call NSRC 997.", "Early reporting helps limit damage.", ["NFCC_NSRC_997"]),
        ]

    elif scenario_norm == "job":
        do_now = [
            act("Do not pay ‘processing fees’, ‘training fees’, or ‘equipment fees’ to get a job.", "Upfront payments are a common job-scam pattern.", ["NFCC_NSRC_997"]),
            act("Verify the company via official channels and avoid WhatsApp-only ‘HR’ processes.", "Scammers imitate real companies but use unofficial routes.", ["NFCC_NSRC_997"]),
        ]
        next_steps = [
            act("If you already paid, contact your bank and call NSRC 997 immediately.", "Treat it as money moved.", ["NFCC_NSRC_997"]),
            act("If pressured to transfer, consider making a police report via official PDRM channels.", "Reporting helps enforcement follow-up.", ["PDRM_CCID_EREPORT"]),
        ]

    elif scenario_norm == "romance":
        do_now = [
            act("Do not send money, gift cards, or crypto to someone you haven’t met and verified.", "Romance scams often escalate emotional pressure into transfers.", ["NFCC_NSRC_997"]),
            act("Watch for secrecy, urgency, and requests to move chat off-platform.", "Isolation tactics reduce your ability to verify.", ["NFCC_NSRC_997"]),
        ]
        next_steps = [
            act("Talk to a trusted friend/family member before taking action.", "A second opinion helps reduce manipulation risk.", ["NFCC_NSRC_997"]),
            act("If money moved, call NSRC 997 and contact your bank immediately.", "Time is critical.", ["NFCC_NSRC_997"]),
        ]

    elif scenario_norm == "impersonation":
        do_now = [
            act("Do not trust caller ID or WhatsApp profile photos. Verify using official numbers from official websites.", "Impersonation relies on spoofing and fake identities.", ["NFCC_NSRC_997"]),
            act("Do not share OTP/TAC/passwords or approve unknown transactions.", "Account takeover can happen fast.", ["NFCC_NSRC_997"]),
        ]
        next_steps = [
            act("If money moved, call NSRC 997 and contact your bank immediately.", "Early action helps.", ["NFCC_NSRC_997"]),
            act("If needed, report via official PDRM channels.", "Supports investigation.", ["PDRM_CCID_EREPORT"]),
        ]

    elif scenario_norm == "asked_to_pay":
        do_now = [
            act("Pause before paying. Don’t be rushed by urgency or threats.", "Urgency is a common scam pressure tactic.", ["NFCC_NSRC_997"]),
            act("Verify the request using official channels (official site / official hotline), not numbers in the message.", "Prevents being routed to fake ‘support’.", ["NFCC_NSRC_997"]),
        ]
        next_steps = [
            act("If you already paid, treat it as money moved and call NSRC 997.", "Early reporting matters.", ["NFCC_NSRC_997"]),
        ]

    else:
        do_now = [
            act("Stop engaging and do not follow instructions from the other party (no links, no QR scans, no app installs).", "Urgency tactics can push you to act before verifying.", ["NFCC_NSRC_997"]),
            act("If money moved, contact your bank immediately and call NSRC 997 right away.", "Speed matters.", ["NFCC_NSRC_997"]),
        ]
        next_steps = [
            act("Preserve evidence and seek clarification via official channels in Resources tab.", "Official channels can advise the right path.", ["NFCC_NSRC_997", "MCMC_ADUAN"]),
        ]

    result = {
        "scenario": scenario_norm,
        "when": when_map.get(scenario_norm, "Immediately"),
        "do_this_now": do_now,
        "next_steps": next_steps,
        "who_to_contact": contacts,
        "evidence_to_save": evidence,
        "sources": [x.model_dump() for x in srcs],
        "caveat": (
            "This is informational guidance and may be incomplete. It is not an official finding. "
            "Avoid sharing identifiable details publicly. If money has moved, contact your bank and call NSRC 997 immediately."
        ),
    }

    return {"result": result}


@app.post("/analyze")
def analyze(payload: AnalyzeIn):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    if OpenAI is None:
        raise HTTPException(status_code=500, detail="openai package not installed")

    img = payload.image_data_url
    if not img.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data_url must be a data:image/... base64 URL")

    srcs = official_sources()

    client = openai_client()

    try:
        # Vision input: attach image to the user message
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": system_prompt()},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_user_prompt(payload.lang)},
                        {"type": "image_url", "image_url": {"url": img}},
                    ],
                },
            ],
        )

        text = (resp.choices[0].message.content or "").strip()
        obj = extract_json(text)
        obj = ensure_minimum_fields(obj, srcs)

        # Validate structure
        result = VerifyResult(**obj).model_dump()

        return {"result": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {str(e)}")
