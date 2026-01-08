import os
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("waspada-api")

app = FastAPI(title="Waspada API", version="2026.01.08")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# --- Official references (public, Malaysia) ---
# NOTE: These URLs can change; we expose "last_checked" so you can refresh later.
SOURCES_LAST_CHECKED = "2026-01-08"

SOURCES = [
    {
        "id": "PDRM_NSRC_997",
        "name": "PDRM – National Scam Response Centre (NSRC) 997",
        "url": "https://www.rmp.gov.my/orang-awam/jabatan-siasatan-jenayah-komersil/national-scam-response-centre-(nsrc)",
        "last_checked": SOURCES_LAST_CHECKED,
    },
    {
        "id": "PDRM_SCAM_INFO_03",
        "name": "PDRM JSJK – Scam info (incl. Semak Mule / CCID contact)",
        "url": "https://www.rmp.gov.my/news-detail/2024/06/03/pdrm-giat-jalankan-operasi-banteras-scam",
        "last_checked": SOURCES_LAST_CHECKED,
    },
    {
        "id": "PDRM_SCAM_INFO_19",
        "name": "PDRM JSJK – Scam prevention tips / enforcement updates",
        "url": "https://www.rmp.gov.my/news-detail/2024/06/19/pdrm-giat-jalankan-operasi-banteras-scam",
        "last_checked": SOURCES_LAST_CHECKED,
    },
    {
        "id": "CSM_CYBER999_ADVISORY",
        "name": "CyberSecurity Malaysia (Cyber999) – Scam / phishing advisory",
        "url": "https://www.cybersecurity.my/portal-main/advisories-details/dc8402e8-b9f7-11f0-b161-0050568ccc16",
        "last_checked": SOURCES_LAST_CHECKED,
    },
    {
        "id": "MYCERT_CYBER999",
        "name": "MyCERT – Cyber999 services information",
        "url": "https://mycert.org.my/portal/advisories?id=fb834148-452a-44d2-858b-7f5c64611d22&month=2025-08&page=2&per-page=10",
        "last_checked": SOURCES_LAST_CHECKED,
    },
]

# --- Scenarios used by the app ---
SCENARIOS = [
    "MONEY_MOVED",
    "ASKED_TO_PAY",
    "OTP_PASSWORD",
    "COURIER",
    "INVESTMENT",
    "JOB",
    "ROMANCE",
    "IMPERSONATION",
    "OTHER",
]

