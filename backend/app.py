"""
app.py — Flask API server for the Career Guidance Chatbot
Run:  python app.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# ── Add backend folder to path ────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatbot import CareerChatbot

# ── App setup ─────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR  = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ── Load chatbot once at startup ──────────────────────────────────────────────
print("🚀 Loading Career Guidance Chatbot...")
chatbot = CareerChatbot()
print("✅ Chatbot ready!")

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the frontend website."""
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint."""
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = str(data["message"]).strip()

    if len(user_message) > 500:
        return jsonify({"error": "Message too long (max 500 characters)"}), 400

    result = chatbot.get_response(user_message)

    return jsonify({
        "response":   result["response"],
        "intent":     result["intent"],
        "confidence": result["confidence"],
        "status":     "success"
    })

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Career Guidance Chatbot is running!"})

@app.route("/api/intents", methods=["GET"])
def get_intents():
    """Return list of available intent tags (for info/debug)."""
    tags = [intent["tag"] for intent in chatbot.intents]
    return jsonify({"intents": tags, "count": len(tags)})

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  🎓 Career Guidance Chatbot Server")
    print("=" * 55)
    print(f"  Frontend : http://127.0.0.1:5000")
    print(f"  API      : http://127.0.0.1:5000/api/chat")
    print(f"  Health   : http://127.0.0.1:5000/api/health")
    print("=" * 55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
