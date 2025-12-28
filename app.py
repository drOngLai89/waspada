import os
import json
import base64
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI()

AS_OF = "27 Dec 2025"

# Malaysia official channels (you can add more later)
CHANNELS = [
    {
        "id": "nsrc_hotline",
        "title": "NSRC (National Scam Response Centre)",
        "subtitle": "15999 (Malaysia)",
        "action": "call",
        "value": "15999",
        "note": "If money was transferred recently, call NSRC first. They can coordinate urgent response with banks."
    },
    {
        "id": "ccid_997",
        "title": "CCID Scam Response (PDRM)",
        "subtitle": "997 (Malaysia)",
        "action": "call",
        "value": "997",
        "note": "Police hotline for scam reporting guidance. Use if you need immediate advice or to be routed to the right unit."
    },
    {
        "id": "ccid_whatsapp",
        "title": "CCID WhatsApp (PDRM)",
        "subtitle": "+60 13-211 1222",
        "action": "whatsapp",
        "value": "+60132111222",
        "note": "Submit scam details and screenshots via WhatsApp if needed."
    },
    {
        "id": "tng_careline",
        "title": "Touch 'n Go eWallet Careline",
        "subtitle": "If the screenshot involves eWallet transfers",
        "action": "url",
        "value": "https://www.touchngo.com.my/customer-service/",
        "note": "Use if your case involves TNG eWallet. (Official help page)"
    },
    {
        "id": "maybank_help",
        "title": "Maybank: Fraud / Scam Help",
        "subtitle": "If your bank is Maybank",
        "action": "url",
        "value": "https://www.maybank2u.com.my/",
        "note": "Use your bank’s official hotline / app to freeze access and report fraud."
    },
]

# JSON schema the model must follow
RESULT_SCHEMA = {
    "name": "waspada_scam_analysis",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "risk": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "summary": {"type": "string"}
                },
                "required": ["level", "score", "summary"]
            },
            "likely_scam_type": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "label": {"type": "string"},
                    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                    "reasoning": {"type": "string"}
                },
                "required": ["label", "confidence", "reasoning"]
            },
            "what_ai_sees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "signal": {"type": "string"},
                        "evidence_from_image": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "risk_impact": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["signal", "evidence_from_image", "why_it_matters", "risk_impact"]
                }
            },
            "what_to_do_now": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "step": {"type": "integer", "minimum": 1, "maximum": 20},
                        "title": {"type": "string"},
                        "detail": {"type": "string"}
                    },
                    "required": ["step", "title", "detail"]
                }
            },
            "questions_to_confirm": {
                "type": "array",
                "items": {"type": "string"}
            },
            "evidence_checklist": {
                "type": "array",
                "items": {"type": "string"}
            },
            "recommended_contact": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "primary": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "id": {"type": "string"},
                            "why": {"type": "string"}
                        },
                        "required": ["id", "why"]
                    },
                    "others": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {"type": "string"},
                                "why": {"type": "string"}
                            },
                            "required": ["id", "why"]
                        }
                    }
                },
                "required": ["primary", "others"]
            },
            "disclaimer": {"type": "string"}
        },
        "required": [
            "risk",
            "likely_scam_type",
            "what_ai_sees",
            "what_to_do_now",
            "questions_to_confirm",
            "evidence_checklist",
            "recommended_contact",
            "disclaimer"
        ]
    }
}


def _data_url_from_base64(image_b64: str) -> str:
    # Allow either raw base64 or full data URL input
    if image_b64.startswith("data:"):
        return image_b64
    return f"data:image/jpeg;base64,{image_b64}"


def _extract_json_loose(text: str):
    """
    Backup: if model returns extra text, try to locate a JSON object inside.
    """
    if not text:
        return None
    t = text.strip()

    # remove code fences if present
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t else t
        t = t.replace("json", "").strip()

    # find first { ... last }
    a = t.find("{")
    b = t.rfind("}")
    if a == -1 or b == -1 or b <= a:
        return None

    candidate = t[a:b+1].strip()
    try:
        return json.loads(candidate)
    except:
        return None


