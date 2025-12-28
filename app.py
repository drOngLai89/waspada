import os, json, base64, re
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

AS_OF = "27 Dec 2025"

LANG_NAMES = {
    "en": "English",
    "ms": "Bahasa Melayu",
    "zh": "中文（简体）",
    "ta": "தமிழ்",
}

# Malaysia official-ish channels (hard-coded, stable)
CHANNELS = [
    {
        "id": "nsrc_997",
        "title": "NSRC 997",
        "subtitle": "If money moved / urgent banking scam",
        "action": "call",
        "value": "997",
        "note": "Call immediately. If cannot get through, call your bank’s 24/7 hotline."
    },
    {
        "id": "ccid_whatsapp",
        "title": "CCID Infoline (WhatsApp)",
        "subtitle": "Report scam details / commercial crime",
        "action": "whatsapp",
        "value": "+60132111222",
        "note": "Text-only channel for scam details."
    },
    {
        "id": "ccid_phone",
        "title": "CCID Scam Response Centre",
        "subtitle": "Phone hotline (PDRM CCID)",
        "action": "call",
        "value": "03-2610 1559 / 03-2610 1599",
        "note": "Use when you need to speak to CCID."
    },
    {
        "id": "semakmule",
        "title": "Semak Mule",
        "subtitle": "Check mule accounts / numbers before paying",
        "action": "url",
        "value": "https://semakmule.rmp.gov.my/",
        "note": "Verify account/phone/company before transfer."
    },
    {
        "id": "cyber999",
        "title": "Cyber999 (MyCERT)",
        "subtitle": "Phishing/malware/data breach",
        "action": "call",
        "value": "1-300-88-2999",
        "note": "Also email cyber999@cybersecurity.my"
    },
    {
        "id": "mcmc",
        "title": "MCMC Aduan",
        "subtitle": "Scam ads / SMS / telco issues / harmful content",
        "action": "call",
        "value": "1800-188-030",
        "note": "Also WhatsApp 016-2206 262, portal aduan.skmm.gov.my"
    },
]

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def strip_data_url(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("data:"):
        # data:image/png;base64,xxxx
        try:
            return s.split(",", 1)[1]
        except Exception:
            return s
    return s

def to_data_url(base64_str: str) -> str:
    # default jpeg
    return "data:image/jpeg;base64," + base64_str

def safe_lang(lang: str) -> str:
    lang = (lang or "en").lower().strip()
    return lang if lang in LANG_NAMES else "en"

SYSTEM_PROMPT_TEMPLATE = """You are Waspada, an anti-scam assistant for Malaysia.
You analyse a screenshot of a suspected scam and respond with STRICT JSON ONLY.

Rules:
- Malaysia-only guidance and channels.
- Be diagnostic and prescriptive: explain what you see in the image, why it matters, and what to do now.
- Do NOT invent facts not visible from the screenshot. If unsure, say "unclear" and explain what is missing.
- The user may include a short note (context).
- Output language: {LANG_NAME}. Use the same language in all narrative fields.
- Keep hotlines and numbers exactly as Malaysia channels.
- Avoid legal overclaims. This is safety guidance, not legal advice.

You MUST return JSON with this exact top-level structure:

{{
  "risk": {{
    "level": "low|medium|high|critical",
    "score": 0-100,
    "summary": "1-2 lines"
  }},
  "what_ai_sees": [
    {{
      "signal": "short label",
      "evidence_from_image": "what in the screenshot triggered it (quote/describe)",
      "why_it_matters": "why this signal is risky"
    }}
  ],
  "likely_scam_type": {{
    "label": "e.g., bank impersonation / parcel / investment / job / loan / romance / crypto / malware / unknown",
    "confidence": 0-100,
    "reasoning": "short"
  }},
  "questions_to_confirm": [
    "up to 5 short questions that would reduce uncertainty (no personal data requests)"
  ],
  "what_to_do_now": [
    {{
      "step": 1,
      "title": "short",
      "detail": "specific actions, not generic"
    }}
  ],
  "recommended_contact": {{
    "primary": {{
      "id": "nsrc_997|ccid_whatsapp|ccid_phone|semakmule|cyber999|mcmc",
      "why": "why this is the best first contact for this case"
    }},
    "secondary": [
      {{
        "id": "one of the ids above",
        "why": "when to use it"
      }}
    ]
  }},
  "evidence_checklist": [
    "what to screenshot/save (transaction ref, phone number, account number, chat, URLs, etc.)"
  ],
  "safe_message_to_send_scammer": "Optional: a short message to disengage safely (or empty string)",
  "disclaimer": "Short disclaimer line"
}}

Keep it grounded. Ensure JSON is valid (double quotes, no trailing commas).
"""

@app.get("/version")
def version():
    return jsonify(
        as_of=AS_OF,
        server_time=now_iso(),
        version=os.environ.get("RENDER_GIT_COMMIT", "dev")[:7] if os.environ.get("RENDER_GIT_COMMIT") else "dev",
        has_key=bool(os.environ.get("OPENAI_API_KEY")),
    ), 200

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify(error="Missing 'prompt'"), 400
    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = (resp.choices[0].message.content or "").strip()
        return jsonify(output=text), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/analyze")
def analyze():
    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    data = request.get_json(silent=True) or {}
    img = data.get("image_base64") or ""
    note = (data.get("note") or "").strip()
    lang = safe_lang(data.get("lang") or "en")
    lang_name = LANG_NAMES.get(lang, "English")

    b64 = strip_data_url(img)
    if not b64:
        return jsonify(error="Missing 'image_base64'"), 400

    # Basic sanity check to avoid junk
    if len(b64) < 1000:
        return jsonify(error="Image too small / invalid base64"), 400

    data_url = to_data_url(b64)

    # Include channels in-context so model can pick an ID
    channels_brief = [{"id": c["id"], "title": c["title"], "subtitle": c["subtitle"]} for c in CHANNELS]

    user_prompt = f"""User note (context, may be empty):
{note if note else "(none)"}

Available Malaysia channels (choose ids exactly):
{json.dumps(channels_brief, ensure_ascii=False)}

Task:
Analyse the screenshot for scam indicators. Provide diagnostic signals grounded in what is visible.
Then give prescriptive next steps and recommend the best contact channel id(s) for this case.
"""

    system_prompt = SYSTEM_PROMPT_TEMPLATE.replace("{LANG_NAME}", lang_name)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )

        out = (resp.choices[0].message.content or "").strip()

        # Strict JSON enforcement
        if not out.startswith("{"):
            return jsonify(error="Model did not return JSON", raw=out), 502

        # Validate JSON now so frontend isn't guessing
        try:
            obj = json.loads(out)
        except Exception:
            return jsonify(error="Invalid JSON from model", raw=out), 502

        # Attach channels so app can render "call now" buttons reliably
        return jsonify(result=obj, channels=CHANNELS), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
