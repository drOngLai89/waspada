import os
import base64
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI()

APP_VERSION = os.environ.get("APP_VERSION", "dev")
AS_OF_DATE = "27 Dec 2025"

MALAYSIA_CHANNELS = {
    "urgent_money_moved": [
        {"name": "NSRC (National Scam Response Centre)", "type": "phone", "value": "997", "note": "Call immediately if money has moved."},
        {"name": "Your bank 24/7 hotline", "type": "text", "value": "Call your bank’s official hotline immediately if you can’t get through to 997."},
    ],
    "pdrm_ccid": [
        {"name": "CCID Infoline (WhatsApp)", "type": "whatsapp", "value": "+60132111222"},
        {"name": "CCID Scam Response Centre", "type": "phone", "value": "+60326101559"},
        {"name": "CCID Scam Response Centre (alt)", "type": "phone", "value": "+60326101599"},
        {"name": "Semak Mule (CCID portal)", "type": "url", "value": "https://semakmule.rmp.gov.my/"},
    ],
    "cyber_incident": [
        {"name": "Cyber999 (MyCERT) hotline", "type": "phone", "value": "+601300882999"},
        {"name": "Cyber999 (MyCERT) emergency 24x7", "type": "phone", "value": "+60192665850"},
        {"name": "Cyber999 (MyCERT) email", "type": "email", "value": "cyber999@cybersecurity.my"},
    ],
    "mcmc_content_telco": [
        {"name": "MCMC hotline", "type": "phone", "value": "+601800188030"},
        {"name": "MCMC WhatsApp", "type": "whatsapp", "value": "+60162206262"},
        {"name": "MCMC email", "type": "email", "value": "aduanskmm@mcmc.gov.my"},
        {"name": "MCMC portal", "type": "url", "value": "https://aduan.skmm.gov.my/"},
    ],
}

SYSTEM_PROMPT = f"""
You are Waspada, a Malaysia-only anti-scam assistant.
Today is {AS_OF_DATE}. You must ONLY provide advice relevant to Malaysia.

Important:
- Do NOT invent hotlines, portals, laws, or agencies. Use ONLY the reporting channels I provide.
- If the screenshot contains personal data (IC/passport/account numbers), advise the user to redact before sharing further.
- Your job: (1) read the screenshot, (2) identify scam signals, (3) extract key entities, (4) give clear “do now” steps.

Return STRICT JSON only with this schema:
{{
  "risk_level": "low|medium|high|critical",
  "scam_type": "string",
  "summary": "string",
  "red_flags": ["string", "..."],
  "extracted": {{
    "phones": ["string", "..."],
    "urls": ["string", "..."],
    "bank_accounts": ["string", "..."],
    "names": ["string", "..."],
    "amounts": ["string", "..."]
  }},
  "do_now": ["string", "..."],
  "dont_do": ["string", "..."],
  "reporting": {{
    "urgent_money_moved": [{{"name":"", "type":"", "value":"", "note":""}}],
    "pdrm_ccid": [{{"name":"", "type":"", "value":"", "note":""}}],
    "cyber_incident": [{{"name":"", "type":"", "value":"", "note":""}}],
    "mcmc_content_telco": [{{"name":"", "type":"", "value":"", "note":""}}]
  }},
  "disclaimer": "string"
}}

When recommending reporting actions:
- If money has moved: start with NSRC 997 and bank hotline immediately.
- Always remind: do not share OTP/TAC/password; banks/authorities will not ask for OTP.
"""

@app.get("/")
def home():
    return "Waspada backend is running ✅", 200

@app.get("/version")
def version():
    return jsonify(
        version=APP_VERSION,
        as_of=AS_OF_DATE,
        server_time=datetime.utcnow().isoformat() + "Z",
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
    data = request.get_json(silent=True) or {}
    image_b64 = (data.get("image_base64") or "").strip()
    user_note = (data.get("note") or "").strip()

    if not image_b64:
        return jsonify(error="Missing 'image_base64'"), 400

    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    # Guardrails: avoid gigantic payloads
    if len(image_b64) > 12_000_000:
        return jsonify(error="Image too large. Please send a smaller screenshot."), 413

    # Accept both raw base64 and data URLs
    if image_b64.startswith("data:"):
        data_url = image_b64
    else:
        data_url = f"data:image/jpeg;base64,{image_b64}"

    user_prompt = f"""
Analyse this screenshot for scam signals and give Malaysia-only guidance.

User note (optional):
{user_note}

You MUST use ONLY these reporting channels:

{MALAYSIA_CHANNELS}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
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

        # We expect strict JSON; if the model returns extra text, fail loudly
        if not out.startswith("{"):
            return jsonify(error="Model did not return JSON", raw=out), 502

        return jsonify(result=out), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