@app.get("/version")
def version():
    return jsonify(
        as_of=AS_OF,
        server_time=datetime.datetime.utcnow().isoformat() + "Z",
        version=os.environ.get("RENDER_GIT_COMMIT", "dev")[:7] if os.environ.get("RENDER_GIT_COMMIT") else "dev"
    )


@app.post("/analyze")
def analyze():
    try:
        body = request.get_json(force=True) or {}
        image_b64 = (body.get("image_base64") or "").strip()
        note = (body.get("note") or "").strip()
        lang = (body.get("lang") or "en").strip().lower()

        if not image_b64:
            return jsonify(error="Missing image_base64"), 400

        if lang not in ["en", "ms", "zh", "ta"]:
            lang = "en"

        data_url = _data_url_from_base64(image_b64)

        # Decide recommended contact based on note hints (simple first)
        note_l = note.lower()
        if any(k in note_l for k in ["money", "transfer", "transferred", "duit", "pindah", "转账", "பணம்"]):
            primary_id = "nsrc_hotline"
            primary_why = "Money transfer indicated. NSRC is the fastest route for urgent bank coordination."
        else:
            primary_id = "ccid_997"
            primary_why = "No confirmed transfer. CCID hotline can advise next steps and proper reporting route."

        # System instruction tuned to be diagnostic + prescriptive
        system = f"""
You are Waspada, a Malaysia-only scam screenshot assistant.
You must produce a practical, diagnostic and prescriptive analysis based on what you can SEE in the screenshot.
Be specific: cite visible cues (names, numbers, URLs, payment instructions, urgency language, impersonation, fake UI, etc).
Do NOT invent details you cannot see.
Output must follow the JSON schema exactly.

Language:
- If lang=en: output English
- If lang=ms: output Bahasa Melayu
- If lang=zh: output Simplified Chinese
- If lang=ta: output Tamil

The recommended_contact.primary.id MUST be one of:
- nsrc_hotline
- ccid_997
- ccid_whatsapp

For what_to_do_now: give step-by-step actions that a real victim can do immediately in Malaysia.
For evidence_checklist: list concrete evidence items to keep (transaction ref, phone numbers, bank details, chat logs).
        """.strip()

        user_prompt = f"""
User note (optional): {note or "(none)"}

Your job:
1) Assess risk with score and clear summary.
2) Identify likely scam type with reasoning.
3) Provide "what_ai_sees": at least 5 items, each must cite evidence seen in screenshot.
4) Provide "what_to_do_now": 6-10 steps, Malaysia-specific, clear actions.
5) Provide questions_to_confirm: 5-8 short questions.
6) Provide evidence_checklist: 8-12 items.
7) recommended_contact: choose the best primary channel and explain why.
8) Add a short disclaimer.
        """.strip()

        # ✅ Force JSON output using response_format json_schema
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            response_format={
                "type": "json_schema",
                "json_schema": RESULT_SCHEMA
            },
            messages=[
                {"role": "system", "content": system},
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

        # With json_schema, content should be JSON. Still keep a backup extractor.
        try:
            result_obj = json.loads(out)
        except:
            result_obj = _extract_json_loose(out)

        if not isinstance(result_obj, dict):
            return jsonify(error="Model did not return JSON", raw=out[:2000]), 502

        # Inject our recommended contact defaults if model left it blank (shouldn't, but safe)
        if "recommended_contact" in result_obj and isinstance(result_obj["recommended_contact"], dict):
            if "primary" in result_obj["recommended_contact"]:
                # keep model choice if valid, else override
                pid = result_obj["recommended_contact"]["primary"].get("id", "")
                if pid not in ["nsrc_hotline", "ccid_997", "ccid_whatsapp"]:
                    result_obj["recommended_contact"]["primary"]["id"] = primary_id
                    result_obj["recommended_contact"]["primary"]["why"] = primary_why
            else:
                result_obj["recommended_contact"] = {
                    "primary": {"id": primary_id, "why": primary_why},
                    "others": [
                        {"id": "ccid_997", "why": "Police hotline guidance."},
                        {"id": "ccid_whatsapp", "why": "WhatsApp submission if needed."},
                    ],
                }

        return jsonify(result=result_obj, channels=CHANNELS), 200

    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