# --- Toolkit action plans (non-AI) shown in-app, each step includes citations ---
# Keep this concise; AI can expand in Verify, but Toolkit must be practical + scannable.
ACTION_PLANS: Dict[str, Dict[str, Any]] = {
    "MONEY_MOVED": {
        "title": "Money already moved",
        "when": "Immediately (time matters).",
        "steps": [
            {"text": "Call NSRC 997 straight away and follow their instructions.", "sources": ["PDRM_NSRC_997"]},
            {"text": "Call your bank’s hotline to freeze/flag the transfer if possible.", "sources": ["PDRM_NSRC_997"]},
            {"text": "Save evidence (screenshots, chat logs, receipts, account numbers, phone numbers).", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "Make a police report (JSJK/CCID) and provide the evidence.", "sources": ["PDRM_SCAM_INFO_03", "PDRM_SCAM_INFO_19"]},
        ],
    },
    "ASKED_TO_PAY": {
        "title": "Asked to pay / urgent payment request",
        "when": "Before paying anything.",
        "steps": [
            {"text": "Stop. Don’t transfer to ‘safe accounts’ or pay to ‘unlock’/‘recover’ money.", "sources": ["PDRM_SCAM_INFO_19"]},
            {"text": "Verify using official numbers from official websites (not numbers given by the caller/message).", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "If pressured or threatened, treat it as a red flag and contact authorities for advice.", "sources": ["PDRM_SCAM_INFO_03"]},
        ],
    },
    "OTP_PASSWORD": {
        "title": "OTP / password / TAC requested",
        "when": "Immediately.",
        "steps": [
            {"text": "Do not share OTP/TAC/passwords. End the conversation.", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "Change banking/email passwords if you clicked a link or entered credentials.", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "Call your bank hotline and ask to secure your account.", "sources": ["CSM_CYBER999_ADVISORY", "PDRM_NSRC_997"]},
        ],
    },
    "COURIER": {
        "title": "Courier / parcel / customs scam",
        "when": "Before paying any ‘fee’.",
        "steps": [
            {"text": "Don’t pay fees via links or unknown accounts. Verify via official channels.", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "Save the message and numbers; report if harassment/pressure continues.", "sources": ["PDRM_SCAM_INFO_03"]},
        ],
    },
    "INVESTMENT": {
        "title": "Investment / high-return pitch",
        "when": "Before sending any funds.",
        "steps": [
            {"text": "Be cautious of guaranteed returns, urgency, or moving chat to private channels.", "sources": ["PDRM_SCAM_INFO_19"]},
            {"text": "Do not transfer to personal accounts or unknown crypto wallets.", "sources": ["PDRM_SCAM_INFO_19"]},
            {"text": "If funds already moved, follow ‘Money already moved’ steps (NSRC 997).", "sources": ["PDRM_NSRC_997"]},
        ],
    },
    "JOB": {
        "title": "Job offer / work-from-home scam",
        "when": "Before paying ‘processing’ fees.",
        "steps": [
            {"text": "Avoid paying upfront fees for jobs. Verify company details independently.", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "Do not share sensitive documents unless you can verify the employer.", "sources": ["CSM_CYBER999_ADVISORY"]},
        ],
    },
    "ROMANCE": {
        "title": "Romance / love scam",
        "when": "Before sending money or gifts.",
        "steps": [
            {"text": "Do not send money/crypto/gift cards to someone you have not verified.", "sources": ["PDRM_SCAM_INFO_19"]},
            {"text": "Watch for emotional pressure, secrecy, emergencies, or ‘customs/parcel’ stories.", "sources": ["PDRM_SCAM_INFO_19"]},
            {"text": "Save evidence and speak to someone you trust before acting.", "sources": ["CSM_CYBER999_ADVISORY"]},
        ],
    },
    "IMPERSONATION": {
        "title": "Impersonation (police/bank/government)",
        "when": "Immediately.",
        "steps": [
            {"text": "Hang up / stop responding. Don’t stay on the line.", "sources": ["PDRM_SCAM_INFO_19"]},
            {"text": "Do not transfer to ‘safe accounts’. Verify via official numbers from official sites.", "sources": ["PDRM_SCAM_INFO_19", "CSM_CYBER999_ADVISORY"]},
            {"text": "If you already transferred money, call NSRC 997 now.", "sources": ["PDRM_NSRC_997"]},
        ],
    },
    "OTHER": {
        "title": "Other / unsure",
        "when": "If you feel pressured or uncertain.",
        "steps": [
            {"text": "Pause. Avoid sending money or personal details.", "sources": ["CSM_CYBER999_ADVISORY"]},
            {"text": "Save evidence and contact NSRC 997 if money moved or risk is high.", "sources": ["PDRM_NSRC_997"]},
        ],
    },
}


class AnalyzeRequest(BaseModel):
    image_data_url: str = Field(..., description="data:image/jpeg;base64,...")
    # Keep lang optional in API so old clients don't break; app UI no longer shows language selector.
    lang: Optional[str] = "EN"


@app.get("/version")
def version():
    return {
        "ok": True,
        "service": "waspada-api",
        "model": OPENAI_MODEL,
        "has_key": bool(OPENAI_API_KEY),
        "sources_last_checked": SOURCES_LAST_CHECKED,
    }


@app.get("/resources")
def resources():
    # App uses this to show official contacts / links
    return {
        "ok": True,
        "sources_last_checked": SOURCES_LAST_CHECKED,
        "official_sources": SOURCES,
        "hotlines": [
            {"name": "NSRC", "phone": "997", "notes": "For suspected scam / funds moved (Malaysia).", "sources": ["PDRM_NSRC_997"]},
        ],
    }


