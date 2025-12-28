import os
import json
import time
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Slightly longer client-side timeout helps too (Render timeout is separate)
client = OpenAI(timeout=90.0)

AS_OF = "27 Dec 2025"


def extract_json_anywhere(text: str):
    if not text:
        return None
    t = text.strip()

    # Strip ``` fences if present
    if t.startswith("```"):
        lines = t.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
        if t.lower().startswith("json"):
            t = t[4:].strip()

    a = t.find("{")
    b = t.rfind("}")
    if a == -1 or b == -1 or b <= a:
        return None

    candidate = t[a:b + 1].strip()
    try:
        return json.loads(candidate)
    except:
        return None


@app.get("/version")
def version():
    return jsonify(
        as_of=AS_OF,
        server_time=datetime.datetime.utcnow().isoformat() + "Z",
        version="dev",
    ), 200


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    image_base64 = (data.get("image_base64") or "").strip()
    note = (data.get("note") or "").strip()
    lang = (data.get("lang") or "en").strip().lower()

    if not image_base64:
        return jsonify(error="Missing image_base64"), 400

    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    if image_base64.startswith("data:"):
        data_url = image_base64
    else:
        data_url = f"data:image/jpeg;base64,{image_base64}"

    channels = [
        {"id": "nsrc_997", "title": "NSRC Hotline", "value": "997", "type": "call", "note": "If money already moved, call 997 immediately."},
        {"id": "ccid_whatsapp", "title": "CCID WhatsApp", "value": "+60132111222", "type": "whatsapp", "note": "Send details/screenshots via WhatsApp if needed."},
        {"id": "ccid_call", "title": "CCID Scam Response Centre", "value": "03-26101559", "type": "call", "note": "Alternative CCID phone line."},
        {"id": "semak_mule", "title": "Semak Mule", "value": "https://semakmule.rmp.gov.my", "type": "url", "note": "Check suspicious bank accounts/phone numbers."},
        {"id": "cyber999", "title": "Cyber999 (MyCERT)", "value": "1300882999", "type": "call", "note": "Report phishing/malware/cyber incidents."},
        {"id": "mcmc", "title": "MCMC Aduan", "value": "https://aduan.skmm.gov.my", "type": "url", "note": "Report scam ads / harmful online content."},
    ]

    system = f"""
You are Waspada, a Malaysia-only scam screenshot assistant.
Return ONLY valid JSON. No markdown. No backticks. No extra text.
Be diagnostic and prescriptive. Explain what you can see in the image and why it is risky.
Language: {lang} (en/ms/zh/ta). Use that language in all fields.
""".strip()

    user = f"""
User note (optional): {note or "(none)"}

Return JSON with this shape:

{{
  "risk": {{ "level": "low|medium|high|critical", "score": 0-100, "summary": "..." }},
  "likely_scam_type": {{ "label": "...", "confidence": 0-100, "reasoning": "..." }},
  "what_ai_sees": [
    {{ "signal": "...", "evidence_from_image": "...", "why_it_matters": "...", "risk_impact": "low|medium|high" }}
  ],
  "what_to_do_now": [
    {{ "step": 1, "title": "...", "detail": "..." }}
  ],
  "recommended_contact": {{
    "primary": {{ "id": "nsrc_997|ccid_whatsapp|cyber999|mcmc|semak_mule", "why": "..." }},
    "others": [ {{ "id": "...", "why": "..." }} ]
  }},
  "evidence_checklist": ["...", "..."],
  "questions_to_confirm": ["...", "..."],
  "disclaimer": "..."
}}

Rules:
- Provide at least 5 what_ai_sees items based on the screenshot (not the note).
- Provide 6-10 what_to_do_now steps, ordered.
- recommended_contact.primary.id must be one of the ids listed above.
""".strip()

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    last_err = None
    for attempt in range(1, 4):  # 3 tries
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
            )
            out = (resp.choices[0].message.content or "").strip()
            obj = extract_json_anywhere(out)

            if not isinstance(obj, dict):
                return jsonify(error="Model did not return JSON", raw=out[:2000]), 502

            return jsonify(result=obj, channels=channels), 200

        except Exception as e:
            last_err = str(e)
            # short backoff and retry
            time.sleep(0.6 * attempt)

    return jsonify(error="Upstream error (OpenAI/timeout). Try again.", detail=last_err), 502


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
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = (resp.choices[0].message.content or "").strip()
        return jsonify(output=text), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
