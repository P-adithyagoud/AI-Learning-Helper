import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Must be before any os.getenv() calls

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from services.ai_service import generate_learning_plan

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Allow all origins so the browser can call the API from any context
CORS(app, resources={r"/*": {"origins": "*"}})

VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}


def validate_plan_request(data):
    if not data:
        return "Invalid JSON strictly structured payload required."
        
    skill = data.get("skill")
    if not skill or not isinstance(skill, str) or len(skill.strip()) < 3:
        return "Skill must be at least 3 characters long."

    level = data.get("level")
    if level not in VALID_LEVELS:
        return f"Level must be one of: {', '.join(VALID_LEVELS)}"

    try:
        daily_hours = float(data.get("daily_hours"))
        if not (1 <= daily_hours <= 10):
            return "Daily hours must be between 1 and 10."
    except (TypeError, ValueError):
        return "Daily hours must be a number between 1 and 10."

    return None


@app.route("/health", methods=["GET"])
def health_check():
    api_key = os.getenv("GROQ_API_KEY", "")
    key_set = bool(api_key) and api_key != "your_groq_api_key_here"
    return jsonify({"status": "ok", "groq_api_key_configured": key_set})


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    try:
        data = request.get_json(silent=True)
        error = validate_plan_request(data)
        if error:
            return jsonify({"detail": error}), 422

        skill = data["skill"].strip()
        level = data["level"]
        daily_hours = float(data["daily_hours"])

        logger.info(f"Plan request: skill={skill}, level={level}, hours={daily_hours}")
        
        result = generate_learning_plan(skill, level, daily_hours)
        
        if "error" in result:
            return jsonify({"detail": result["error"]}), 502
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Fatal endpoint error: {e}\n{error_trace}")
        return jsonify({"detail": f"Server crash: {str(e)}", "trace": error_trace}), 400


# Serve the frontend — index.html at root "/"
@app.route("/", methods=["GET"])
def serve_frontend():
    return send_file(os.path.join(os.path.dirname(__file__), "index.html"))

@app.route("/login", methods=["GET"])
def serve_login():
    return send_file(os.path.join(os.path.dirname(__file__), "login.html"))

@app.route("/api/signin", methods=["POST"])
def api_signin():
    data = request.get_json(silent=True)
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"success": False, "message": "Email and password required"}), 400
    
    # Mock logic: extract name from email
    email = data.get("email")
    name = email.split("@")[0].capitalize()
    return jsonify({"success": True, "message": "Successfully signed in", "token": "mock-jwt-token", "name": name})

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True)
    if not data or not data.get("email") or not data.get("password") or not data.get("name"):
        return jsonify({"success": False, "message": "Name, email, and password required"}), 400
    
    # Mock logic: successful registration
    return jsonify({"success": True, "message": "Successfully registered. Please sign in."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
