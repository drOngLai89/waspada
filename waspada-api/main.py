import os
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from openai import OpenAI

log = logging.getLogger("waspada-api")
logging.basicConfig(level=logging.INFO)

APP_NAME = "Waspada API"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Official sources (Malaysia) ---
# NOTE: We attach these to outputs via source_ids, and also expose them via /resources.
# Load-bearing official references:
# - NFCC / NSRC 997: :contentReference[oaicite:0]{index=0}
# - PDRM Semak Mule & CCID reporting guidance: :contentReference[oaicite:1]{index=1}
# - BNM Financial Consumer Alert: :contentReference[oaicite:2]{index=2}
# - SC Investor Alert List: 
# - CyberSecurity Malaysia Cyber999 portal: :contentReference[oaicite:4]{index=4}

LAST_VERIFIED = os.getenv("WASPADA_SOURCES_LAST_VERIFIED", "2026-01-08")

SOURCES: Dict[str, Dict[str, str]] = {
    "NFCC_NSRC_997": {
        "title": "National Scam Response Centre (NSRC) – 997",
        "org": "National Fraud Control Centre (NFCC), Prime Minister’s Department",
        "url": "https://nfcc.jpm.gov.my/",
        "notes": "NSRC hotline for scam/fraud cases where funds may have moved. Reference the NSRC page on NFCC site.",
        "last_verified": LAST_VERIFIED,
    },
    "PDRM_SEMAKMULE": {
        "title": "Semak Mule (Account/Phone Checking)",
        "org": "Royal Malaysia Police (PDRM)",
        "url": "https://ccid.rmp.gov.my/semakmule",
        "notes": "PDRM CCID page referencing Semak Mule portal and related checks.",
        "last_verified": LAST_VERIFIED,
    },
    "PDRM_CCID_EREPORT": {
        "title": "PDRM CCID e-Reporting (Commercial Crime)",
        "org": "Royal Malaysia Police (PDRM)",
        "url": "https://ereporting.rmp.gov.my/",
        "notes": "Official PDRM online reporting portal guidance referenced by PDRM CCID pages.",
        "last_verified": LAST_VERIFIED,
    },
    "BNM_FCA": {
        "title": "Financial Consumer Alert",
        "org": "Bank Negara Malaysia (BNM)",
        "url": "https://www.bnm.gov.my/financial-consumer-alert",
        "notes": "List of entities/alerts for consumer protection (check before investing/transferring).",
        "last_verified": LAST_VERIFIED,
    },
    "SC_INVESTOR_ALERT": {
        "title": "Investor Alert List",
        "org": "Securities Commission Malaysia (SC)",
        "url": "https://www.sc.com.my/investor-alert-list",
        "notes": "Investor Alert List for suspicious/unlicensed investment offers.",
        "last_verified": LAST_VERIFIED,
    },
    "CSM_CYBER999": {
        "title": "Cyber999 Incident Reporting",
        "org": "CyberSecurity Malaysia",
        "url": "https://www.mycert.org.my/portal/advisory?id=CYBER999_20230919112452",
        "notes": "Cyber999 reporting info (phishing, malware, online abuse).",
        "last_verified": LAST_VERIFIED,
    },
}

# --- API models ---
class AnalyzeIn(BaseModel):
    image_data_url: str = Field(..., description="data:image/...;base64,...")
    lang: Optional[str] = "EN"

class SourceOut(BaseModel):
    id: str
    title: str
    org: str
    url: str
    notes: str
    last_verified: str

class ContactOut(BaseModel):
    name: str
    type: str  # phone|url|email
    value: str
    notes: str = ""
    source_ids: List[str] = []

class ActionOut(BaseModel):
    step: str
    why: str = ""
    source_ids: List[str] = []

class AnalyzeOut(BaseModel):
    out_of_scope: bool = False
    malaysia_relevance: str
    scenario: str
    verdict: str
    risk: str
    what_the_screenshot_shows: List[str]
    analysis: str
    findings: List[str] = []
    recommended_next_actions: List[ActionOut] = []
    who_to_contact: List[ContactOut] = []
    evidence_to_save: List[str] = []
    caveat: str
    sources: List[SourceOut] = []

class ResourceCategoryOut(BaseModel):
    id: str
    title: str
    items: List[SourceOut]

class ResourcesOut(BaseModel):
    last_verified: str
    categories: List[ResourceCategoryOut]


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY on server.")
    return OpenAI(api_key=key)


def _pick_sources(ids: List[str]) -> List[SourceOut]:
    out: List[SourceOut] = []
    seen = set()
    for sid in ids:
        if sid in SOURCES and sid not in seen:
            s = SOURCES[sid]
            out.append(SourceOut(
                id=sid,
                title=s["title"],
                org=s["org"],
                url=s["url"],
                notes=s.get("notes", ""),
                last_verified=s.get("last_verified", LAST_VERIFIED),
            ))
            seen.add(sid)
    return out


