import os
import json
import datetime as dt
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

AS_OF = "27 Dec 2025"

MALAYSIA_CHANNELS = [
    {
        "id": "nsrc_997",
        "name": "NSRC (National Scam Response Centre)",
        "type": "phone",
        "value": "997",
        "note": "Urgent if money already moved (bank transfer / online banking fraud).",
        "when": "Money already moved / unauthorised transfer / banking scam"
    },
    {
        "id": "bank_hotline",
        "name": "Your bank 24/7 hotline",
        "type": "generic",
        "value": "Call the number on your bank card / official website",
        "note": "If you can’t reach 997, call your bank immediately.",
        "when": "Money moved / account compromised"
    },
    {
        "id": "ccid_whatsapp",
        "name": "PDRM CCID Infoline (WhatsApp)",
        "type": "whatsapp",
        "value": "+60132111222",
        "note": "Report scam details / seek guidance.",
        "when": "Scam reports, mule accounts, impersonation scams"
    },
    {
        "id": "ccid_phone_1",
        "name": "PDRM CCID Scam Response Centre",
        "type": "phone",
        "value": "+60326101559",
        "note": "Commercial crime / scam response line.",
        "when": "Scam reports, mule accounts"
    },
    {
        "id": "ccid_phone_2",
        "name": "PDRM CCID Scam Response Centre (alt)",
        "type": "phone",
        "value": "+60326101599",
        "note": "Alternative number.",
        "when": "Scam reports, mule accounts"
    },
    {
        "id": "semakmule",
        "name": "Semak Mule (PDRM CCID portal)",
        "type": "url",
        "value": "https://semakmule.rmp.gov.my/",
        "note": "Check suspicious bank accounts/phone numbers before paying.",
        "when": "Before paying / verifying a suspicious account"
    },
    {
        "id": "cyber999_hotline",
        "name": "Cyber999 (MyCERT) Hotline",
        "type": "phone",
        "value": "+601300882999",
        "note": "Phishing / malware / suspicious links / cyber incidents.",
        "when": "Clicked link, installed app, malware, data breach"
    },
    {
        "id": "cyber999_emergency",
        "name": "Cyber999 Emergency (24x7)",
        "type": "phone",
        "value": "+60192665850",
        "note": "Urgent phishing/data breach escalation.",
        "when": "Active compromise / urgent cyber incident"
    },
    {
        "id": "cyber999_email",
        "name": "Cyber999 Email",
        "type": "email",
        "value": "cyber999@cybersecurity.my",
        "note": "Send evidence/screenshots and incident details.",
        "when": "Phishing, malware, suspicious content"
    },
    {
        "id": "mcmc_hotline",
        "name": "MCMC Hotline",
        "type": "phone",
        "value": "+601800188030",
        "note": "Scam ads / harmful online content / telco-related complaints.",
        "when": "Scam ads, SMS scams, telco issues"
    },
    {
        "id": "mcmc_whatsapp",
        "name": "MCMC WhatsApp",
        "type": "whatsapp",
        "value": "+60162206262",
        "note": "Report scam content/complaints.",
        "when": "Scam ads, SMS scams"
    },
    {
        "id": "mcmc_email",
        "name": "MCMC Email",
        "type": "email",
        "value": "aduanskmm@mcmc.gov.my",
        "note": "Formal complaints with attachments.",
        "when": "Scam ads, harmful content"
    },
    {
        "id": "mcmc_portal",
        "name": "MCMC Complaint Portal",
        "type": "url",
        "value": "https://aduan.skmm.gov.my/",
        "note": "Online complaint submission.",
        "when": "Scam ads, harmful content"
    },
]

def now_iso():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

@app.get("/version")
def version():
    return jsonify(
        as_of=AS_OF,
        server_time=now_iso(),
        version=os.environ.get("RENDER_GIT_COMMIT", "dev")[:7] if os.environ.get("RENDER_GIT_COMMIT") else "dev",
        has_key=bool(os.environ.get("OPENAI_API_KEY"))
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

    image = (data.get("image_base64") or "").strip()
    note = (data.get("note") or "").strip()
    lang = (data.get("lang") or "EN").strip().upper()

    if not image:
        return jsonify(error="Missing 'image_base64'"), 400
    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    # Accept either a full data URL or raw base64
    if image.startswith("data:image/"):
        data_url = image
    else:
        data_url = "data:image/jpeg;base64," + image

    # Guard against insanely large payloads (Render/proxy can choke)
    if len(data_url) > 6_000_000:
        return jsonify(error="Image too large. Please use a smaller screenshot (we will compress on device)."), 413

    # Language hints (UI language, NOT perfect legal translation)
    lang_name = {
        "EN": "English",
        "MS": "Bahasa Melayu",
        "ZH": "中文（简体/通用）",
        "TA": "தமிழ்"
    }.get(lang, "English")

    # System prompt: force JSON only (no markdown), Malaysia-only action guidance
    SYSTEM_PROMPT = f"""
You are Waspada, a Malaysia-only scam screenshot analysis assistant.

Return STRICT JSON only. No markdown, no code fences, no extra text.
Output language: {lang_name}. Keep short labels where needed.

You will be given:
- A screenshot image (may be scam, may be normal)
- An optional user note describing what happened.

Your job:
1) Explain what you can actually see in the image (signals, clues) in a grounded way.
2) Give a risk score + level.
3) Provide prescriptive steps: what to do NOW, next 24h, and what NOT to do.
4) Recommend who to contact (choose best 1-2 channels), but still include all Malaysia official channels list.
5) Tell the user how to preserve evidence (screenshots, bank refs, chats, URLs, app package names).
6) Be careful: you are not police/bank. Avoid claiming certainty. Use “may / likely” appropriately.

Use these Malaysia official channels (must include in output):
{json.dumps(MALAYSIA_CHANNELS, ensure_ascii=False)}
"""

    # Schema-ish contract (we use json_object response_format so it stays parseable)
    CONTRACT = """
Return JSON with exactly these top-level keys:

{
  "risk": { "level": "low|medium|high", "score": 0-100, "summary": "string", "reasons": ["..."] },
  "what_ai_sees": [
    { "signal": "string", "evidence_from_image": "string", "why_it_matters": "string" }
  ],
  "diagnosis": {
    "likely_scam_type": "string",
    "confidence": 0-100,
    "explanation": "string"
  },
  "what_to_do_now": {
    "top_actions": ["..."], 
    "next_24_hours": ["..."],
    "do_not_do": ["..."]
  },
  "recommended_contacts": {
    "primary": { "id": "string", "why": "string" },
    "secondary": { "id": "string", "why": "string" }
  },
  "channels": [ ...the channel objects provided... ],
  "evidence_to_save": ["..."],
  "user_message": "short reassuring line"
}
"""

    user_prompt = f"""
User note: {note if note else "(none)"}

Follow the contract below and stay Malaysia-only.
{CONTRACT}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
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

        # Parse to ensure valid JSON
        try:
            obj = json.loads(out)
        except Exception:
            return jsonify(error="Bad JSON from model", raw=out), 502

        # Ensure channels always present (fallback)
        if "channels" not in obj:
            obj["channels"] = MALAYSIA_CHANNELS

        return jsonify(result=obj, server_time=now_iso()), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