@app.get("/action-plan")
def action_plan(scenario: str):
    sc = scenario.strip().upper()
    if sc not in ACTION_PLANS:
        raise HTTPException(status_code=400, detail="Unknown scenario.")
    plan = ACTION_PLANS[sc]
    return {
        "ok": True,
        "scenario": sc,
        "plan": plan,
        "sources_last_checked": SOURCES_LAST_CHECKED,
        "official_sources": SOURCES,
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Server missing OPENAI_API_KEY.")

    img = req.image_data_url
    if not (img.startswith("data:image/")):
        raise HTTPException(status_code=400, detail="image_data_url must be a data:image/... URL")

    # Strict JSON schema expected from the model
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "out_of_scope": {"type": "boolean"},
            "malaysia_relevance": {"type": "string"},
            "scenario": {"type": "string", "enum": SCENARIOS},
            "verdict": {"type": "string", "enum": ["LIKELY_SAFE", "SUSPICIOUS", "HIGH_RISK", "UNKNOWN"]},
            "risk": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]},
            "observations": {"type": "array", "items": {"type": "string"}},
            "analysis": {"type": "string"},
            "recommended_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "step": {"type": "string"},
                        "why": {"type": "string"},
                        "source_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["step", "why", "source_ids"],
                },
            },
            "who_to_contact": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["phone", "url", "note"]},
                        "value": {"type": "string"},
                        "notes": {"type": "string"},
                        "source_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "type", "value", "notes", "source_ids"],
                },
            },
            "evidence_to_save": {"type": "array", "items": {"type": "string"}},
            "message_you_can_copy": {"type": "string"},
            "caveat": {"type": "string"},
            "references": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "source_id": {"type": "string"},
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                        "last_checked": {"type": "string"},
                    },
                    "required": ["source_id", "name", "url", "last_checked"],
                },
            },
        },
        "required": [
            "out_of_scope",
            "malaysia_relevance",
            "scenario",
            "verdict",
            "risk",
            "observations",
            "analysis",
            "recommended_actions",
            "who_to_contact",
            "evidence_to_save",
            "message_you_can_copy",
            "caveat",
            "references",
        ],
    }

    sources_json = json.dumps(SOURCES, ensure_ascii=False)
    plans_json = json.dumps(ACTION_PLANS, ensure_ascii=False)

    system = (
        "You are Waspada, a Malaysia-focused anti-scam assistant.\n"
        "Your job: interpret the screenshot content and recommend next steps.\n\n"
        "Hard rules:\n"
        "1) Malaysia-first. If the screenshot has no Malaysia context, set out_of_scope=true.\n"
        "2) Use ONLY the provided OFFICIAL SOURCES and ACTION PLANS. Do not invent numbers, agencies, laws, or URLs.\n"
        "3) If unsure, be explicit and choose verdict/risk UNKNOWN rather than guessing.\n"
        "4) Every recommended action MUST include source_ids from the provided sources.\n"
        "5) Always include a clear caveat that this is AI-generated guidance, may be wrong/incomplete, and users should contact authorities/banks/police for final action.\n"
    )

    user = (
        "OFFICIAL_SOURCES (use only these):\n"
        f"{sources_json}\n\n"
        "ACTION_PLANS (use these for actions, but tailor to the screenshot):\n"
        f"{plans_json}\n\n"
        "TASK:\n"
        "- Read the screenshot.\n"
        "- Decide if it is Malaysia scam-related.\n"
        "- Choose the best scenario.\n"
        "- Provide observations + analysis.\n"
        "- Provide recommended_actions (practical, short) with citations.\n"
        "- Provide who_to_contact (NSRC 997 at minimum when high risk / money moved).\n"
        "- Provide evidence_to_save + message_you_can_copy.\n"
        "- Provide references array listing only sources you used.\n"
    )

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            max_tokens=900,
            response_format={"type": "json_schema", "json_schema": {"name": "waspada_analyze", "schema": schema}},
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user},
                        {"type": "image_url", "image_url": {"url": img}},
                    ],
                },
            ],
        )

        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)

        # Ensure references are populated with full source objects
        used_ids = {r.get("source_id") for r in data.get("references", []) if isinstance(r, dict)}
        if not used_ids:
            # Backfill from recommended actions if model forgot
            for a in data.get("recommended_actions", []):
                for sid in a.get("source_ids", []):
                    used_ids.add(sid)
        refs = []
        for s in SOURCES:
            if s["id"] in used_ids:
                refs.append({"source_id": s["id"], "name": s["name"], "url": s["url"], "last_checked": s["last_checked"]})
        data["references"] = refs

        return {
            "result": data,
            "sources_last_checked": SOURCES_LAST_CHECKED,
        }

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
