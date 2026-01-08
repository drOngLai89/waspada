import base64
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from openai import OpenAI

log = logging.getLogger("waspada-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="waspada-api", version="1.0")

# CORS for Expo dev / mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]

def _get_key() -> str:
    k = (os.getenv("OPENAI_API_KEY") or "").strip()
    return k

def _key_format_ok(k: str) -> bool:
    # OpenAI keys typically start with "sk-"
    return k.startswith("sk-") and len(k) > 20

def _get_model() -> str:
    return (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()

def _client() -> OpenAI:
    k = _get_key()
    if not k:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY on server.")
    return OpenAI(api_key=k)

DATA_URL_RE = re.compile(r"^data:image\/(png|jpeg|jpg|webp);base64,(.+)$", re.IGNORECASE)

def _validate_image_data_url(image_data_url: str) -> None:
    if not image_data_url or not isinstance(image_data_url, str):
        raise HTTPException(status_code=400, detail="image_data_url is required.")

    m = DATA_URL_RE.match(image_data_url.strip())
    if not m:
        raise HTTPException(
            status_code=400,
            detail="Invalid image_data_url. Must be a data URL like data:image/jpeg;base64,...",
        )

    b64 = m.group(2)
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 in image_data_url.")

    # Basic sanity: prevent huge payloads (tune as you like)
    if len(raw) < 20:
        raise HTTPException(status_code=400, detail="Image data is too small.")
    if len(raw) > 6_000_000:
        raise HTTPException(status_code=400, detail="Image too large. Try a smaller screenshot.")

class AnalyzeReq(BaseModel):
    image_data_url: str = Field(..., description="Screenshot as data:image/...;base64,...")
    lang: str = Field("EN", description="EN|MS|ZH|TA")

@app.get("/")
def root():
    return {"ok": True, "service": "waspada-api"}

@app.head("/")
def root_head():
    return {"ok": True}

@app.get("/version")
def version():
    k = _get_key()
    return {
        "ok": True,
        "service": "waspada-api",
        "uptime_s": None,
        "has_key": bool(k),
        "key_format_ok": _key_format_ok(k) if k else False,
        "key_fp": _fp(k) if k else None,
        "model": _get_model(),
    }

def _prompt(lang: str) -> str:
    # Keep it short + consistent output schema
    return f"""
You are Waspada, an anti-scam assistant for Malaysia.
Analyse the screenshot content and output ONLY valid JSON (no markdown, no extra text).

Language: {lang}

Return JSON with exactly these keys:
- risk: one of ["LOW","MEDIUM","HIGH","CRITICAL"]
- diagnosis: 1–2 sentence summary
- what_ai_sees: 1–2 sentence description of what the screenshot appears to show
- analysis: short paragraph explaining why
- justification: short bullet-like list (array of strings)
- red_flags: array of strings
- what_to_do_now: array of strings (Malaysia-first, practical)
- channels: array of strings (e.g. "bank hotline", "NSRC 997", "PDRM report", "Semak Mule")
- recommended_contacts: array of strings (e.g. "NSRC 997", "your bank hotline", etc.)
""".strip()

def _extract_output_text(resp: Any) -> str:
    # openai python usually provides resp.output_text
    if hasattr(resp, "output_text") and resp.output_text:
        return str(resp.output_text)

    # Fallback: walk output items
    out = getattr(resp, "output", None)
    if not out:
        return ""

    parts: List[str] = []
    for item in out:
        if isinstance(item, dict):
            # older structures
            if item.get("type") == "message":
                content = item.get("content") or []
                for c in content:
                    if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                        parts.append(c.get("text", ""))
        else:
            # object-like
            if getattr(item, "type", None) == "message":
                content = getattr(item, "content", None) or []
                for c in content:
                    if getattr(c, "type", None) in ("output_text", "text"):
                        parts.append(getattr(c, "text", "") or "")
    return "\n".join([p for p in parts if p]).strip()

@app.post("/analyze")
def analyze(req: AnalyzeReq):
    lang = (req.lang or "EN").upper().strip()
    if lang not in ("EN", "MS", "ZH", "TA"):
        lang = "EN"

    image_data_url = req.image_data_url.strip()
    _validate_image_data_url(image_data_url)

    model = _get_model()
    prompt = _prompt(lang)

    try:
        client = _client()

        # Responses API with image data URL (supported pattern shown in OpenAI docs). :contentReference[oaicite:2]{index=2}
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_data_url},
                    ],
                }
            ],
            max_output_tokens=1200,
        )

        text = _extract_output_text(resp)
        if not text:
            raise HTTPException(status_code=502, detail="Empty AI response.")

        # Expect pure JSON; try parse
        data = json.loads(text)
        if not isinstance(data, dict):
            raise HTTPException(status_code=502, detail="AI returned non-JSON object.")

        return {"result": {"lang": lang, **data}}

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        log.exception("Analyze failed: %s", msg)

        # Friendlier classification
        if "invalid_api_key" in msg or "Incorrect API key" in msg or "401" in msg:
            raise HTTPException(
                status_code=500,
                detail="AI service authentication failed. Re-check OPENAI_API_KEY on Render and redeploy (Clear cache).",
            )

        if "valid image" in msg or "Invalid image" in msg:
            raise HTTPException(status_code=400, detail="Invalid image. Please pick a real screenshot and try again.")

        raise HTTPException(status_code=502, detail=f"AI service error: {msg}")
