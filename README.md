# AI Learning Planner

A full-stack web app that generates structured, week-by-week learning plans using Groq AI.

## Project Structure

```
project/
├── backend/
│   ├── main.py                  # FastAPI app + routes
│   ├── services/
│   │   └── ai_service.py        # Groq API logic
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── index.html               # HTML + Tailwind UI
```

---

## Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)

---

## Setup & Run

### 1. Backend

```bash
# Navigate to backend
cd project/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_actual_key

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be live at: `http://localhost:8000`

### 2. Frontend

Open `frontend/index.html` directly in your browser — no build step needed.

```bash
# Option A: Double-click index.html in your file explorer

# Option B: Serve via Python (avoids any CORS quirks)
cd project/frontend
python -m http.server 3000
# Then open http://localhost:3000
```

---

## API Reference

### `POST /generate-plan`

**Request body:**
```json
{
  "skill": "Python",
  "level": "Beginner",
  "daily_hours": 2
}
```

**Success response:**
```json
{
  "duration": "4 weeks",
  "weeks": [
    {
      "week": 1,
      "days": [
        {
          "day": 1,
          "topic": "Python Basics & Setup",
          "resource": "https://www.youtube.com/watch?v=rfscVS0vtbw",
          "task": "Install Python, run first script, print Hello World"
        }
      ]
    }
  ]
}
```

**Validation errors** return HTTP 422 with detail messages.  
**AI failures** return HTTP 502 with an error message.

---

## Notes

- The backend retries once if the AI returns invalid JSON
- All AI errors are caught and return clean messages to the frontend
- No database or authentication required
