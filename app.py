import os, json, re
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

AS_OF = "27 Dec 2025"

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = f"""
You are Waspada, a Malaysia-only anti-scam assistant. Today is {AS_OF}.

You will analyze a scam screenshot (chat/SMS/WhatsApp/email/bank screen/ads).
Return STRICT JSON only. No markdown. No extra commentary outside JSON.

Core goals:
- Be diagnostic: explain WHY the risk is what it is, referencing concrete cues visible in the screenshot.
- Be prescriptive: give step-by-step actions that the user can execute, with urgency and ordering.
- Malaysia context ONLY.

Do not invent hotlines/numbers. If uncertain, say "unknown" or "cannot confirm from screenshot".

Malaysia reporting channels (as-of {AS_OF}):
- NSRC hotline: 997 (National Scam Response Centre) for financial scams / transfers.
- Police (PDRM CCID/JSJK): WhatsApp 013-211 1222; phone 03-2610 1559 / 03-2610 1599
- Cyber999 (MyCERT): 1-300-88-2999; emergency +6019-266 5850; email cyber999@cybersecurity.my
- MCMC: 1800-188-030; WhatsApp 016-2206 262; email aduanskmm@mcmc.gov.my; portal aduan.skmm.gov.my

IMPORTANT:
- Banks/NSRC/police will never ask for OTP/TAC/password. Mention this in do_not_do.
- Do NOT give legal advice. Practical guidance only.

JSON schema to return (fill as much as possible):
{{
  "as_of": "{AS_OF}",
  "risk": {{
    "level": "LOW|MEDIUM|HIGH",
    "score": 0-100,
    "confidence": 0.0-1.0,
    "justification": "2-5 sentences explaining WHY this level/score, based on screenshot cues.",
    "key_indicators": [
      {{
        "indicator": "string (e.g., urgency / impersonation / link / payment request)",
        "evidence": "what in the screenshot supports it (quote/describe)",
        "severity": "LOW|MEDIUM|HIGH"
      }}
    ]
  }},
  "incident": {{
    "category": "bank_transfer|phishing_link|impersonation|investment|job|parcel|loan|marketplace|unknown",
    "money_moved": true|false|"unknown",
    "urgency": "IMMEDIATE|SOON|MONITOR",
    "why_this_category": "1-3 sentences mapping screenshot cues -> category."
  }},
  "what_i_can_see": {{
    "short_summary": "1-2 sentence plain summary.",
    "detailed_summary": "6-12 sentences, more substantiated, describing the story + cues from the screenshot.",
    "extracted": {{
      "phone_numbers": ["..."],
      "urls": ["..."],
      "bank_accounts": ["..."],
      "platforms": ["WhatsApp","SMS","Telegram","Email","Facebook","Instagram","Shopee","Lazada","TikTok","unknown"],
      "names_or_orgs": ["..."],
      "amounts": ["..."]
    }}
  }},
  "red_flags": ["More detailed bullets. Refer to screenshot cues where possible."],
  "what_to_do_now": [
    {{
      "priority": 1,
      "action": "Clear action statement",
      "why": "Why this matters",
      "how": "How to do it (steps)",
      "timeframe": "e.g., now / within 30 min / today"
    }}
  ],
  "do_not_do": ["..."],
  "save_as_evidence": [
    {{
      "item": "What to save",
      "how": "How to save it on phone",
      "why": "Why it helps reporting"
    }}
  ],
  "recommended_reporting_channels": [
    {{
      "id": "NSRC_997|BANK_HOTLINE|CCID_WHATSAPP|CCID_CALL|CYBER999|MCMC",
      "contact_first": true|false,
      "why": "Why this is the right channel given this case",
      "what_to_say": "Short script: what to tell them (facts to share)"
    }}
  ],
  "disclaimer": "Short safety disclaimer."
}}
"""

def _now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _extract_json(text: str):
    if not text:
        return None, "empty model output"
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None, "no JSON object found"
    blob = m.group(0)
    try:
        return json.loads(blob), None
    except Exception as e:
        return None, f"JSON parse error: {e}"

@app.get("/")
def root():
    return jsonify(ok=True, service="waspada-backend", time=_now_iso())

@app.get("/version")
def version():
    sha = (
        os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("GIT_COMMIT")
        or os.environ.get("COMMIT_SHA")
        or "unknown"
    )
    return jsonify(
        as_of=AS_OF,
        server_time=_now_iso(),
        version="dev",
        sha=sha,
        has_key=bool(os.environ.get("OPENAI_API_KEY")),
    )

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
    img = (data.get("image_base64") or "").strip()
    note = (data.get("note") or "").strip()

    if not img:
        return jsonify(error="Missing 'image_base64'"), 400
    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    if img.startswith("data:image"):
        data_url = img
    else:
        data_url = f"data:image/jpeg;base64,{img}"

    user_prompt = f"""
Analyze this screenshot for scam signals. Malaysia-only context.
User note (optional): {note if note else "(none)"}

Be diagnostic + prescriptive:
- Expand justifications (risk justification, incident mapping).
- Use evidence cues visible in screenshot (e.g., wording, link patterns, payment request, impersonation).
- Give ordered actions with timeframe.
- Recommend the best contact FIRST (contact_first=true), then secondary channels.

Return strict JSON following the schema.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1200,
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
        parsed, err = _extract_json(out)
        if err:
            return jsonify(error="Model did not return valid JSON", detail=err, raw=out), 502
        return jsonify(result=parsed), 200

    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
