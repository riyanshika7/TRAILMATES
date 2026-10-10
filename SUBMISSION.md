---
title: TrailMates AI — Touch Grass Outdoor Adventure Companion (Best Use of Render)
published: true
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

---

## 1. What I Built & The Problem It Solves

Modern life keeps us glued to screens, notifications, and infinite feeds. While productivity and social apps constantly demand our attention, getting outside for even 15 or 30 minutes can drastically improve mental clarity, energy, and well-being.

**TrailMates** is an open-source, pocket-sized outdoor adventure companion designed to get people off their screens and into nature.

Instead of another addictive app, TrailMates acts as a friendly nature journal. Users select their activity (e.g. Walking, Nature Photography, Birdwatching, Mindful Outdoor Break), available time (15–60 mins), energy level, outdoor setting, and interests. TrailMates then generates a personalized, screen-free outdoor itinerary complete with:

* ⏱️ **Timeline Steps with Durations**: Custom-fitted to the user's available time.
* 📊 **Activity Suitability Score**: Rates activity intensity against user inputs using a rule-based heuristic scorer (TabPFN package installed on Render).
* 🎧 **Audio Trail Guide (Play & Stop Controls)**: Generates a 60-second audio briefing so users can hit play, put their phone in Do Not Disturb mode, and head outside.
* 📱🔒 **Screen-Free Offline Challenge**: A sensory reset task (e.g. identify 5 natural textures, 4 ambient sounds).
* ❓ **Post-Walk Reflection Question**: Encourages mindful observation during the walk.

---

## 2. Live Demo & Render Deployment

* **Live Demo Site on Render**: https://trailmates-89sz.onrender.com
* **GitHub Repository**: https://github.com/riyanshika7/TRAILMATES
* **Render Health Endpoint**: https://trailmates-89sz.onrender.com/health
* **Render AI Status Endpoint**: https://trailmates-89sz.onrender.com/api/status

---

## 3. How Render Powers TrailMates (Best Use of Render)

Render serves as the primary **AI Application Runtime & Host** for TrailMates:

1. **FastAPI Web Service Hosting**: Render builds and runs the Python FastAPI server, serving static frontend assets (`index.html`, `styles.css`, `app.js`) and REST API endpoints.
2. **AI Model Pipeline Orchestration**: On Render, the FastAPI backend securely executes the multi-service pipeline:
   * Scores activity suitability via the TabPFN heuristic/model scorer.
   * Dispatches requests to **Hugging Face Inference Providers** using open-weight models (`Qwen/Qwen2.5-7B-Instruct`).
   * Synthesises **ElevenLabs** voice narration audio (falls back to browser Web Speech API).
   * Records execution spans in-memory (forwarded to Sentry when `SENTRY_DSN` is set).
3. **Automated Health Monitoring**: Render monitors the application via the `/health` endpoint (`healthCheckPath: /health`), automatically restarting containers if an anomaly occurs.
4. **Environment Credential Security**: Render securely manages `HF_TOKEN` and `HF_MODEL` as server-side environment variables, ensuring API secrets never reach the client browser.

---

## 4. How Open Innovation & Open-Weight Models Were Used

### Why Open-Weight Models Matter:
1. **Privacy**: Open-weight models can run on local hardware — user outdoor preferences don't have to leave their device.
2. **Cost Efficiency & Model Control**: Serving open-weight models eliminates per-token API costs and avoids vendor lock-in.

### AI Model Integration & Resilient Architecture:
* **Hugging Face Inference Providers**: TrailMates communicates with `Qwen/Qwen2.5-7B-Instruct` via the official OpenAI-compatible router (`https://router.huggingface.co/v1/chat/completions`) in `app/services/hf_service.py`.
* **Truthful Fallback Engine**: If `HF_TOKEN` is not configured or inference fails, TrailMates serves a rule-based plan clearly labelled with:
  > 💡 *"Demo plan — AI inference is not configured or currently unavailable"*

TrailMates **never** labels a rule-based plan as AI-generated. The `is_ai_generated` field in the API response is set only after a valid model response is received and its JSON structure is verified.

---

## 5. Technology Stack & Code Highlights

```
hacktoberfest/
├── app/
│   ├── main.py                  # FastAPI Backend (/health, /api/status, /api/plan)
│   └── services/
│       ├── hf_service.py        # Hugging Face Open-Weight Model Integration
│       ├── tabpfn_service.py    # Activity Suitability Scorer (TabPFN / heuristic)
│       ├── elevenlabs_service.py# ElevenLabs Audio Briefing Engine
│       └── sentry_service.py    # In-memory span recorder (Sentry when DSN set)
├── static/
│   ├── index.html               # Doodle-Inspired Nature Journal UI
│   ├── app.js                   # Client interactivity & Play/Stop Audio Controls
│   └── styles.css               # Warm Cream Paper Palette & Animations
├── tests/
│   └── test_api.py              # Automated Pytest Suite
├── render.yaml                  # Render Blueprint Manifest
└── Dockerfile                   # Container Build File
```

---

## 6. What I Learned & Trade-Offs

1. **Designing for Phone Disengagement**: The biggest design challenge was making a digital app whose primary goal is to close itself. Adding an **Audio Trail Guide** with Play & Stop buttons solved this — users listen to their 60-second briefing and lock their screen.
2. **Resilience & Honest AI Attribution**: Relying on external inference APIs requires strict timeouts and fallback handling. Clearly distinguishing between real model output and rule-based demo output builds user trust.
3. **Deploying on Render**: Using `render.yaml` with explicit health check paths made setup repeatable with a single blueprint deploy.

---

## 7. Submission Checklist

- [x] Live URL hosted on Render: https://trailmates-89sz.onrender.com
- [x] Health check endpoint `/health` returning HTTP 200 `{"status": "healthy"}`
- [x] Open-weight AI model configured (`Qwen/Qwen2.5-7B-Instruct` via Hugging Face — requires valid `HF_TOKEN` in Render env vars)
- [x] Honest AI vs. Demo plan attribution — `is_ai_generated` only set `true` after verified model response
- [x] Play & Stop audio controls for hands-free outdoor listening
- [x] Automated test suite — run `py -m pytest tests/test_api.py -v` to verify
