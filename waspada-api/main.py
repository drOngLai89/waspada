import base64
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from openai import OpenAI

log = logging.getLogger("waspada-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="waspada-api", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Official resources (hardcoded so AI cannot invent)
# -------------------------
OFFICIAL_RESOURCES = [
    {"name": "National Scam Response Centre (NSRC)", "type": "phone", "value": "997", "notes": "Malaysia. For online financial fraud / funds moved."},
    {"name": "PDRM Semak Mule", "type": "url", "value": "https://semakmule.rmp.gov.my/", "notes": "Check mule accounts/phone numbers."},
    {"name": "BNM Scam / Fraud FAQs", "type": "url", "value": "https://www.bnm.gov.my/faqs/banking/all", "notes": "Bank Negara Malaysia guidance."},
    {"name": "MyCERT Cyber999 (Report incidents)", "type": "url", "value": "https://www.mycert.org.my/portal/online-form?id=7a911418-9e84-4e48-84d3-aa8a4fe55f16", "notes": "CyberSecurity Malaysia reporting form."},
    {"name": "Cyber999 email", "type": "email", "value": "cyber999@cybersecurity.my", "notes": "CyberSecurity Malaysia / MyCERT."},
    {"name": "NFCC (National Anti-Financial Crime Centre)", "type": "url", "value": "https://nfcc.jpm.gov.my/", "notes": "NSRC owner agency info."},
]

# -------------------------
# Helpers
# -------------------------
def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]

def _get_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()

def _key_format_ok(k: str) -> bool:
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

    if len(raw) < 200:
        raise HTTPException(status_code=400, detail="Image data is too small. Please pick a real screenshot.")
    if len(raw) > 6_000_000:
        raise HTTPException(status_code=400, detail="Image too large. Try a smaller screenshot.")

def _extract_output_text(resp: Any) -> str:
    # Most common in openai python
    if hasattr(resp, "output_text") and resp.output_text:
        return str(resp.output_text).strip()

    # Fallback: walk items
    out = getattr(resp, "output", None)
    if not out:
        return ""

    parts: List[str] = []
    for item in out:
        if isinstance(item, dict):
            if item.get("type") == "message":
                for c in item.get("content") or []:
                    if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                        parts.append(c.get("text", ""))
        else:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", None) or []:
                    if getattr(c, "type", None) in ("output_text", "text"):
                        parts.append(getattr(c, "text", "") or "")
    return "\n".join([p for p in parts if p]).strip()

def _parse_json_loose(text: str) -> Dict[str, Any]:
    """
    We WANT pure JSON, but models occasionally add stray text.
    This tries:
      1) json.loads(text)
      2) extract first {...} block and json.loads(that)
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text")

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Extract first JSON object block
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict):
            return obj

    raise ValueError("Could not parse JSON")

# -------------------------
# API models
# -------------------------
class AnalyzeReq(BaseModel):
    image_data_url: str = Field(..., description="Screenshot as data:image/...;base64,...")
    lang: str = Field("EN", description="EN|MS|ZH|TA")

# -------------------------
# Routes
# -------------------------
@app.get("/")
def root():
    return {"ok": True, "service": "waspada-api"}

@app.get("/version")
def version():
    k = _get_key()
    return {
        "ok": True,
        "service": "waspada-api",
        "has_key": bool(k),
        "key_format_ok": _key_format_ok(k) if k else False,
        "key_fp": _fp(k) if k else None,
        "model": _get_model(),
        "api_version": "1.1",
    }

@app.get("/hotlines")
def hotlines():
    # Frontend can show this in a "Report / Call" area later.
    return {"ok": True, "resources": OFFICIAL_RESOURCES}

def _prompt(lang: str) -> str:
    # Malaysia-first, action routing, and strong disclaimers.
    # IMPORTANT: we instruct the model to ONLY use resources we provide.
    return f"""
You are Waspada: a Malaysia-first anti-scam ACTION assistant.
Your job is NOT “image analysis for fun”. Your job is to produce a practical action plan for people in Malaysia.

You will be given a screenshot image.
You must:
1) Interpret what the screenshot most likely shows (short).
2) Decide if it looks like a scam attempt or suspicious situation (verdict + risk).
3) Identify the likely scam scenario (choose one).
4) Provide Malaysia-specific next steps and who to contact.
5) Include clear disclaimers.

