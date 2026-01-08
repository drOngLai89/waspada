import os
import json
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import OpenAI

APP_START = time.time()
SERVICE_NAME = os.getenv("SERVICE_NAME", "waspada-api")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

app = FastAPI(title="Waspada API", version="1.0")

# Helpful for Expo web + debugging; native apps don't need CORS, but it doesn't hurt here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))

def norm_lang(raw: Optional[str]) -> str:
    if not raw:
        return "EN"
    s = str(raw).strip().upper()

    aliases = {
        "EN": "EN",
        "ENG": "EN",
        "ENGLISH": "EN",

        "MS": "MS",
        "BM": "MS",
        "MY": "MS",
        "MALAY": "MS",
        "BAHASA": "MS",
        "BAHASA MALAYSIA": "MS",

        "ZH": "ZH",
        "CN": "ZH",
        "CHINESE": "ZH",
        "中文": "ZH",
        "华语": "ZH",

        "TA": "TA",
        "TAMIL": "TA",
    }
    return aliases.get(s, "EN")

class AnalyzeRequest(BaseModel):
    image_data_url: str
    lang: Optional[str] = "EN"

@app.get("/version")
def version():
    return {
        "ok": True,
        "service": SERVICE_NAME,
        "uptime_s": int(time.time() - APP_START),
        "has_key": has_openai_key(),
        "model": MODEL,
    }

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    lang = norm_lang(req.lang)

    if not has_openai_key():
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY on server")

    image_url = (req.image_data_url or "").strip()
    if not image_url.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data_url must be a data:image/...;base64,... URL")

    # Malaysia-first, practical output in STRICT JSON
    system = f"""
You are Waspada, a Malaysia-first scam safety assistant.

Goals:
- Detect likely scam patterns from a screenshot (chat, bank transfer screen, message, social post).
- Provide safe, practical next steps for someone in Malaysia.
- If money might already be transferred, prioritise urgent actions.

You MUST output a single JSON object only (no markdown, no extra text).

Include Malaysia official channels in guidance where relevant:
- National Scam Response Centre (NSRC): 997
- PDRM Semak Mule: https://semakmule.rmp.gov.my
- Cyber999 (MyCERT): 1-300-88-2999 (office hours), +6019-2665850 (24x7), https://www.mycert.org.my
- Bank Negara Malaysia BNMTELELINK: 1-300-88-5465

Language:
- Use {lang}. Keep it calm, not alarmist.
"""

    user = """
Return STRICT JSON with this schema:

{
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "scam_type": "string",
  "confidence": 0-100,
  "what_you_see": ["short bullet", "..."],
  "red_flags": ["short bullet", "..."],
  "safe_next_steps": ["actionable step 1", "..."],
  "if_money_transferred": ["urgent step 1", "..."],
  "who_to_contact": [
    {"name":"NSRC","value":"997","note":"..."},
    {"name":"PDRM Semak Mule","value":"https://semakmule.rmp.gov.my","note":"..."},
    {"name":"Cyber999 (MyCERT)","value":"1-300-88-2999 / +6019-2665850","note":"..."},
    {"name":"BNMTELELINK","value":"1-300-88-5465","note":"..."}
  ],
  "useful_links": [
    {"name":"Semak Mule","url":"https://semakmule.rmp.gov.my"},
    {"name":"MyCERT","url":"https://www.mycert.org.my"}
  ],
  "disclaimer": "short, friendly disclaimer"
}

Rules:
- If screenshot shows urgency / threats / “act now” / account freeze / police / parcel / loan / job offer / crypto / mule account, it’s likely MEDIUM/HIGH.
- Never tell user to send money. Never ask for passwords/OTP.
- Keep steps realistic (call bank, freeze, evidence, report).
"""

    try:
        client = OpenAI()

        # Use chat.completions for broad SDK compatibility
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0.2,
            max_tokens=900,
            messages=[
                {"role": "system", "content": system.strip()},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user.strip()},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )

        text = (resp.choices[0].message.content or "").strip()

        # Parse JSON (attempt recovery if model adds noise)
        try:
            data = json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(text[start : end + 1])
            else:
                data = {"risk_level": "MEDIUM", "scam_type": "Unknown", "confidence": 50, "raw": text}

        return {"result": data, "lang": lang}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {str(e)}")