def _ensure_nonempty_list(v: Any, fallback: str) -> List[str]:
    if isinstance(v, list):
        cleaned = [str(x).strip() for x in v if str(x).strip()]
        if cleaned:
            return cleaned
    return [fallback]


def _json_mode_prompt() -> str:
    # Keep it very practical + Malaysia-first.
    # We also force the model to populate 'what_the_screenshot_shows' with at least 3 bullets,
    # or explicitly say it cannot reliably read.
    return f"""
You are Waspada, a Malaysia-first anti-scam assistant.

Your job:
1) Interpret what is visible in the screenshot (messages, bank/payment UI, URLs, names, amounts, threats).
2) Decide a scenario category and risk.
3) Give Malaysia-specific next actions aligned to OFFICIAL Malaysia resources.
4) Provide who to contact in Malaysia (hotlines / official sites) and cite them using source_ids.

STRICT RULES:
- Malaysia-only. If the screenshot has no Malaysia context, set out_of_scope=true and explain briefly.
- NEVER claim certainty. Be careful. No legal or medical claims.
- Always include a caveat: AI-generated guidance, may be wrong/incomplete, refer to bank/PDRM/authorities.
- Always output valid JSON matching the schema. No markdown.

Allowed scenario values:
MONEY_MOVED, ASKED_TO_PAY, OTP_PASSWORD, COURIER, INVESTMENT, JOB, ROMANCE, IMPERSONATION, OTHER, OUT_OF_SCOPE

Verdict values:
LIKELY_SCAM, SUSPICIOUS, UNCLEAR, LIKELY_SAFE, OUT_OF_SCOPE

Risk values:
LOW, MEDIUM, HIGH

OFFICIAL SOURCES (use these IDs in source_ids when relevant):
- NFCC_NSRC_997 (NSRC 997)
- PDRM_SEMAKMULE (Semak Mule)
- PDRM_CCID_EREPORT (PDRM e-Reporting)
- BNM_FCA (BNM Financial Consumer Alert)
- SC_INVESTOR_ALERT (SC Investor Alert List)
- CSM_CYBER999 (Cyber999)

Output JSON schema:
{{
  "out_of_scope": boolean,
  "malaysia_relevance": string,
  "scenario": string,
  "verdict": string,
  "risk": string,

  "what_the_screenshot_shows": [string, ...],   // MUST NOT be empty. Aim 3-6 bullets.
  "analysis": string,                            // short paragraph
  "findings": [string, ...],                     // 3-8 key red flags / observations

  "recommended_next_actions": [
    {{
      "step": string,                            // action step (imperative)
      "why": string,                             // short reason
      "source_ids": [string, ...]                // from official sources above
    }}
  ],

  "who_to_contact": [
    {{
      "name": string,
      "type": "phone"|"url"|"email",
      "value": string,
      "notes": string,
      "source_ids": [string, ...]
    }}
  ],

  "evidence_to_save": [string, ...],

  "caveat": string,
  "source_ids_used": [string, ...]               // list all official ids you relied on
}}

If you cannot read text clearly:
- Put a bullet in what_the_screenshot_shows: "Couldn’t reliably read the text; retake a clearer screenshot (full message, no blur)."
- Still infer scenario if possible from visible context, otherwise OUT_OF_SCOPE.
""".strip()


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/version")
def version():
    return {
        "name": APP_NAME,
        "model": MODEL,
        "has_key": bool(os.getenv("OPENAI_API_KEY")),
        "sources_last_verified": LAST_VERIFIED,
    }


@app.get("/resources", response_model=ResourcesOut)
def resources():
    # Curated categories so the Resources tab is actually useful.
    categories = [
        ResourceCategoryOut(
            id="urgent_money",
            title="Urgent (money moved / bank transfer)",
            items=_pick_sources(["NFCC_NSRC_997", "PDRM_CCID_EREPORT"]),
        ),
        ResourceCategoryOut(
            id="check_before_pay",
            title="Check before you pay (accounts / investment offers)",
            items=_pick_sources(["PDRM_SEMAKMULE", "BNM_FCA", "SC_INVESTOR_ALERT"]),
        ),
        ResourceCategoryOut(
            id="cyber_phishing",
            title="Phishing / malware / online abuse reporting",
            items=_pick_sources(["CSM_CYBER999"]),
        ),
        ResourceCategoryOut(
            id="police_reporting",
            title="Police reporting & references",
            items=_pick_sources(["PDRM_CCID_EREPORT", "PDRM_SEMAKMULE"]),
        ),
    ]
    return ResourcesOut(last_verified=LAST_VERIFIED, categories=categories)


