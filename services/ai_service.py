import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
TIMEOUT = 60.0


def build_prompt(skill: str, level: str, daily_hours: float) -> str:
    return f"""You are an expert learning planner and curriculum designer.

Create a complete, structured, and realistic learning system.

---

INPUT:

* Skill: {skill}
* Level: {level}
* Daily Time: {daily_hours}
* Target Duration: auto

---

GOAL:

Generate a structured learning system divided into 4 sections:

1. Resources (what to learn from)
2. Roadmap (step-by-step execution)
3. Certifications (end goal)
4. Common Mistakes (guidance + awareness)

---

DURATION LOGIC:

* If user provides duration → strictly follow it

* If Target Duration = "auto":
  → calculate based on:

  * number of topics required to master the skill
  * user level (Beginner → more time, Advanced → less time)
  * daily available time

* Duration must be realistic and NOT fixed

* Allowed range: 2 to 12 weeks

---

CURRICULUM STRUCTURE RULES:

* Build COMPLETE roadmap from basics → intermediate → advanced
* Ensure logical progression (no skipping fundamentals)
* Cover all key concepts required for the skill

EDGE CASE HANDLING:

* If skill is too broad (e.g., "AI", "Programming"):
  → break into core foundational topics

* If skill is too niche:
  → focus on fundamental concepts and practical understanding

---

RESOURCE RULES (UPGRADED — VERY IMPORTANT):

Instead of random video links, provide structured learning sources.

---

YOUTUBE CHANNELS:

* Provide TOP 5 high-quality YouTube channels for the given skill

Each channel must include:

* channel_name

* coverage_level:
  (Basic / Intermediate / Advanced / Full)

* description (what they teach in 1 line)

* link (channel link, NOT individual videos)

* Prefer:

  * well-known, trusted channels
  * channels with structured playlists

---

PRACTICE PLATFORMS:

* Provide 3–5 coding/practice platforms

Each platform must include:

* name
* purpose (e.g., DSA practice, beginner coding, contests)
* link

---

ROADMAP RULES (UPDATED — VERY IMPORTANT):

The roadmap is for EXECUTION ONLY, not for learning resources.

---

STRUCTURE:

* Organize as:
  Week → Days

* Each week must have 5–7 days

---

EACH DAY MUST INCLUDE:

* day (number)
* topic (clear and specific)
* plan (what exactly to do that day in simple steps)
* practice_platform (if applicable)
* task (clear action task)

---

STRICT RULES:

* DO NOT include any links in the roadmap
* DO NOT include YouTube or article references
* DO NOT repeat resources from the resources section
* Focus only on:
  * what to study
  * what to practice
  * what to complete

---

PLAN FORMAT (IMPORTANT):

The "plan" field should describe:
* what to learn
* what to practice
* how to approach the topic

Example:
"plan": "Understand variables and data types. Practice writing small programs using int, float, and strings."

---

CERTIFICATION RULES:

* ALWAYS include 2–3 FREE certification platforms
* Must be:

  * relevant to the skill
  * actually free
  * useful for learners

---

COMMON MISTAKES RULES:

* Provide 5–8 realistic mistakes learners make
* Must be:

  * practical
  * specific
  * actionable

---

ANTI-REPETITION RULES:

* Do NOT repeat:

  * topics
  * resources
  * tasks

---

OUTPUT FORMAT (STRICT JSON ONLY):

{{
"duration": "<calculated duration>",

"resources": {{
"youtube_channels": [
{{
"channel_name": "...",
"coverage_level": "Basic",
"description": "...",
"link": "https://youtube.com/..."
}}
],
"practice_platforms": [
{{
"name": "...",
"purpose": "...",
"link": "https://..."
}}
]
}},

"roadmap": [
{{
"week": 1,
"days": [
{{
"day": 1,
"topic": "Introduction to Python",
"plan": "Understand what Python is, install Python, and run your first program.",
"practice_platform": "Replit",
"task": "Write a program to print your name and a message."
}}
]
}}
],

"certifications": [
{{
"name": "...",
"link": "https://..."
}}
],

"common_mistakes": [
"..."
]
}}

---

CONSTRAINTS:

* Each week: 5–7 days
* Each day:

  * exactly 1 topic
  * 1–2 resources
  * 1 platform
  * 1 task

---

SYSTEM STABILITY RULES:

* Maintain consistency for similar inputs
* Keep output concise (avoid unnecessary verbosity)

---

PRIORITY ORDER (VERY IMPORTANT):

1. Valid JSON output (highest priority)
2. Logical curriculum structure
3. Free and reliable resources
4. Non-repetition
5. Conciseness

---

STRICT OUTPUT RULES:

* Output ONLY valid JSON
* No explanation
* No markdown
* No extra text

---

QUALITY CHECK BEFORE OUTPUT:

* Is JSON valid and clean?
* Is duration realistic?
* Is curriculum logically structured?
* Are resources free and reliable?
* Is there zero repetition?
* Are mistakes useful and practical?

Return ONLY the final JSON.
"""


def extract_json(text: str) -> dict | None:
    """Try to extract JSON from text, handling common AI response noise."""
    text = text.strip()
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def call_groq(prompt: str, attempt: int = 1) -> str | None:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        logger.error("GROQ_API_KEY is not set. Please add it to your .env file.")
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 8192,
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        logger.info(f"[Attempt {attempt}] Raw AI response (first 300 chars): {raw[:300]}")
        return raw
    except requests.Timeout:
        logger.error(f"[Attempt {attempt}] Groq API timeout.")
    except requests.HTTPError as e:
        logger.error(f"[Attempt {attempt}] HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"[Attempt {attempt}] Unexpected error: {e}")

    return None


def generate_learning_plan(skill: str, level: str, daily_hours: float) -> dict:
    prompt = build_prompt(skill, level, daily_hours)

    # Attempt 1
    raw = call_groq(prompt, attempt=1)
    if raw:
        result = extract_json(raw)
        if result:
            return result

    # Attempt 2 with stricter prompt
    logger.warning("First attempt failed or returned invalid JSON. Retrying with stricter prompt.")
    strict_prompt = prompt + "\n\nCRITICAL: Your previous response was not valid JSON. Return ONLY the raw JSON object. Start your response with { and end with }. No other characters."
    raw2 = call_groq(strict_prompt, attempt=2)
    if raw2:
        result2 = extract_json(raw2)
        if result2:
            return result2

    logger.error("Both attempts failed to produce valid JSON.")
    return {"error": "Failed to generate valid plan. Please try again."}
