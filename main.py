import logging
from dotenv import load_dotenv
load_dotenv()  # Must be before any os.getenv() calls

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from services.ai_service import generate_learning_plan
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Learning Planner", version="1.0.0")

# Allow all origins so the browser can call the API from any context
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}


class PlanRequest(BaseModel):
    skill: str
    level: str
    daily_hours: float

    @field_validator("skill")
    @classmethod
    def skill_must_be_valid(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Skill must be at least 3 characters long.")
        return v

    @field_validator("level")
    @classmethod
    def level_must_be_valid(cls, v):
        if v not in VALID_LEVELS:
            raise ValueError(f"Level must be one of: {', '.join(VALID_LEVELS)}")
        return v

    @field_validator("daily_hours")
    @classmethod
    def hours_must_be_valid(cls, v):
        if not (1 <= v <= 10):
            raise ValueError("Daily hours must be between 1 and 10.")
        return v


@app.get("/health")
def health_check():
    api_key = os.getenv("GROQ_API_KEY", "")
    key_set = bool(api_key) and api_key != "your_groq_api_key_here"
    return {"status": "ok", "groq_api_key_configured": key_set}


@app.post("/generate-plan")
async def generate_plan(request: PlanRequest):
    logger.info(f"Plan request: skill={request.skill}, level={request.level}, hours={request.daily_hours}")
    result = await generate_learning_plan(request.skill, request.level, request.daily_hours)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


# Serve the frontend — index.html at root "/"
@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))
