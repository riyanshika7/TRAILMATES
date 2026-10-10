# 🌱 TrailMates — Less Scrolling. More Exploring.

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026-brightgreen.svg)](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)
[![Gemma 2 Open Weight](https://img.shields.io/badge/Model-Gemma--2--Open--Weight-blue.svg)](https://ai.google.dev/gemma)
[![Hugging Face Providers](https://img.shields.io/badge/Provider-Hugging--Face--Inference-yellow.svg)](https://huggingface.co/)
[![TabPFN Prior Labs](https://img.shields.io/badge/Tabular--AI-TabPFN-orange.svg)](https://docs.priorlabs.ai/)
[![Render Deployable](https://img.shields.io/badge/Deploy-Render-purple.svg)](https://render.com)

**TrailMates** is an open-source outdoor adventure companion designed to help people trade screen time for outdoor time. Built for the **Hacktoberfest 2026 Open-Source AI Challenge (Week 1: Touch Grass)**.

---

## 📖 Overview & Motivation

Digital screens and infinite feeds draw people away from real-world nature. TrailMates encourages users to spend less time scrolling and more time outdoors.

Users select their activity, available time (15–60 mins), energy level, outdoor setting, and interests. TrailMates uses **Hugging Face Open-Weight Models** (such as `google/gemma-2-9b-it` or `meta-llama/Llama-3.2-3B-Instruct`) alongside **Prior Labs TabPFN** to generate a practical, screen-free outdoor adventure complete with timeline steps, packing list, safety tips, an offline sensory challenge, and a post-walk reflection question.

---

## ✨ Features

- 🌿 **Open-Weight AI Integration**: Powered by open-weight models via Hugging Face Inference Providers.
- 📊 **TabPFN Feasibility Prediction**: Tabular foundation model predicts activity suitability and weather friction.
- 🎧 **Audio Trail Guide (Play & Stop Controls)**: Listen to a 60-second audio briefing before locking your phone, with dedicated **Play** and **Stop** controls.
- 💡 **Truthful AI Attribution**: Clearly distinguishes between AI-generated plans and rule-based demo plans when AI inference is unconfigured or unavailable.
- 🔒 **Screen-Free Offline Challenge**: Encourages putting phones in Do-Not-Disturb mode during the activity.
- 🖨️ **Printable Reference Card**: High-contrast, print-optimized design for phone-free outdoor use.

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: HTML5, Tailwind CSS, Lucide Icons, Vanilla JavaScript.
- **Backend Framework**: Python FastAPI (`app/main.py`).
- **AI Model Integration**: Hugging Face Inference Providers (`app/services/hf_service.py`).
- **Tabular Intelligence**: Prior Labs TabPFN (`app/services/tabpfn_service.py`).
- **Voice Synthesis**: ElevenLabs & Neural Browser Web Speech API (`app/services/elevenlabs_service.py`).
- **Agent Tracing**: Sentry Agent Tracing SDK (`app/services/sentry_service.py`).
- **Deployment**: Render Web Service via `render.yaml` blueprint & Docker container.

---

## 🔑 Environment Variables Configuration

Copy `.env.example` to `.env` for local development:

```env
# Hugging Face Settings
HF_TOKEN=your_huggingface_token_here
HF_MODEL=google/gemma-2-9b-it

# Partner APIs (Optional)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
SERPAPI_API_KEY=your_serpapi_key_here
SENTRY_DSN=your_sentry_dsn_here

ENVIRONMENT=development
PORT=8000
```

> ⚠️ **Security Note**: Never commit `.env` or any real API token to Git. `.env` is listed in `.gitignore`.

---

## 💻 Local Setup Instructions

### Windows (PowerShell):
```powershell
# 1. Clone repository
git clone https://github.com/your-username/trailmates.git
cd trailmates

# 2. Create and activate virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
py -m pip install -r requirements.txt

# 4. Launch development server
py -m uvicorn app.main:app --reload --port 8000
```

### macOS / Linux:
```bash
# 1. Clone repository
git clone https://github.com/your-username/trailmates.git
cd trailmates

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch development server
python3 -m uvicorn app.main:app --reload --port 8000
```

Open your browser at **`http://localhost:8000`**.

---

## 🚀 Render Deployment Guide (Step-by-Step)

TrailMates is configured for 1-click deployment on [Render](https://render.com).

1. Push your repository to GitHub.
2. Log into the **Render Dashboard** and click **New +** -> **Blueprint**.
3. Connect your GitHub repository containing `render.yaml`.
4. Render will automatically detect `render.yaml` and configure:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
5. Under **Environment Variables** in the Render Dashboard, set:
   - `HF_TOKEN`: Your Hugging Face user access token (from [hf.co/settings/tokens](https://huggingface.co/settings/tokens)).
   - `HF_MODEL`: `google/gemma-2-9b-it` (or `meta-llama/Llama-3.2-3B-Instruct`).
6. Click **Deploy**. Render will build and launch your application.

> 💡 *Note on Demo Mode*: If no `HF_TOKEN` is added, TrailMates boots seamlessly in **Demo Mode**, serving rule-based outdoor plans clearly marked with *"Demo plan — AI inference is not configured"*.

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive TrailMates homepage. |
| `GET` | `/health` | Returns HTTP 200 `{"status": "healthy"}` for Render health checks. |
| `GET` | `/api/status` | Reports whether AI inference is configured without exposing tokens. |
| `POST` | `/api/plan` | Accepts activity preferences and returns a structured adventure plan. |
| `GET` | `/api/traces` | Returns recorded Sentry Agent Tracing execution spans. |

---

## 🧪 Automated Testing

Run the test suite using `pytest`:

```bash
py -m pytest tests/test_api.py -v
```

Tests verify homepage loading, health check HTTP 200, status reporting, input sanitization, plan generation, and honest fallback handling.

---

## 🛡️ Safety & Responsible Design

- TrailMates promotes low-risk, accessible outdoor activities (local parks, walking trails, neighborhoods).
- Reminds users to stay aware of traffic, weather, daylight, and hydration.
- Explicitly states that generated plans are general suggestions and does not claim to verify live environmental hazards.
- Does not collect or track user precise locations or home addresses.