SCOPE:
- This app is only for MALAYSIA scam / fraud situations.
- If the screenshot is clearly NOT related to Malaysia (not Malaysia context, no Malaysia banks/services, no Malaysia audience),
  set out_of_scope=true and explain politely that Waspada only supports Malaysia, and you cannot provide country-specific steps.

OFFICIAL RESOURCES:
You MUST NOT invent hotlines, agencies, or links.
Only refer to these resources (exactly as provided):
{json.dumps(OFFICIAL_RESOURCES, ensure_ascii=False)}

LANGUAGE:
Respond in: {lang}

OUTPUT:
Return ONLY valid JSON (no markdown, no extra text). Must be a JSON object with EXACTLY these keys:

- out_of_scope: boolean
- malaysia_relevance: short reason (1 sentence)
- scenario: one of ["BANK_TRANSFER","UNAUTHORISED_TRANSACTION","IMPERSONATION","COURIER_PARCEL","INVESTMENT","JOB_SCAM","ROMANCE","OTP_MALWARE","MARKETPLACE","OTHER"]
- verdict: one of ["LIKELY_SAFE","SUSPICIOUS","LIKELY_SCAM","CRITICAL_RISK"]
- risk: one of ["LOW","MEDIUM","HIGH","CRITICAL"]
- what_the_screenshot_suggests: 1–2 sentences
- key_red_flags: array of strings (max 8)
- what_to_do_next: array of strings (max 10, Malaysia-first, concrete)
- who_to_contact: array of strings (use ONLY the provided official resources, plus "your bank’s 24/7 hotline")
- evidence_to_save: array of strings (max 8)
- message_you_can_copy: a short copy-ready message the user can send to their bank or family (2–5 lines)
- disclaimer: a clear caveat in proper English: this is AI-generated guidance based on the screenshot, may be wrong/incomplete, not official advice/diagnosis, and for urgent cases contact bank/authorities.

RULES:
- If money has already moved or the user is being pressured to transfer now, your output should lean to CRITICAL risk with immediate steps.
- Avoid accusing real people by name. Talk in terms of “the sender / the caller / the account”.
""".strip()

@app.post("/analyze")
def analyze(req: AnalyzeReq):
    lang = (req.lang or "EN").upper().strip()
    if lang not in ("EN", "MS", "ZH", "TA"):
        lang = "EN"

    image_data_url = (req.image_data_url or "").strip()
    _validate_image_data_url(image_data_url)

    model = _get_model()
    prompt = _prompt(lang)

    try:
        client = _client()

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
            max_output_tokens=1300,
        )

        text = _extract_output_text(resp)
        if not text:
            raise HTTPException(status_code=502, detail="Empty AI response.")

        data = _parse_json_loose(text)

        # Minimal sanity: ensure required keys exist
        required = [
            "out_of_scope","malaysia_relevance","scenario","verdict","risk",
            "what_the_screenshot_suggests","key_red_flags","what_to_do_next",
            "who_to_contact","evidence_to_save","message_you_can_copy","disclaimer"
        ]
        missing = [k for k in required if k not in data]
        if missing:
            raise HTTPException(status_code=502, detail=f"AI response missing keys: {', '.join(missing)}")

        # Always attach resources so frontend can show “Official resources”
        data["official_resources"] = OFFICIAL_RESOURCES

        return {"result": {"lang": lang, **data}}

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        log.exception("Analyze failed: %s", msg)
        low = msg.lower()

        if "invalid_api_key" in low or "incorrect api key" in low or "401" in low:
            raise HTTPException(status_code=500, detail="Auth failed. Check OPENAI_API_KEY on Render, then clear cache & redeploy.")
        if "rate limit" in low or "429" in low:
            raise HTTPException(status_code=503, detail="AI service is rate-limited. Try again in a minute.")
        if "timeout" in low:
            raise HTTPException(status_code=504, detail="AI service timed out. Try again.")
        if "json" in low:
            raise HTTPException(status_code=502, detail="AI returned an invalid format. Try again with a clearer screenshot.")
        raise HTTPException(status_code=502, detail=f"AI service error: {msg}")
