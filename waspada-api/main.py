import os
import time
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_NAME = "waspada-api"
START_TS = int(time.time())

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "45"))
MAX_B64_CHARS = int(os.getenv("MAX_B64_CHARS", str(3_500_000)))


class AnalyzeRequest(BaseModel):
    image_data_url: str = Field(..., description="data:image/jpeg;base64,...")
    lang: Optional[Literal["EN", "MS", "ZH", "TA"]] = "EN"


class AnalyzeResponse(BaseModel):
    ok: bool
    risk: Literal["LOW", "MEDIUM", "HIGH"]
    summary: str
    what_i_notice: list[str]
    red_flags: list[str]
    what_to_do_now: list[str]
    recommended_contacts: list[str]
    disclaimer: str


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"ok": True, "service": APP_NAME}


@app.get("/version")
def version():
    key = os.getenv("OPENAI_API_KEY", "")
    return {
        "ok": True,
        "service": APP_NAME,
        "uptime_s": int(time.time()) - START_TS,
        "has_key": bool(key),
        "model": OPENAI_MODEL,
    }


def _client():
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise HTTPException(status_code=500, detail="Server misconfigured: OPENAI_API_KEY missing")
    if OpenAI is None:
        raise HTTPException(status_code=500, detail="openai package not available on server")
    return OpenAI(api_key=key, timeout=OPENAI_TIMEOUT)


def _system_prompt(lang: str) -> str:
    return (
        "You are Waspada, an anti-scam assistant. Analyse the screenshot as a user safety helper.\n"
        "Return ONLY valid JSON with keys: risk, summary, what_i_notice, red_flags, what_to_do_now, recommended_contacts.\n"
        "Rules:\n"
        "- risk must be one of LOW, MEDIUM, HIGH\n"
        "- Keep it practical, calm, and non-accusatory\n"
        "- If unsure, say so and recommend verification steps\n"
        f"- Language: {lang}\n"
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    data_url = req.image_data_url.strip()

    if not data_url.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data_url must start with data:image/...")

    if len(data_url) > MAX_B64_CHARS:
        raise HTTPException(status_code=413, detail="Image too large. Please resize/compress and try again.")

    client = _client()

    messages = [
        {"role": "system", "content": _system_prompt(req.lang or "EN")},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyse this screenshot for scam indicators and what to do next."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=900,
        )
        raw = resp.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI request failed: {type(e).__name__}: {e}")

    import json
    try:
        obj = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=502, detail="AI returned non-JSON output. Try again or reduce image complexity.")

    def _as_list(v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v][:12]
        return [str(v)]

    risk = str(obj.get("risk", "MEDIUM")).upper()
    if risk not in ["LOW", "MEDIUM", "HIGH"]:
        risk = "MEDIUM"

    result = {
        "ok": True,
        "risk": risk,
        "summary": str(obj.get("summary", "")).strip()[:800],
        "what_i_notice": _as_list(obj.get("what_i_notice")),
        "red_flags": _as_list(obj.get("red_flags")),
        "what_to_do_now": _as_list(obj.get("what_to_do_now")),
        "recommended_contacts": _as_list(obj.get("recommended_contacts")),
        "disclaimer": "This is guidance, not a guarantee. If money or accounts are at risk, stop and verify via official channels.",
    }

    if not result["summary"]:
        result["summary"] = "I couldn’t confidently read enough details from this screenshot. Try a clearer capture and verify via official channels."

    return result
