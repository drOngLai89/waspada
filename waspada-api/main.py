import os
import time
import json
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openai import OpenAI

START_TS = time.time()
log = logging.getLogger("waspada-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="waspada-api")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def uptime_s() -> int:
    return int(time.time() - START_TS)

def key_present() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))

def key_format_ok() -> bool:
    k = os.getenv("OPENAI_API_KEY", "")
    return k.startswith("sk-") and len(k) >= 20

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
        "model": MODEL,
    }

@app.post("/analyze")
def analyze(req: AnalyzeReq) -> Dict[str, Any]:
    lang = norm_lang(req.lang)

    if not req.image_data_url or not req.image_data_url.startswith("data:image"):
        raise HTTPException(status_code=422, detail="image_data_url must be a data URL starting with data:image/...")

    system_prompt = f"""
You are Waspada, an anti-scam assistant for Malaysia.
You will review ONE screenshot (chat, SMS, WhatsApp, bank screen, marketplace, etc) and produce safe, practical guidance.

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
    {{"name":"BNMTELELINK","value":"1-300-88-5465","note":"Bank Negara Malaysia general guidance"}},
    {{"name":"MyCERT","url":"https://www.mycert.org.my","note":"Cyber incident guidance"}}
  ],
  "confidence": 0.0
}}

Language requirement:
- If lang == "EN": respond in English.
- If lang == "MS": respond in Bahasa Melayu.
- If lang == "ZH": respond in Simplified Chinese.
- If lang == "TA": respond in Tamil (simple, clear).

Be calm, non-judgemental. No legal claims. No accusations. Focus on safety.
""".strip()

    user_text = f"Analyse this screenshot for scam signs. lang={lang}. Return JSON only."

    try:
        client = OpenAI()

        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_prompt},
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
            raise ValueError("Empty response from model")

        data = json.loads(text)
        return {"result": {"lang": lang, **data}}

    except Exception as e:
        msg = str(e)
        log.exception("Analyze failed")

        if "invalid_api_key" in msg or "Incorrect API key" in msg or "Error code: 401" in msg:
            raise HTTPException(
                status_code=500,
                detail="AI service authentication failed. Check OPENAI_API_KEY on Render (must start with sk-), then redeploy.",
            )

        raise HTTPException(status_code=500, detail="AI service error. Please try again in a moment.")