@app.post("/analyze")
def analyze(payload: AnalyzeIn):
    try:
        if not payload.image_data_url.startswith("data:image/"):
            raise HTTPException(status_code=400, detail="image_data_url must be a data:image/... base64 URL")

        client = _client()
        system = _json_mode_prompt()

        # Vision: include the image as image_url in chat.completions
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Language hint: {payload.lang or 'EN'}"},
                    {"type": "image_url", "image_url": {"url": payload.image_data_url}},
                    {"type": "text", "text": "Analyse this screenshot for Malaysia scam risk and next actions."},
                ],
            },
        ]

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=1200,
        )

        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)

        # Normalize + enforce critical fields
        out_of_scope = bool(data.get("out_of_scope", False))
        scenario = str(data.get("scenario", "OTHER")).strip() or "OTHER"
        verdict = str(data.get("verdict", "UNCLEAR")).strip() or "UNCLEAR"
        risk = str(data.get("risk", "LOW")).strip() or "LOW"

        malaysia_relevance = str(data.get("malaysia_relevance", "")).strip()
        if not malaysia_relevance:
            malaysia_relevance = "Malaysia relevance not clear from the screenshot."

        what_shows = _ensure_nonempty_list(
            data.get("what_the_screenshot_shows"),
            "Couldn’t reliably read the text; retake a clearer screenshot (full message visible, no blur).",
        )

        analysis = str(data.get("analysis", "")).strip()
        if not analysis:
            analysis = "Based on what is visible, this may involve a scam pattern. Follow Malaysia-first safety steps below."

        findings = data.get("findings", [])
        if not isinstance(findings, list):
            findings = []
        findings = [str(x).strip() for x in findings if str(x).strip()]

        # recommended_next_actions objects
        rna = data.get("recommended_next_actions", [])
        actions: List[ActionOut] = []
        used_source_ids: List[str] = []

        if isinstance(rna, list):
            for item in rna[:12]:
                if not isinstance(item, dict):
                    continue
                step = str(item.get("step", "")).strip()
                why = str(item.get("why", "")).strip()
                sids = item.get("source_ids", [])
                if not isinstance(sids, list):
                    sids = []
                sids = [str(s).strip() for s in sids if str(s).strip()]
                if step:
                    actions.append(ActionOut(step=step, why=why, source_ids=sids))
                    used_source_ids.extend(sids)

        # who_to_contact objects
        wtc = data.get("who_to_contact", [])
        contacts: List[ContactOut] = []
        if isinstance(wtc, list):
            for item in wtc[:10]:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                typ = str(item.get("type", "")).strip()
                val = str(item.get("value", "")).strip()
                notes = str(item.get("notes", "")).strip()
                sids = item.get("source_ids", [])
                if not isinstance(sids, list):
                    sids = []
                sids = [str(s).strip() for s in sids if str(s).strip()]
                if name and typ and val:
                    contacts.append(ContactOut(name=name, type=typ, value=val, notes=notes, source_ids=sids))
                    used_source_ids.extend(sids)

        evidence = data.get("evidence_to_save", [])
        if not isinstance(evidence, list):
            evidence = []
        evidence = [str(x).strip() for x in evidence if str(x).strip()]

        caveat = str(data.get("caveat", "")).strip()
        if not caveat:
            caveat = (
                "This is AI-generated guidance based on the screenshot and may be wrong or incomplete. "
                "For urgent cases (especially if money moved), contact your bank and the relevant Malaysian authorities."
            )

        # If out_of_scope, ensure we still push Malaysia-first guidance
        if out_of_scope:
            # Add a small default action + contacts based on official sources
            if not actions:
                actions = [
                    ActionOut(
                        step="If you suspect a scam or money has moved, contact your bank immediately and call NSRC 997.",
                        why="Fast action can improve the chances of stopping transfers.",
                        source_ids=["NFCC_NSRC_997"],
                    )
                ]
                used_source_ids.append("NFCC_NSRC_997")

        # Final sources list for UI
        used_source_ids = [s for s in used_source_ids if s in SOURCES]
        sources = _pick_sources(used_source_ids)

        result = AnalyzeOut(
            out_of_scope=out_of_scope,
            malaysia_relevance=malaysia_relevance,
            scenario=scenario,
            verdict=verdict,
            risk=risk,
            what_the_screenshot_shows=what_shows,
            analysis=analysis,
            findings=findings,
            recommended_next_actions=actions,
            who_to_contact=contacts,
            evidence_to_save=evidence,
            caveat=caveat,
            sources=sources,
        )

        return {"result": result.model_dump()}

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        log.exception("Analyze failed: %s", msg)
        low = msg.lower()
        if "invalid_api_key" in low or "incorrect api key" in low or "401" in low:
            raise HTTPException(status_code=500, detail="Auth failed. Check OPENAI_API_KEY on Render and redeploy.")
        if "rate limit" in low or "429" in low:
            raise HTTPException(status_code=503, detail="AI is rate-limited. Try again in a minute.")
        if "timeout" in low:
            raise HTTPException(status_code=504, detail="AI timed out. Try again.")
        raise HTTPException(status_code=502, detail=f"AI service error: {msg}")
