import os
import time
import re
from typing import Optional, Literal, Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from openai import OpenAI

APP_NAME = "waspada-api"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "45"))

client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)

app = FastAPI(title=APP_NAME)

# Safe CORS for mobile dev. Tighten later if you want.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()

LANG_CANON = {"EN": "EN", "MS": "MS", "ZH": "ZH", "TA": "TA"}
LANG_ALIASES = {
    "en": "EN", "eng": "EN", "english": "EN",
    "ms": "MS", "bm": "MS", "malay": "MS", "bahasa": "MS", "bahasa malaysia": "MS",
    "zh": "ZH", "cn": "ZH", "chinese": "ZH", "mandarin": "ZH",
    "ta": "TA", "tamil": "TA",
}

def normalise_lang(value: str) -> str:
    if not value:
        return "EN"
    v = value.strip()
    if v in LANG_CANON:
        return v
    key = v.lower()
    return LANG_ALIASES.get(key, "EN")

def strip_data_url_prefix(data_url: str) -> str:
    # Accept both full data URLs and raw base64
    if not data_url:
        return ""
    m = re.match(r"^data:image\/[a-zA-Z0-9.+-]+;base64,(.*)$", data_url)
    return m.group(1) if m else data_url

class VersionOut(BaseModel):
    ok: bool = True
    service: str = APP_NAME
    uptime_s: int
    has_key: bool
    model: str

@app.get("/version", response_model=VersionOut)
def version():
    return VersionOut(
        uptime_s=int(time.time() - START_TIME),
        has_key=bool(OPENAI_API_KEY),
        model=OPENAI_MODEL,
    )

class AnalyzeIn(BaseModel):
    image_data_url: str = Field(..., description="data:image/...;base64,... OR raw base64")
    lang: Optional[str] = Field("EN", description="EN/MS/ZH/TA (case-insensitive accepted)")
    client_context: Optional[dict] = Field(default=None, description="Optional metadata like appVersion")

class AnalyzeOut(BaseModel):
    result: Dict[str, Any]

MALAYSIA_RESOURCES = {
    "NSRC": {"name": "National Scam Response Centre (NSRC)", "phone": "997"},
    "BNM": {"name": "BNMTELELINK (Bank Negara Malaysia)", "phone": "1-300-88-5465"},
    "PDRM_SEMAKMULE": {"name": "PDRM CCID Semak Mule", "url": "https://semakmule.rmp.gov.my"},
    "CCID_SRC": {"name": "PDRM CCID Scam Response Centre", "phone": "03-2610 1559 / 1599"},
}

def build_prompt(lang: str) -> str:
    # Keep it short + consistent. The model outputs JSON only.
    # The Malaysia resources are included in the output for immediate action.
    if lang == "MS":
        return (
            "Anda ialah pembantu keselamatan digital untuk Malaysia. "
            "Tugas anda: analisis tangkapan skrin/imej untuk tanda-tanda penipuan (scam), phishing, pemerasan, peniruan bank/kerajaan, "
            "atau transaksi mencurigakan. Jangan buat tuduhan fakta yang tidak pasti; sebut sebagai 'berkemungkinan'. "
            "Berikan langkah tindakan segera yang praktikal untuk Malaysia.\n\n"
            "WAJIB keluarkan JSON sahaja ikut skema yang diberi.\n"
        )
    if lang == "ZH":
        return (
            "你是面向马来西亚用户的数码安全助手。"
            "任务：分析截图/图片中是否存在诈骗、钓鱼、勒索、冒充银行/政府、可疑转账等迹象。"
            "不要把不确定的内容当成事实，使用“可能/疑似”。"
            "给出适用于马来西亚的具体行动步骤。\n\n"
            "必须只输出符合给定结构的 JSON。\n"
        )
    if lang == "TA":
        return (
            "நீங்கள் மலேசியாவுக்கான டிஜிட்டல் பாதுகாப்பு உதவியாளர். "
            "பணி: ஸ்கிரீன்‌ஷாட்/படத்தில் மோசடி, ஃபிஷிங், மிரட்டல், வங்கி/அரசு போலி, சந்தேகமான பரிவர்த்தனை சான்றுகள் உள்ளதா என்பதை பார்க்கவும். "
            "நிச்சயமில்லாததை உண்மையாக கூற வேண்டாம்; 'இருக்கலாம்' என்று சொல்லவும். "
            "மலேசியா சூழலில் உடனடி நடவடிக்கை படிகளை கூறவும்.\n\n"
            "கொடுக்கப்பட்ட கட்டமைப்பில் JSON மட்டும் வெளியிடவும்.\n"
        )
    return (
        "You are a digital safety assistant for Malaysia. "
        "Task: analyse the screenshot/image for scam/phishing/extortion/impersonation/red flags. "
        "Do not present uncertain claims as facts; use 'likely'/'possible'. "
        "Give practical Malaysia-specific next steps.\n\n"
        "You MUST output JSON only matching the schema.\n"
    )

