import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.get("/")
def home():
    return "Waspada backend is running ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")

    if not prompt:
        return jsonify(error="Missing 'prompt'"), 400

    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify(error="OPENAI_API_KEY not set on server"), 500

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )
        # responses API returns text in output_text
        return jsonify(output=resp.output_text), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
