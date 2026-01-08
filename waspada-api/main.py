import os
import json
import time
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openai import OpenAI

log = logging.getLogger("uvicorn.error")

app = FastAPI(title="waspada-api", version="2.0")

SERVICE_NAME = "waspada-api"
START_TS = time.time()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ---- helpers ----

def _has_key() -> bool:
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())

def _key_format_ok() -> bool:
    k = (OPENAI_API_KEY or "").strip()
    return k.startswith("sk-") and len(k) > 20

def _fingerprint_key() -> str:
    # lightweight fingerprint for debugging only (never return full key)
    import hashlib
    k = (OPENAI_API_KEY or "").encode("utf-8")
    return hashlib.sha256(k).hexdigest()[:8] if k else ""

def _normalize_lang(lang: str) -> Literal["EN", "MS", "ZH", "TA"]:
    if not lang:
        return "EN"
    s = str(lang).strip().upper()
    # accept common aliases
    if s in ("EN", "ENG", "ENGLISH"):
        return "EN"
    if s in ("MS", "BM", "MY", "MALAY", "BAHASA", "BAHASA MELAYU"):
        return "MS"
    if s in ("ZH", "CN", "CHINESE", "ZH-CN", "ZH-HANS", "SIMPLIFIED"):
        return "ZH"
    if s in ("TA", "TAMIL"):
        return "TA"
    # default
    return "EN"

def _looks_like_data_url(s: str) -> bool:
    return isinstance(s, str) and s.startswith("data:image/") and ";base64," in s

def _data_url_size_ok(s: str) -> bool:
    # guard against truly tiny payloads that often fail vision decode
    try:
        b64 = s.split(";base64,", 1)[1]
        return len(b64) > 200  # very small images often rejected
    except Exception:
        return False


# ---- models ----

class AnalyzeRequest(BaseModel):
    image_data_url: str = Field(..., description="data:image/*;base64,...")
    lang: str = Field("EN", description="EN/MS/ZH/TA (case-insensitive accepted)")

class VersionResponse(BaseModel):
    ok: bool
    service: str
    uptime_s: int
    has_key: bool
    key_format_ok: bool
    key_fp: str
    model: str


# ---- routes ----

@app.get("/")
def root():
    return {"ok": True, "service": SERVICE_NAME, "hint": "Try GET /version or POST /analyze"}

@app.get("/version", response_model=VersionResponse)
def version():
    return VersionResponse(
        ok=True,
        service=SERVICE_NAME,
        uptime_s=int(time.time() - START_TS),
        has_key=_has_key(),
        key_format_ok=_key_format_ok(),
        key_fp=_fingerprint_key(),
        model=DEFAULT_MODEL,
    )

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not _has_key():
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing on server.")
    if not _key_format_ok():
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY format looks wrong (should start with sk-).")

    lang = _normalize_lang(req.lang)

    if not _looks_like_data_url(req.image_data_url):
        raise HTTPException(status_code=422, detail="image_data_url must be a data:image/*;base64,... URL")
    if not _data_url_size_ok(req.image_data_url):
        raise HTTPException(
            status_code=422,
            detail="Image payload looks too small/invalid. Use a real screenshot/photo data URL (not tiny 1x1).",
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    system = (
        "You are Waspada, a Malaysia-first anti-scam assistant.\n"
        "Return ONLY valid JSON, no markdown, no extra text.\n"
        "Be calm, supportive, and practical.\n"
    )

    # Minimal but useful schema; app can render nicely.
    output_schema = {
        "risk_level": "LOW|MEDIUM|HIGH",
        "summary": "1-2 sentence summary of what this looks like",
        "what_ai_sees": ["bullet", "bullet"],
        "red_flags": ["bullet", "bullet"],
        "what_to_do_now": ["bullet", "bullet"],
        "malaysia_contacts": [
            {"name": "NSRC", "value": "997", "note": "Call immediately if money transferred"},
            {"name": "Semak Mule", "value": "https://semakmule.rmp.gov.my", "note": "Check mule account"},
        ],
        "confidence": 0.0,
    }

    user = (
        f"Language: {lang}\n\n"
        "Analyse this screenshot/photo for scam risk in a Malaysia context.\n"
        "Output must be JSON matching this schema shape:\n"
        f"{json.dumps(output_schema, ensure_ascii=False)}\n"
    )

    try:
        resp = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user},
                        {"type": "input_image", "image_url": req.image_data_url},
                    ],
                },
            ],
            max_output_tokens=900,
        )

        text = (resp.output_text or "").strip()
        if not (text.startswith("{") and text.endswith("}")):
            raise ValueError(f"Model did not return JSON. Got: {text[:120]}")

        data = json.loads(text)
        return {"result": {"lang": lang, **data}}

    except Exception as e:
        msg = str(e)
        log.exception("Analyze failed")

        # surface OpenAI errors clearly
        if "Incorrect API key" in msg or "invalid_api_key" in msg or "Error code: 401" in msg:
            raise HTTPException(
                status_code=500,
                detail="AI auth failed. Check OPENAI_API_KEY on Render, then redeploy.",
            )

        if "The image data you provided does not represent a valid image" in msg:
            raise HTTPException(
                status_code=422,
                detail="OpenAI rejected the image as invalid. Send a real screenshot/photo (larger base64), not tiny test images.",
            )

        raise HTTPException(status_code=502, detail=f"OPENAI_ERROR: {msg}")
