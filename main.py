import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Must be before any os.getenv() calls

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from services.ai_service import generate_learning_plan

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
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


# Logic for form-based production rendering
@app.route("/generate-playlists", methods=["POST"])
def generate_playlists():
    # Detect if request is JSON or Form
    is_json = request.is_json
    if is_json:
        data = request.get_json(silent=True)
    else:
        data = request.form.to_dict()

    error = validate_plan_request(data)
    if error:
        if is_json:
            return jsonify({"detail": error}), 422
        return f"<h1>Error</h1><p>{error}</p><a href='/'>Back</a>", 422

    skill = data["skill"].strip()
    level = data["level"]
    daily_hours = float(data["daily_hours"])

    # Logic for JSON processing (AJAX driven)
    result = generate_learning_plan(skill, level, daily_hours)

    if "error" in result:
        return jsonify({"detail": result["error"]}), 502

    return jsonify(result)


# Serve the Dashboard — native Flask template
@app.route("/", methods=["GET"])
def serve_dashboard():
    return render_template("index.html")


@app.route("/login", methods=["GET"])
def serve_login():
    return render_template("login.html")


@app.route("/logout")
def logout():
    # Placeholder for session cleanup
    return redirect("/login")


if __name__ == "__main__":
    from flask import render_template, redirect
    app.run(host="0.0.0.0", port=8000, debug=True)
