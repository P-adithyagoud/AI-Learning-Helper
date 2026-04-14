import os
import json
import logging
import requests
from .curated_data import find_in_curated_data, score_from_rank, get_duration_category

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Using a powerful Llama 3 model for reliable JSON output
MODEL = "llama-3.3-70b-versatile" 
TIMEOUT = 60.0

def build_prompt(skill: str, level: str, daily_hours: float, curated_resources=None) -> str:
    # If we have curated resources, we pass them to the LLM so it can build the roadmap around them.
    curated_context = ""
    if curated_resources:
        curated_context = f"\n\nCURATED RESOURCES TO USE FOR ROADMAP:\n{json.dumps(curated_resources, indent=2)}\n"

    return f"""You are a production-grade recommendation engine and learning planner.
Return EXACTLY 10 high-quality YouTube PLAYLISTS for: Skill="{skill}", Level="{level}", Daily hours={daily_hours}.

{curated_context}

---

## PRIMARY OBJECTIVE
Return a complete, structured learning system including:
1. Playlists (Resources) - EXACTLY 10 items.
2. Roadmap (Week-by-week) - Structured for execution.
3. Certifications - 4 end goal platforms.
4. Questions - 10 interview-level questions.

---

## PLAYLIST RULES (STRICT SCHEMA)
- Format: "playlists" array (EXACTLY 10 items)
- Each item MUST have these 10 fields (in this order):
  rank, channel_name, playlist_title, language, level, video_count, duration_hours, description, channel_url, playlist_url
- URLs: playlist_url MUST contain "list=" (Playlist format)
- No shorts, no channel homepages.
- Max 2 playlists per channel.
- Quality Ranking: Rank 1 is the absolute best.

---

## ROADMAP RULES
- Organize: Week -> Days.
- Max 14 days total.
- Description: Focus on what to study and practice.
- NO links in roadmap.
- If curated resources were provided above, structure the roadmap to align with those.

---

## OUTPUT FORMAT (STRICT JSON ONLY)
{{
  "skill": "{skill}",
  "level": "{level}",
  "daily_hours": {daily_hours},
  "summary": {{
    "total_playlists": 10,
    "estimated_completion_days": "X days",
    "recommended_strategy": "...",
    "learning_path_hint": "..."
  }},
  "playlists": [
    {{
      "rank": 1,
      "channel_name": "...",
      "playlist_title": "...",
      "language": "...",
      "level": "...",
      "video_count": 0,
      "duration_hours": 0,
      "description": "...",
      "channel_url": "...",
      "playlist_url": "..."
    }}
  ],
  "roadmap": [
    {{
      "week": 1,
      "days": [
        {{ "day": 1, "topic": "...", "plan": "...", "task": "..." }}
      ]
    }}
  ],
  "certifications": ["Platform 1", "Platform 2", "Platform 3", "Platform 4"],
  "questions": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"]
}}

Return ONLY valid JSON."""

def call_groq(prompt: str) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Groq API error: {e}")
    return None

def extract_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except:
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

def generate_learning_plan(skill: str, level: str, daily_hours: float) -> dict:
    curated = find_in_curated_data(skill)
    
    # Process curated items to match the new 10-column schema
    curated_formatted = None
    if curated:
        curated_formatted = []
        for i, p in enumerate(curated[:10]):
            curated_formatted.append({
                "rank": p.get("rank", i + 1),
                "channel_name": p["channel_name"],
                "playlist_title": p["playlist_title"],
                "language": p.get("language", "English"),
                "level": p.get("level", "Beginner"),
                "video_count": p.get("video_count", 0),
                "duration_hours": p.get("duration_hours", 0),
                "description": p["description"],
                "channel_url": p.get("channel_url", ""),
                "playlist_url": p["playlist_url"]
            })

    prompt = build_prompt(skill, level, daily_hours, curated_formatted)
    
    raw = call_groq(prompt)
    if not raw:
        return {"error": "Failed to connect to AI engine (Groq)."}

    result = extract_json(raw)
    if not result:
        return {
            "error": "AI engine (Groq) returned invalid format. Please try again.",
            "raw_debug": raw[:500]
        }

    # If we had curated data, we prioritize it
    if curated_formatted:
        result["playlists"] = curated_formatted
        result["source"] = "curated"
    else:
        result["source"] = "llm"

    return result
