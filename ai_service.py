import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"
TIMEOUT = 10.0


def build_prompt(skill: str, level: str, daily_hours: float) -> str:
    return f"""You are a structured learning plan generator. Generate a complete, actionable learning plan.

STRICT RULES:
- Return ONLY valid JSON. No extra text, no markdown, no backticks.
- Duration: 3 to 6 weeks (choose based on skill complexity and daily hours)
- Each week: 5 to 7 days
- Each day must have exactly: 1 topic, 1-2 real resources (real YouTube URLs or article URLs), 1 concise task

INPUT:
- Skill: {skill}
- Level: {level}
- Daily available time: {daily_hours} hour(s)

OUTPUT FORMAT (return exactly this structure, no deviations):
{{
  "duration": "X weeks",
  "weeks": [
    {{
      "week": 1,
      "days": [
        {{
          "day": 1,
          "topic": "Topic name",
          "resource": "https://real-resource-url.com",
          "task": "Concise actionable task description"
        }}
      ]
    }}
  ],
  "resources": [
    {{
      "title": "Descriptive resource title",
      "url": "https://real-resource-url.com",
      "type": "Video",
      "week": 1
    }}
  ],
  "failure_tips": [
    {{
      "reason": "Why most people fail at this",
      "tip": "What to do instead"
    }}
  ]
}}

Rules for resources:
- Use real, well-known sources: YouTube (youtube.com), MDN, freeCodeCamp, official docs, etc.
- For YouTube, use format: https://www.youtube.com/watch?v=VIDEOID
- Separate multiple resources with " | " inside the same resource string
- In the "resources" array, list ALL unique resources as individual items with a descriptive title (type = Video, Article, or Docs)
- In "failure_tips", provide 5-7 specific, honest reasons why most learners fail at {skill} and exactly what mistake to avoid. Be concrete, not generic.

Make tasks specific and measurable. Avoid vague instructions like "learn more about X".
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


async def call_groq(prompt: str, attempt: int = 1) -> str | None:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            logger.info(f"[Attempt {attempt}] Raw AI response (first 300 chars): {raw[:300]}")
            return raw
    except httpx.TimeoutException:
        logger.error(f"[Attempt {attempt}] Groq API timeout.")
    except httpx.HTTPStatusError as e:
        logger.error(f"[Attempt {attempt}] HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"[Attempt {attempt}] Unexpected error: {e}")

    return None


async def generate_learning_plan(skill: str, level: str, daily_hours: float) -> dict:
    prompt = build_prompt(skill, level, daily_hours)

    # Attempt 1
    raw = await call_groq(prompt, attempt=1)
    if raw:
        result = extract_json(raw)
        if result:
            return result

    # Attempt 2 with stricter prompt
    logger.warning("First attempt failed or returned invalid JSON. Retrying with stricter prompt.")
    strict_prompt = prompt + "\n\nCRITICAL: Your previous response was not valid JSON. Return ONLY the raw JSON object. Start your response with { and end with }. No other characters."
    raw2 = await call_groq(strict_prompt, attempt=2)
    if raw2:
        result2 = extract_json(raw2)
        if result2:
            return result2

    logger.error("Both attempts failed to produce valid JSON.")
    return {"error": "Failed to generate valid plan. Please try again."}
