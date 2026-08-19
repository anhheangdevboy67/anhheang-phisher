import os
import json
import time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# These are auto-set once you connect a KV (Upstash Redis) database
# to this project in the Vercel dashboard -> Storage tab.
KV_URL = os.environ.get("KV_REST_API_URL", "")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN", "")
MESSAGES_KEY = "anhheang_inbox_messages"


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def kv_command(*args):
    """Send a single Redis command to Upstash's REST API."""
    resp = requests.post(
        KV_URL,
        headers={"Authorization": f"Bearer {KV_TOKEN}"},
        json=list(args),
        timeout=8,
    )
    resp.raise_for_status()
    return resp.json().get("result")


def load_messages():
    if not KV_URL or not KV_TOKEN:
        return []
    try:
        result = kv_command("GET", MESSAGES_KEY)
        return json.loads(result) if result else []
    except Exception:
        return []


def save_messages(messages):
    if not KV_URL or not KV_TOKEN:
        return
    kv_command("SET", MESSAGES_KEY, json.dumps(messages))


@app.route("/api/messages", methods=["GET"])
def get_messages():
    return jsonify(load_messages())


@app.route("/api/messages", methods=["POST"])
def post_message():
    if not KV_URL or not KV_TOKEN:
        return jsonify({"error": "No database connected yet. Add Vercel KV in the dashboard."}), 500

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()[:60]
    message = str(data.get("message", "")).strip()[:600]

    if not name or not message:
        return jsonify({"error": "name and message are required"}), 400

    messages = load_messages()
    entry = {
        "name": name,
        "message": message,
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    messages.append(entry)
    save_messages(messages)

    return jsonify(entry), 201
