import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
TIMEOUT = 60.0


def build_prompt(skill: str, level: str, daily_hours: float) -> str:
    return f"""You are an expert learning coach. Generate a complete, structured learning plan for the given skill.

STRICT RULES:
- Return ONLY valid JSON. No extra text, no markdown, no backticks.
- Start your response with {{ and end with }}

INPUT:
- Skill: {skill}
- Level: {level}
- Daily available time: {daily_hours} hour(s)

OUTPUT FORMAT (return exactly this structure, no deviations):
{{
  "skill": "{skill}",
  "level": "{level}",
  "duration": "X weeks",
  "resources": [
    {{
      "category": "Category name (e.g. Video Courses, Books, Practice, Official Docs)",
      "items": [
        {{
          "title": "Resource title",
          "url": "https://real-url.com",
          "description": "One line about why this resource is great",
          "type": "free" or "paid"
        }}
      ]
    }}
  ],
  "timeline": [
    {{
      "week": 1,
      "focus": "Main focus area for this week",
      "goals": ["Specific goal 1", "Specific goal 2", "Specific goal 3"],
      "daily_task": "What to do each day this week in {daily_hours} hour(s)"
    }}
  ],
  "common_mistakes": [
    {{
      "mistake": "Short name of the mistake",
      "why_it_happens": "Brief explanation of why most learners fall into this trap",
      "how_to_avoid": "Concrete action to avoid or fix this"
    }}
  ]
}}

Rules:
- resources: 3-4 categories, 2-4 items each. Use REAL URLs (YouTube, official docs, MDN, freeCodeCamp, Coursera, books, etc.)
- timeline: 3-6 weeks based on skill complexity and daily hours. Be specific.
- common_mistakes: 4-6 mistakes. These should be REAL pitfalls specific to learning {skill}, not generic advice.
- For YouTube URLs use format: https://www.youtube.com/watch?v=VIDEOID

Be highly specific to {skill} at {level} level. Do not give generic advice.
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
        logger.error(f"[Attempt {attempt}] HTTP error: {e.response.status_code} - {e.text}")
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
