import os
import re
import json
import time
import base64
import hashlib
import logging
from typing import Literal, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from openai import OpenAI
from openai import APIError, BadRequestError, AuthenticationError, RateLimitError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("waspada-api")

app = FastAPI(title="Waspada API", version="2.0")

START_TS = time.time()

# ---------------------------
# Malaysia-first references (kept short; frontend shows the full info)
# ---------------------------
MALAYSIA_RESOURCES = {
    "hotlines": [
        {"name": "NSRC (National Scam Response Centre)", "value": "997", "note": "Call immediately if money was transferred (Malaysia)."},
        {"name": "BNMTELELINK (Bank Negara Malaysia)", "value": "1-300-88-5465", "note": "Banking / financial guidance (Malaysia)."},
    ],
    "links": [
        {"name": "Semak Mule (PDRM CCID)", "url": "https://semakmule.rmp.gov.my"},
        {"name": "NFCC (National Fraud Centre)", "url": "https://nfcc.jpm.gov.my"},
        {"name": "Bank Negara Malaysia", "url": "https://www.bnm.gov.my"},
    ],
}

LANG_CANON = ("EN", "MS", "ZH", "TA")
LANG_ALIASES = {
    "en": "EN", "eng": "EN", "english": "EN",
    "ms": "MS", "bm": "MS", "malay": "MS", "bahasa": "MS",
    "zh": "ZH", "cn": "ZH", "chinese": "ZH", "mandarin": "ZH",
    "ta": "TA", "tamil": "TA",
}

def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None and v != "" else default

def _key_fp(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]

def _looks_like_data_url(s: str) -> bool:
    return s.startswith("data:image/") and ";base64," in s

def _extract_b64(data_url: str) -> str:
    # data:image/png;base64,AAAA...
    return data_url.split(";base64,", 1)[1].strip()

def _bytes_signature_ok(b: bytes) -> bool:
    # PNG header: 89 50 4E 47 0D 0A 1A 0A
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # JPEG header: FF D8 FF
    if len(b) >= 3 and b[0] == 0xFF and b[1] == 0xD8 and b[2] == 0xFF:
        return True
    # WebP: RIFF....WEBP
    if len(b) >= 12 and b.startswith(b"RIFF") and b[8:12] == b"WEBP":
        return True
    return False

def _validate_image_data_url(data_url: str) -> None:
    if not _looks_like_data_url(data_url):
        raise HTTPException(status_code=400, detail="image_data_url must be a data URL like data:image/png;base64,...")

    b64 = _extract_b64(data_url)
    if len(b64) < 32:
        raise HTTPException(status_code=400, detail="image_data_url base64 is too short (not a real image).")

    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="image_data_url base64 cannot be decoded. Please re-pick the image.")

    if len(raw) < 64:
        raise HTTPException(status_code=400, detail="Decoded image bytes are too small. Please re-pick the image.")

    if not _bytes_signature_ok(raw):
        raise HTTPException(status_code=400, detail="Image signature not recognised (expect PNG/JPEG/WebP). Please re-pick the image.")

class AnalyzeIn(BaseModel):
    image_data_url: str = Field(..., description="data:image/...;base64,...")
    lang: str = Field("EN", description="EN | MS | ZH | TA (aliases accepted: en/ms/zh/ta)")

    @field_validator("lang")
    @classmethod
    def normalise_lang(cls, v: str) -> str:
        vv = (v or "").strip()
        if vv in LANG_CANON:
            return vv
        low = vv.lower()
        if low in LANG_ALIASES:
            return LANG_ALIASES[low]
        raise ValueError("Input should be 'EN', 'MS', 'ZH' or 'TA' (aliases: en/ms/zh/ta)")

class VersionOut(BaseModel):
    ok: bool
    service: str
    uptime_s: int
    has_key: bool
    key_format_ok: bool
    key_fp: Optional[str] = None
    model: str

def build_prompt(lang: Literal["EN", "MS", "ZH", "TA"]) -> str:
    # Keep it compact but strict. The frontend is where we show long Malaysia guidance.
    # Return JSON only.
    return f"""
You are Waspada, a Malaysia-first anti-scam assistant.
Analyse the screenshot/image for signs of scam/fraud/impersonation/phishing.
Be careful: do not accuse a real person with certainty. Use probabilities and red flags.

Output MUST be valid JSON ONLY (no markdown), using this schema:

{{
  "risk_level": "LOW"|"MEDIUM"|"HIGH",
  "summary": string,
  "what_i_see": [string, ...],
  "red_flags": [string, ...],
  "likely_scam_type": string,
  "recommended_actions": [string, ...],
  "evidence_to_keep": [string, ...],
  "malaysia_next_steps": {{
    "hotlines": [
      {{"name": string, "value": string, "note": string}}
    ],
    "links": [
      {{"name": string, "url": string}}
    ]
  }}
}}

Language rules:
- If lang=EN, write in English.
- If lang=MS, write in Bahasa Malaysia.
- If lang=ZH, write in Simplified Chinese.
- If lang=TA, write in Tamil.

Malaysia context:
- Mention NSRC 997 if money already transferred.
- Mention Semak Mule for mule account checks.
- Mention calling the bank ASAP for freezing/recall.

Return JSON ONLY.
""".strip()

def get_client() -> OpenAI:
    key = _get_env("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing on server.")
    return OpenAI(api_key=key)

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "waspada-api",
        "message": "Use GET /version and POST /analyze",
    }

@app.get("/version", response_model=VersionOut)
def version() -> VersionOut:
    key = _get_env("OPENAI_API_KEY") or ""
    model = _get_env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
    has_key = key != ""
    key_format_ok = bool(re.match(r"^sk-[A-Za-z0-9].+", key)) if has_key else False

    return VersionOut(
        ok=True,
        service="waspada-api",
        uptime_s=int(time.time() - START_TS),
        has_key=has_key,
        key_format_ok=key_format_ok,
        key_fp=_key_fp(key) if has_key else None,
        model=model,
    )

@app.post("/analyze")
def analyze(payload: AnalyzeIn) -> Dict[str, Any]:
    _validate_image_data_url(payload.image_data_url)

    model = _get_env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"

    try:
        client = get_client()

        prompt = build_prompt(payload.lang)

        # Responses API (vision). We send the image as a data URL.
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": payload.image_data_url},
                    ],
                }
            ],
            max_output_tokens=900,
        )

        text = (resp.output_text or "").strip()
        if not text:
            raise HTTPException(status_code=502, detail="AI returned empty output. Try again.")

        # Must be JSON
        if not (text.startswith("{") and text.endswith("}")):
            raise HTTPException(status_code=502, detail="AI output was not valid JSON. Try again.")

        data = json.loads(text)

        # Inject Malaysia resources (safe fallback)
        data.setdefault("malaysia_next_steps", {})
        data["malaysia_next_steps"].setdefault("hotlines", MALAYSIA_RESOURCES["hotlines"])
        data["malaysia_next_steps"].setdefault("links", MALAYSIA_RESOURCES["links"])

        return {"result": {"lang": payload.lang, **data}}

    except AuthenticationError:
        raise HTTPException(status_code=500, detail="AI auth failed. Re-check OPENAI_API_KEY on Render and redeploy.")
    except RateLimitError:
        raise HTTPException(status_code=503, detail="AI rate-limited. Try again in a minute.")
    except BadRequestError as e:
        # Typical cause: invalid image content, request shape, etc.
        msg = str(e)
        raise HTTPException(status_code=400, detail=f"OPENAI_400: {msg}")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"OPENAI_API_ERROR: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Analyze failed")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
