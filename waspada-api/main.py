import os
import json
import re
import base64
import logging
from typing import Optional, Literal, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openai import OpenAI

# ----------------------------
# App setup
# ----------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("waspada-api")

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "45"))

client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)

Lang = Literal["EN", "MS", "ZH", "TA"]

# ----------------------------
# Request/Response models
# ----------------------------
class AnalyzeRequest(BaseModel):
    # Optional screenshot. We keep this optional so Waspada is NOT "just a screenshot scanner".
    image_data_url: Optional[str] = Field(
        default=None,
        description="data:image/jpeg;base64,... (optional)"
    )
    lang: Lang = "EN"

    # New: user context fields that make Waspada a Malaysia scam ACTION app
    scenario: Optional[str] = Field(
        default=None,
        description="User-selected scenario: e.g., 'bank_transfer', 'otp_tac', 'courier_scam', 'investment', 'job_scam', 'loan_scam', 'romance', 'ecommerce', etc."
    )
    channel: Optional[str] = Field(
        default=None,
        description="Where it happened: WhatsApp/Telegram/SMS/Facebook/Call/Email/Website/etc."
    )
    notes: Optional[str] = Field(
        default=None,
        description="What the user wants you to know (short)."
    )

class AnalyzeResponse(BaseModel):
    lang: Lang
    out_of_scope: bool
    malaysia_relevance: str

    risk: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    verdict: str
    summary: str

    what_we_used: List[str]  # e.g. ["screenshot", "notes"]
    what_ai_saw: List[str]
    red_flags: List[str]

    next_actions: List[Dict[str, Any]]
    who_to_contact: List[Dict[str, str]]

    disclaimer: str

# ----------------------------
# Helpers
# ----------------------------
def _safe_trim(s: Optional[str], max_len: int) -> Optional[str]:
    if not s:
        return s
    s = s.strip()
    return s[:max_len]

def _validate_data_url(data_url: str) -> str:
    """
    Accepts data:image/...;base64,...
    We do NOT decode to bytes for OCR. We only do sanity checks and send to OpenAI as an image input.
    """
    if not data_url.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data_url must start with data:image/...")

    if ";base64," not in data_url:
        raise HTTPException(status_code=400, detail="image_data_url must be base64 encoded (data:image/...;base64,...)")

    # basic size guard (prevents 5MB+ payloads destroying latency)
    # data_url length is a rough proxy; 2,500,000 chars ~ ~1.8MB base64-ish depending on content
    if len(data_url) > 2_500_000:
        raise HTTPException(status_code=413, detail="Screenshot is too large. Please pick a smaller screenshot or crop it.")

    return data_url

def _json_schema() -> Dict[str, Any]:
    # Tight schema so frontend displays nicely and doesn't show raw blobs
    return {
        "name": "waspada_malaysia_scam_triage",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "lang": {"type": "string", "enum": ["EN", "MS", "ZH", "TA"]},
                "out_of_scope": {"type": "boolean"},
                "malaysia_relevance": {"type": "string"},

                "risk": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]},
                "verdict": {"type": "string"},
                "summary": {"type": "string"},

                "what_we_used": {"type": "array", "items": {"type": "string"}},
                "what_ai_saw": {"type": "array", "items": {"type": "string"}},
                "red_flags": {"type": "array", "items": {"type": "string"}},

                "next_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                            "title": {"type": "string"},
                            "timeframe": {"type": "string"},
                            "details": {"type": "string"},
                            "who": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["priority", "title", "timeframe", "details", "who"]
                    }
                },
                "who_to_contact": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "how": {"type": "string"},
                            "when": {"type": "string"}
                        },
                        "required": ["name", "how", "when"]
                    }
                },

                "disclaimer": {"type": "string"}
            },
            "required": [
                "lang", "out_of_scope", "malaysia_relevance",
                "risk", "verdict", "summary",
                "what_we_used", "what_ai_saw", "red_flags",
                "next_actions", "who_to_contact",
                "disclaimer"
            ]
        }
    }

