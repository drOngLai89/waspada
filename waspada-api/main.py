import os
import time
import json
import hashlib
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openai import OpenAI
from openai import AuthenticationError, APIConnectionError, RateLimitError, APIStatusError

START_TS = time.time()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("waspada-api")

app = FastAPI(title="waspada-api")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def uptime_s() -> int:
    return int(time.time() - START_TS)


def key_present() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def key_format_ok() -> bool:
    k = os.getenv("OPENAI_API_KEY", "")
    return k.startswith("sk-") and len(k) >= 20


def key_fingerprint() -> str:
    k = os.getenv("OPENAI_API_KEY", "")
    if not k:
        return ""
    return hashlib.sha256(k.encode("utf-8")).hexdigest()[:8]


def norm_lang(raw: str) -> str:
    if not raw:
        return "EN"
    s = raw.strip()
    s_low = s.lower()

    if s_low in ("en", "eng", "english"):
        return "EN"
    if s_low in ("ms", "bm", "malay", "bahasa", "bahasamelayu"):
        return "MS"
    if s_low in ("zh", "cn", "chi", "中文", "chinese"):
        return "ZH"
    if s_low in ("ta", "tam", "tamil"):
        return "TA"

    s_up = s.upper()
    if s_up in ("EN", "MS", "ZH", "TA"):
        return s_up
    return "EN"


class AnalyzeReq(BaseModel):
    image_data_url: str = Field(..., alias="image_data_url")
    lang: str = "EN"


@app.get("/")
def root():
    return {"ok": True, "service": "waspada-api", "hint": "Use /version or /analyze"}


@app.get("/version")
def version():
    return {
        "ok": True,
        "service": "waspada-api",
        "uptime_s": uptime_s(),
        "has_key": key_present(),
        "key_format_ok": key_format_ok(),
        "key_fp": key_fingerprint(),
        "model": MODEL,
    }


@app.post("/analyze")
def analyze(req: AnalyzeReq) -> Dict[str, Any]:
    lang = norm_lang(req.lang)

    if not req.image_data_url or not req.image_data_url.startswith("data:image"):
        raise HTTPException(status_code=422, detail="image_data_url must be a data URL starting with data:image/...")

    system_prompt = f"""
You are Waspada, an anti-scam assistant for Malaysia.
You will review ONE screenshot and produce safe, practical guidance.

Return STRICT JSON only (no markdown), matching this schema:

{{
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "summary": "1-2 short sentences",
  "what_looks_suspicious": ["bullet", "..."],
  "missing_info_to_confirm": ["bullet", "..."],
  "safe_next_steps_malaysia": [
    "If money already moved: call NSRC 997 immediately (Malaysia).",
    "Call your bank ASAP to freeze/recall transfer; provide transaction reference.",
    "Keep evidence: screenshots, phone numbers, account numbers, chat logs, receipts.",
    "Check recipient details on Semak Mule (PDRM CCID).",
    "If links/OTP/password shared: change passwords and enable 2FA."
  ],
  "official_resources": [
    {{"name":"NSRC 997 (Malaysia)","note":"If funds transferred or in-progress scam"}},
    {{"name":"Semak Mule (PDRM CCID)","url":"https://semakmule.rmp.gov.my"}},
    {{"name":"BNMTELELINK","value":"1-300-88-5465","note":"Bank Negara Malaysia guidance"}},
    {{"name":"MyCERT","url":"https://www.mycert.org.my","note":"Cyber incident guidance"}}
  ],
  "confidence": 0.0
}}

Language requirement:
- EN: English
- MS: Bahasa Melayu
- ZH: Simplified Chinese
- TA: Tamil (simple)

Be calm, non-judgemental. Focus on safety. No legal claims.
""".strip()

    user_text = f"Analyse this screenshot for scam signs in Malaysia. lang={lang}. Return JSON only."

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Responses API (best support for vision + modern models)
        resp = client.responses.create(
            model=MODEL,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_text},
                        {"type": "input_image", "image_url": req.image_data_url},
                    ],
                },
            ],
            max_output_tokens=900,
        )

        text = (resp.output_text or "").strip()
        if not text:
            raise ValueError("empty_model_output")

        # Parse JSON strictly; fallback if model misbehaves
        try:
            data = json.loads(text)
            return {"result": {"lang": lang, **data}}
        except Exception:
            return {
                "result": {
                    "lang": lang,
                    "risk_level": "MEDIUM",
                    "summary": "Could not parse AI output as JSON. Please try again.",
                    "what_looks_suspicious": [],
                    "missing_info_to_confirm": [],
                    "safe_next_steps_malaysia": [
                        "If money already moved: call NSRC 997 immediately.",
                        "Call your bank ASAP and request to freeze/recall the transfer.",
                        "Keep evidence: screenshots, phone numbers, account numbers, chat logs.",
                        "Check recipient details on Semak Mule (PDRM CCID).",
                    ],
                    "official_resources": [
                        {"name": "NSRC 997 (Malaysia)", "note": "If funds transferred or in-progress scam"},
                        {"name": "Semak Mule (PDRM CCID)", "url": "https://semakmule.rmp.gov.my"},
                        {"name": "BNMTELELINK", "value": "1-300-88-5465"},
                    ],
                    "confidence": 0.2,
                    "_debug_raw_model_output": text[:400],
                }
            }

    except AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail=f"OPENAI_AUTH_FAILED (key_fp={key_fingerprint()}). Re-check OPENAI_API_KEY in Render, save, and redeploy.",
        )
    except RateLimitError:
        raise HTTPException(status_code=503, detail="OPENAI_RATE_LIMIT. Try again in a minute.")
    except APIConnectionError:
        raise HTTPException(status_code=502, detail="OPENAI_CONNECTION_ERROR. Upstream network issue, try again.")
    except APIStatusError as e:
        # Try to surface the OpenAI error message cleanly
        msg = "OPENAI_STATUS_ERROR"
        try:
            body = e.response.json()
            if isinstance(body, dict) and "error" in body and isinstance(body["error"], dict):
                msg = body["error"].get("message", msg)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"OPENAI_400/500: {msg}")
    except Exception as e:
        log.exception("Analyze failed")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)[:180]}")