JSON_SCHEMA = {
    "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
    "scam_type_guess": "string",
    "what_ai_sees": ["bullet strings"],
    "red_flags": ["bullet strings"],
    "why_it_looks_like_a_scam": "short string",
    "what_to_do_now": ["step strings"],
    "who_to_contact_malaysia": [
        {"name": "string", "phone": "string", "url": "string"}
    ],
    "safe_reply_suggestion": "string",
    "confidence": "0-100 integer",
    "disclaimer": "string"
}

@app.post("/analyze", response_model=AnalyzeOut)
def analyze(payload: AnalyzeIn):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing on server")

    lang = normalise_lang(payload.lang or "EN")

    b64 = strip_data_url_prefix(payload.image_data_url)
    if not b64 or len(b64) < 50:
        raise HTTPException(status_code=400, detail="image_data_url is empty/invalid")

    # Guardrail: avoid huge payloads
    if len(b64) > 6_000_000:
        raise HTTPException(status_code=413, detail="Image too large. Please use a smaller screenshot.")

    system = build_prompt(lang)

    contacts = [
        {"name": MALAYSIA_RESOURCES["NSRC"]["name"], "phone": MALAYSIA_RESOURCES["NSRC"]["phone"], "url": ""},
        {"name": MALAYSIA_RESOURCES["CCID_SRC"]["name"], "phone": MALAYSIA_RESOURCES["CCID_SRC"]["phone"], "url": ""},
        {"name": MALAYSIA_RESOURCES["BNM"]["name"], "phone": MALAYSIA_RESOURCES["BNM"]["phone"], "url": "https://www.bnm.gov.my"},
        {"name": MALAYSIA_RESOURCES["PDRM_SEMAKMULE"]["name"], "phone": "", "url": MALAYSIA_RESOURCES["PDRM_SEMAKMULE"]["url"]},
    ]

    user = (
        "Return JSON ONLY with these keys:\n"
        f"{list(JSON_SCHEMA.keys())}\n\n"
        "Rules:\n"
        "- Keep it short and actionable.\n"
        "- Include Malaysia contacts in who_to_contact_malaysia.\n"
        "- If money already transferred, prioritise immediate action steps.\n"
        "- safe_reply_suggestion: a short reply the user can send to the scammer (to stall / refuse safely).\n"
        "- disclaimer: include that this is guidance, not legal/financial advice.\n\n"
        f"who_to_contact_malaysia must include these:\n{contacts}\n"
    )

    try:
        resp = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{b64}",
                        },
                    ],
                },
            ],
            max_output_tokens=900,
        )
        text = resp.output_text.strip()
        # Ensure it's JSON-ish
        if not (text.startswith("{") and text.endswith("}")):
            raise ValueError("Model did not return JSON")
        return {"result": {"lang": lang, "analysis": text}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {str(e)}")
