import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
TIMEOUT = 60.0


def build_prompt(skill: str, level: str, daily_hours: float) -> str:
    return f"""You are an expert learning planner and curriculum designer.

Create a complete, structured, and realistic learning system.

---

INPUT:

* Skill: {skill}
* Level: {level}
* Daily Time: {daily_hours}
* Target Duration: dynamic based on complexity and daily hours

---

GOAL:

Generate a structured learning system divided into 4 sections:

1. Resources (what to learn from)
2. Roadmap (step-by-step execution)
3. Certifications (end goal)
4. Questions (knowledge check)

---

DURATION LOGIC:

* Calculate the TOTAL NUMBER OF DAYS based purely on skill complexity, level, and daily hours ({daily_hours} hours/day).
* A simple topic with high daily hours might require 3-7 days.
* A complex topic might require up to 14 days (maximum 2 weeks).
* IMPORTANT: DO NOT exceed 14 days (2 weeks) under any circumstances to prevent API limits from being reached.

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

* Provide TOP 5 high-quality YouTube channels for the given skill.
* CURATED MAPPING: If the requested skill falls into one of these categories, you MUST prioritize and use these exact channels. Include the specific "Tip" or "Combo" in their descriptions:
  1. Data Structures & Algorithms (DSA): take U forward, Apna College, CodeHelp, Abdul Bari, NeetCode. (Tip: Best combo: Striver + NeetCode)
  2. Programming (Java/C++/Python): Bro Code, Telusko, freeCodeCamp.org, Programming with Mosh, CodeWithHarry. (Tip: Telusko + Bro Code)
  3. Web Development: Traversy Media, The Net Ninja, CodeWithHarry, freeCodeCamp.org, Kevin Powell. (Tip: Build projects while learning - portfolio website minimum)
  4. AI / Machine Learning: Krish Naik, codebasics, Sentdex, freeCodeCamp.org, 3Blue1Brown. (Tip: Don’t skip math basics - huge mistake students make)
  5. Database (DBMS + SQL): CodeHelp, freeCodeCamp.org, Kudvenkat, ProgrammingKnowledge, Simplilearn. (Tip: Practice SQL daily - not just theory)
  6. Git & GitHub: freeCodeCamp.org, Traversy Media, Programming with Mosh, The Net Ninja, CodeWithHarry. (Tip: Learn in 2–3 days, then USE daily)
  7. Problem Solving / Logic: Numberphile, MindYourDecisions, 3Blue1Brown, TED, CrashCourse. (Tip: Still, coding problems > watching videos)
  8. System Design (Beginner): Gaurav Sen, CodeKarle, Tech Dummies, freeCodeCamp.org, Hussein Nasser. (Tip: Start after DSA basics - don’t rush)
  9. Debugging & Testing: Tech With Tim, freeCodeCamp.org, Academind, Programming with Mosh, Google for Developers. (Tip: Best learning = fixing your own bugs)
  10. Communication Skills: TED, Charisma on Command, Improvement Pill, BeerBiceps, Jordan Peterson.

* CRITICAL: Ensure the link is 100% accurate and working. Do not hallucinate links. If unsure of the exact channel URL, provide a YouTube search query URL (e.g., https://www.youtube.com/results?search_query=ChannelName) or direct user to search for the channel name instead of a fake link to avoid 404 errors.

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

ROADMAP RULES (UPDATED — VERY IMPORTANT):

The roadmap is for EXECUTION ONLY, not for learning resources.

---

STRUCTURE:

* Organize as: Week -> Days
* A week can have up to 7 days.
* The total number of days across all weeks must align with your calculated duration.

---

EACH DAY MUST INCLUDE:

* day (number)
* topic (clear and specific)
* plan (what exactly to do that day in simple steps)
* task (clear action task)

---

STRICT RULES:

* DO NOT include any links in the roadmap
* DO NOT include YouTube or article references
* DO NOT repeat resources from the resources section
* DO NOT include questions in the roadmap days (they will be provided at the end)
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

* Provide 4 certification platforms: Coursera, Udemy, and 2 other FREE certification platforms.
* CRITICAL: Ensure links are 100% accurate and working. Most generated links are 404s. Do not hallucinate exact course links if unsure; instead, provide a search link (e.g., https://www.coursera.org/search?query=SkillName or https://www.udemy.com/courses/search/?q=SkillName) to guarantee it works.
* Must be relevant to the skill and highly useful for learners.

---

QUESTIONS RULES:

* Provide exactly 30 interview-level questions.
* These questions must deeply test core concepts, edge cases, and practical implementation scenarios across the learned skill.
* Keep each question strictly to 1 sentence
* DO NOT provide answers
* Provide as a plain JSON string array

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
"questions": [
  "What is Python and why is it popular?",
  "Explain how Python determines the type of a variable at runtime.",
  "Write a program that takes two numbers as input and prints their sum, difference, product, and quotient."
],
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

"questions": [
"..."
]
}}

---

CONSTRAINTS:

* Total Duration: calculate realistically based on skill complexity and {daily_hours} hours/day
* Each day:

  * exactly 1 topic
  * purely 1 straightforward plan
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
* Are the questions useful for checking knowledge?

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
        "max_tokens": 3500,
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        logger.info(f"[Attempt {attempt}] Raw response length: {len(raw)} chars")
        logger.info(f"[Attempt {attempt}] First 400 chars: {raw[:400]}")
        return raw
    except requests.Timeout:
        logger.error(f"[Attempt {attempt}] Groq API timeout after {TIMEOUT}s")
    except requests.HTTPError as e:
        status = e.response.status_code
        logger.error(f"[Attempt {attempt}] HTTP {status}: {e.response.text[:300]}")
        if status == 429:
            return '{"error": "API Rate Limit reached (Free Tier). Please wait 30 seconds and try again."}'
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