def _system_prompt(lang: Lang) -> str:
    # Malaysia-first playbook (kept short but strong)
    # Core official “what to do” is anchored on NSRC (997) + report + bank action patterns.
    # We must NOT claim to be an authority, and MUST show disclaimers.
    base = f"""
You are Waspada, a Malaysia-focused anti-scam action assistant.
Your job: help people in Malaysia respond safely to suspected scams.

IMPORTANT RULES:
- Waspada is Malaysia-focused. If the situation is clearly not related to Malaysia (no Malaysia context, no Malaysia banks, no MY phone numbers, no MY agencies, no MY location), set out_of_scope=true and explain briefly.
- You must NEVER claim this is an official finding. This is AI-generated guidance only.
- Be calm, practical, and step-by-step. Prefer short bullet-like items, not long essays.
- If money was transferred / banking credentials or TAC/OTP shared / remote access installed: treat as HIGH risk unless strong evidence says otherwise.
- Do not ask the user to do risky things. Never tell them to “test” the scammer.

MALAYSIA ACTION PLAYBOOK (use where relevant):
- If funds were transferred or bank access compromised: advise urgent action to contact the bank immediately and use Malaysia’s National Scam Response Centre (NSRC) hotline (997) for rapid response (when applicable).
- Encourage preserving evidence (screenshots, transaction refs, phone numbers, URLs) and making a police report.
- Mention checking mule accounts via Semak Mule where applicable.
- If it involves phishing links, malware, or suspicious websites: advise not clicking further and consider reporting to relevant Malaysian cyber channels.

OUTPUT STYLE:
- Always produce a structured response that a mobile app can display cleanly.
- Prefer “what to do now” with priorities and timeframes.
- If screenshot is unrelated (e.g. random social post) say so and mark out_of_scope accordingly.
"""
    if lang == "MS":
        base += "\nWrite in Bahasa Malaysia."
    elif lang == "ZH":
        base += "\nWrite in Simplified Chinese."
    elif lang == "TA":
        base += "\nWrite in Tamil (simple, clear)."
    else:
        base += "\nWrite in English."

    return base.strip()

def _user_prompt(req: AnalyzeRequest) -> str:
    # Keep it crisp. The model should infer from screenshot if provided.
    scenario = _safe_trim(req.scenario, 80)
    channel = _safe_trim(req.channel, 80)
    notes = _safe_trim(req.notes, 800)

    parts = []
    if scenario:
        parts.append(f"Scenario: {scenario}")
    if channel:
        parts.append(f"Channel: {channel}")
    if notes:
        parts.append(f"User notes: {notes}")

    if not parts:
        parts.append("No extra context provided.")

    parts.append("""
Now:
1) Decide if this is Malaysia-relevant. If not, mark out_of_scope=true.
2) Summarise what you see (or infer) safely.
3) Give a risk rating and verdict.
4) Provide next actions with clear priorities/timeframes and who to contact.
5) Include a clear disclaimer that this is AI guidance only (not official).
""".strip())

    return "\n".join(parts)

# ----------------------------
# Routes
# ----------------------------
@app.get("/version")
def version():
    return {
        "ok": True,
        "service": "waspada-api",
        "has_key": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL
    }

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY on server.")

    used = []
    image_data_url = None
    if req.image_data_url:
        image_data_url = _validate_data_url(req.image_data_url)
        used.append("screenshot")

    if req.notes:
        used.append("notes")
    if req.scenario:
        used.append("scenario")
    if req.channel:
        used.append("channel")
    if not used:
        used = ["none"]

    try:
        inputs = [
            {"role": "system", "content": [{"type": "input_text", "text": _system_prompt(req.lang)}]},
            {"role": "user", "content": [{"type": "input_text", "text": _user_prompt(req)}]},
        ]

        if image_data_url:
            inputs[1]["content"].append({"type": "input_image", "image_url": image_data_url})

        resp = client.responses.create(
            model=OPENAI_MODEL,
            input=inputs,
            max_output_tokens=1200,
            response_format={"type": "json_schema", "json_schema": _json_schema()},
        )

        # responses API returns structured output in output_text
        raw_text = resp.output_text
        data = json.loads(raw_text)

        # Force-fill what_we_used from server-side detection (so UI is consistent)
        data["what_we_used"] = used

        # Safety: ensure disclaimer exists and is clear
        if not data.get("disclaimer"):
            data["disclaimer"] = (
                "This guidance is generated by AI based on what you provided. "
                "It is not an official determination, not legal advice, and may be inaccurate. "
                "If you are at risk or have lost money, contact your bank and the relevant Malaysian authorities immediately."
            )

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
            raise HTTPException(status_code=503, detail="AI service is rate-limited. Try again in a minute.")
        if "timeout" in low:
            raise HTTPException(status_code=504, detail="AI service timed out. Try again.")
        raise HTTPException(status_code=502, detail=f"AI service error: {msg}")
