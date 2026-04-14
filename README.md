# ✨ AI Learning Planner (Monolith v2.0)

A premium, AI-powered YouTube playlist curator and learning assistant. Built with a unified **Flask** backend and a high-fidelity **"Nebula"** Vanilla CSS/JS dashboard.

![Nebula Dashboard Example](https://img.shields.io/badge/UI-Nebula--Design-blueviolet?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-Flask_%7C_Vanilla_JS_%7C_Groq_AI-blue?style=for-the-badge)

---

## 🌌 Key Features

- **Monolithic Architecture**: Zero build steps. High-performance Flask server serving a self-contained, high-fidelity dashboard.
- **Nebula Design System**: Glassmorphism, artisanal gradients, and smooth animations built entirely with native web technologies.
- **AI Recommendation Engine**: Orchestrated by Groq (LLM) to generate custom learning paths based on skill level and schedule.
- **Standardized 10-Column Metadata**: Every playlist includes precise data for:
  - `rank`, `channel_name`, `playlist_title`, `language`, `level`, `video_count`, `duration_hours`, `description`, `channel_url`, `playlist_url`.

---

## 📁 Project Structure

```text
Ai-learning-Assistent/
├── main.py              # Unified Flask Controlle (API + Rendering)
├── services/
│   ├── ai_service.py    # AI logic & Curation orchestration
│   └── curated_data.py  # High-fidelity dataset & schema definitions
├── templates/
│   └── index.html       # The "Nebula" Dashboard (Vanilla JS/CSS)
├── static/              # Assets and global styles
├── requirements.txt     # Python dependencies
└── .env                 # API Credentials (ignored by git)
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- [Groq API Key](https://console.groq.com)

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/P-adithyagoud/AI-Learning-Helper.git
cd AI-Learning-Helper

# Install dependencies
pip install -r requirements.txt

# Configure Environment
echo "GROQ_API_KEY=your_key_here" > .env
```

### 3. Launch
```powershell
# Windows
.\run_local.ps1
```
The dashboard will be available at: **http://localhost:8000**

---

## 🛡️ Metadata Schema
Our platform enforces a strict JSON schema for all playlist recommendations to ensure UI consistency:

| Field | Description |
| :--- | :--- |
| `rank` | Quality score ranking (1-10) |
| `playlist_title` | Name of the YouTube playlist |
| `channel_name` | Name of the creator channel |
| `video_count` | Number of lessons in the playlist |
| `duration_hours` | Estimated total runtime |
| `language` | Instruction language (e.g. English, Hindi) |
| `level` | Difficulty (Beginner/Intermediate/Advanced) |

---

## ✨ Developed with Antigravity
This project was built and optimized using **Antigravity**, a powerful agentic AI coding assistant from Google Deepmind.
