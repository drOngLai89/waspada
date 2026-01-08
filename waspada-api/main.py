import os
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("waspada-api")

app = FastAPI(title="Waspada API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Official Malaysia resources (keep short, linkable) ---
OFFICIAL_RESOURCES: List[Dict[str, str]] = [
    {
        "name": "NSRC (National Scam Response Centre)",
        "type": "phone",
        "value": "997",
        "notes": "Malaysia. If money has moved or banking fraud is in progress. Call immediately."
    },
    {
        "name": "PDRM Semak Mule",
        "type": "url",
        "value": "https://semakmule.rmp.gov.my/",
        "notes": "Malaysia. Check suspected phone/bank account links to mule accounts."
    },
    {
        "name": "CyberSecurity Malaysia (Cyber999)",
        "type": "url",
        "value": "https://www.mycert.org.my/cyber999/",
        "notes": "Malaysia. Cyber incident reporting guidance."
    },
]

SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "MONEY_MOVED": {
        "title": "Money already moved",
        "steps": [
            "Call your bank’s fraud hotline now and tell them it’s an active scam case.",
            "Call NSRC 997 immediately (Malaysia). Ask for fund tracing / recall guidance.",
            "Make a police report as soon as possible and keep all evidence."
        ],
        "evidence": [
            "Screenshots of chat/SMS/WhatsApp",
            "Bank transfer receipt / reference number",
            "Phone numbers, account numbers, names used",
            "Any links / QR codes / payment instructions"
        ],
    },
    "OTP_PASSWORD": {
        "title": "OTP / password requested",
        "steps": [
            "Do not share OTP/TAC codes or passwords. Stop replying.",
            "If you entered credentials, change passwords immediately and enable 2FA.",
            "Call your bank to flag potential account takeover."
        ],
        "evidence": ["Screenshots of the request", "Caller ID / profile / link used"],
    },
    "COURIER": {
        "title": "Courier / parcel / “customs” scam",
        "steps": [
            "Do not pay ‘release fees’ via unknown links.",
            "Verify using official courier channels (not numbers in the message).",
            "If pressured, stop engagement and keep evidence."
        ],
        "evidence": ["SMS/WhatsApp screenshot", "Tracking number shown", "Payment link"],
    },
    "IMPERSONATION": {
        "title": "Government / police impersonation",
        "steps": [
            "Hang up. Do not stay on the line.",
            "Never transfer money to ‘safe accounts’.",
            "Verify using official numbers from official websites only."
        ],
        "evidence": ["Call time/log", "Numbers used", "Any ‘case ID’ given", "Screenshots"],
    },
    "INVESTMENT": {
        "title": "Investment / high return pitch",
        "steps": [
            "Be cautious of guaranteed returns and urgency tactics.",
            "Do not install unknown apps or allow remote access.",
            "If you already paid, treat it as MONEY_MOVED and act immediately."
        ],
        "evidence": ["Promo messages", "Account details", "App name/link", "Receipts"],
    },
    "OTHER": {
        "title": "General suspicious message",
        "steps": [
            "Do not click links or scan unknown QR codes.",
            "Verify via official channels. Keep evidence.",
            "If money moved, switch to MONEY_MOVED steps."
        ],
        "evidence": ["Screenshot", "Link/QR", "Phone/account details"],
    }
}

# --------- Models ----------
class AnalyzeRequest(BaseModel):
    image_data_url: str = Field(..., description="data:image/...;base64,...")
    lang: str = Field("EN", description="EN | MS | ZH | TA")

class ActionPlanRequest(BaseModel):
    scenario: str = Field(..., description="MONEY_MOVED | OTP_PASSWORD | COURIER | INVESTMENT | IMPERSONATION | OTHER")
    lang: str = Field("EN")

class VersionResponse(BaseModel):
    ok: bool
    service: str = "waspada-api"
    has_key: bool
    model: str

@app.get("/version", response_model=VersionResponse)
def version():
    return VersionResponse(ok=True, has_key=bool(OPENAI_API_KEY), model=OPENAI_MODEL)

@app.get("/resources")
def resources():
    return {"ok": True, "resources": OFFICIAL_RESOURCES}

@app.post("/action-plan")
def action_plan(req: ActionPlanRequest):
    scenario = (req.scenario or "OTHER").upper().strip()
    preset = SCENARIO_PRESETS.get(scenario, SCENARIO_PRESETS["OTHER"])
    return {
        "ok": True,
        "scenario": scenario,
        "title": preset["title"],
        "steps": preset["steps"],
        "evidence_to_save": preset["evidence"],
        "disclaimer": (
            "This is general guidance for Malaysia only. "
            "It is not official advice, not legal advice, and may be incomplete. "
            "For urgent or high-risk situations, contact your bank and the relevant authorities."
        ),
        "official_resources": OFFICIAL_RESOURCES,
    }

def _safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        # last-resort: try to extract a JSON object block
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end+1])
        raise

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY on server.")

    data_url = req.image_data_url
    lang = (req.lang or "EN").upper().strip()

    system = (
        "You are Waspada, a Malaysia-focused anti-scam assistant.\n"
        "You must return ONLY valid JSON (no markdown, no extra text).\n"
        "If the content is not related to Malaysia scam safety, set out_of_scope=true.\n"
        "Never invent phone numbers or government programmes. Use only the provided official resources list.\n"
        "Keep output concise and actionable."
    )

    resources_text = "\n".join([f"- {r['name']}: {r['type']} {r['value']} ({r.get('notes','')})" for r in OFFICIAL_RESOURCES])

    user = (
        f"Language: {lang}\n"
        f"Official Malaysia resources you MAY reference:\n{resources_text}\n\n"
        "Task:\n"
        "1) Interpret what the screenshot shows (short).\n"
        "2) Decide if it is Malaysia-relevant scam content.\n"
        "3) Give a clear verdict + risk level.\n"
        "4) Provide next actions (bullets) and who to contact (choose from official resources).\n"
        "5) Provide evidence to save.\n"
        "6) Provide a clear caveat/disclaimer that this is AI-generated guidance and not official diagnostics.\n\n"
        "Return JSON with keys:\n"
        "lang, out_of_scope, malaysia_relevance, scenario, verdict, risk, summary,\n"
        "what_the_screenshot_suggests, key_red_flags (array), what_to_do_next (array),\n"
        "who_to_contact (array of {name,type,value,notes}), evidence_to_save (array),\n"
        "message_you_can_copy, disclaimer, official_resources (array)\n"
    )

    try:
        # Use Chat Completions (works broadly; avoids responses.create response_format issues)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            temperature=0.2,
            max_tokens=900,
        )

        text = resp.choices[0].message.content or "{}"
        data = _safe_json_loads(text)

        # Always attach official resources for UI rendering
        data["official_resources"] = OFFICIAL_RESOURCES

        # Defensive defaults
        data.setdefault("lang", lang)
        data.setdefault("out_of_scope", False)
        data.setdefault("risk", "UNKNOWN")
        data.setdefault("verdict", "UNKNOWN")
        data.setdefault("scenario", "OTHER")
        data.setdefault("summary", "")
        data.setdefault("what_to_do_next", [])
        data.setdefault("who_to_contact", [])
        data.setdefault("evidence_to_save", [])
        data.setdefault("disclaimer", "This is AI-generated guidance and may be wrong or incomplete. For urgent cases, contact your bank and the relevant authorities.")

        return {"result": data}

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
