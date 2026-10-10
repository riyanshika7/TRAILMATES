---
title: TrailMates AI — Touch Grass Outdoor Adventure Companion
published: true
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

---

## What I Built

**TrailMates** is an open-source outdoor adventure companion that generates personalised, screen-free outdoor plans from your preferences — your available time, energy level, setting (park, trail, garden), and mood.

You tell it you have 30 minutes and low energy near a local park. It produces a step-by-step itinerary: when to arrive, what to notice, a packing list, safety reminders, a sensory offline challenge ("find 5 textures without touching your phone"), and a reflection question for after. A Play/Stop audio briefing lets you lock your screen and walk out the door.

**Who is it for?** Anyone who keeps meaning to go outside but needs a tiny nudge with a concrete plan. The whole point is to make the app feel done the moment you press Play — so you can put it in your pocket.

The backend is a Python FastAPI service deployed on Render. The open-weight language model (`Qwen/Qwen2.5-7B-Instruct` via Hugging Face Inference Providers) generates the actual adventure text. If inference fails or the token is missing, the app falls back to a clearly-labelled rule-based plan — it never pretends the AI worked when it didn't.

---

## Demo

🌿 **Live app**: https://trailmates-89sz.onrender.com
🔍 **Health check**: https://trailmates-89sz.onrender.com/health
📊 **AI status**: https://trailmates-89sz.onrender.com/api/status

> **Note on the demo**: The Render free tier spins down after inactivity — first load may take ~30 seconds. Once warm, plan generation is live. The `"AI Generated"` badge only appears when the model actually responded with valid JSON; otherwise the app shows `"Demo plan — rule-based fallback"`.

---

## Code

{% github riyanshika7/TRAILMATES %}

Key files:
- [`app/services/hf_service.py`](https://github.com/riyanshika7/TRAILMATES/blob/main/app/services/hf_service.py) — HF Inference Providers integration with strict AI attribution (only badges a plan as AI-generated after validating the response structure)
- [`app/services/tabpfn_service.py`](https://github.com/riyanshika7/TRAILMATES/blob/main/app/services/tabpfn_service.py) — Activity suitability scorer (heuristic when TabPFN package unavailable, clearly labelled either way)
- [`app/services/serpapi_service.py`](https://github.com/riyanshika7/TRAILMATES/blob/main/app/services/serpapi_service.py) — Live local park search via SerpApi (static defaults labelled when key absent)
- [`static/index.html`](https://github.com/riyanshika7/TRAILMATES/blob/main/static/index.html) + [`static/app.js`](https://github.com/riyanshika7/TRAILMATES/blob/main/static/app.js) — Doodle journal UI with mood cards, Play/Stop audio controls
- [`render.yaml`](https://github.com/riyanshika7/TRAILMATES/blob/main/render.yaml) — Render blueprint with `/health` health check
- [`tests/test_api.py`](https://github.com/riyanshika7/TRAILMATES/blob/main/tests/test_api.py) — 6 automated tests (all passing locally)

---

## How I Built It

**Open-weight model — Hugging Face Inference Providers**

The core AI is `Qwen/Qwen2.5-7B-Instruct`, one of the models recommended on the HF Inference Providers documentation. It is called via the official OpenAI-compatible router endpoint:

```
POST https://router.huggingface.co/v1/chat/completions
Authorization: Bearer $HF_TOKEN
```

The system prompt instructs the model to return a strict JSON schema (title, steps, items\_to\_bring, safety\_tips, phone\_free\_challenge, reflection\_question). The `_extract_ai_result()` method in `hf_service.py` validates the response — checking that `choices[0].message.content` is non-empty, ≥80 chars, parses as JSON, and contains `title` and `steps` — before setting `is_ai_generated: true`. A rule-based fallback runs if any of those checks fail and is always clearly labelled.

**TabPFN (Prior Labs)**

The `tabpfn` package is in `requirements.txt`. When it loads on Render, the suitability scorer is labelled `"TabPFN (Prior Labs tabular model)"`. When it does not load (e.g. local CPU-only environment), it falls back to a heuristic scorer labelled `"Heuristic rule-based scorer"` — the label is set from `self.has_official_tabpfn`.

**ElevenLabs**

`elevenlabs` SDK is wired up in `elevenlabs_service.py`. When the API key is valid, it returns an audio URL for the plan briefing. When it returns 401 (expired key) or is unconfigured, the frontend falls back to `window.speechSynthesis` (browser Web Speech API) — users still get audio, just synthesised client-side.

**SerpApi**

`serpapi_service.py` calls the Google Maps engine for local park results when a key and location are provided. Results include a `"source": "serpapi-live"` tag. Static defaults include `"source": "static-default"` so the frontend can (and does) show which data is real.

**Sentry**

`sentry_service.py` wraps every service call in an `AgentSpan` context manager that records timing, inputs, and outputs in an in-memory list. When `SENTRY_DSN` is set in environment variables, the same spans are forwarded to Sentry's trace dashboard. The startup log is honest about which mode is active.

**Render**

The app is deployed as a Python web service on Render using `render.yaml`:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health` returning `{"status": "healthy"}`
- All API keys stored as Render environment variables — never sent to the client browser

---

## Why Does Open Innovation Matter?

**Model swappability — no rewrite required.**
`HF_MODEL` is an environment variable. Switching from `Qwen/Qwen2.5-7B-Instruct` to `google/gemma-2-2b-it` or any other Hugging Face chat-completion model requires changing one variable and redeploying. No SDK migration, no new API account, no contract negotiation. A closed API would lock the adventure-generation format to one vendor's output style and deprecation schedule.

**Token stays server-side — user preferences stay private.**
Because the model runs on Hugging Face's inference servers (called from Render's backend), the user's location, energy level, and activity preferences are only sent to one server — yours. With a closed, browser-callable API (e.g. a client-side OpenAI call), that preference data travels through a third-party service on every request. Moving to a locally-hosted open-weight model (Ollama, llama.cpp) would eliminate even the Hugging Face hop — the JSON schema the app uses would work identically.

**Honest fallback without vendor gates.**
The rule-based fallback that runs when inference fails produces a real, usable plan — not an error screen. This is only practical because we control the full output format. A closed API that changes its response schema or rate-limits aggressively would break the fallback path silently. Here, the fallback is pure Python with no external dependencies.

**Zero inference cost at scale.**
`Qwen/Qwen2.5-7B-Instruct` on Hugging Face's free serverless tier costs $0 for typical usage. A GPT-4o equivalent would cost ~$0.01–0.03 per plan. For a project designed to encourage people to walk to a park — where the average user generates one plan per session — the economics of open models make this sustainable as a free public tool.

**Fine-tuning is possible.**
The `data/trail_historical_dataset.csv` in the repo exists because the TabPFN scorer is designed to be replaceable with a proper trained model on that data. Open weights mean a contributor could fine-tune the language model on outdoor activity descriptions, or train a real TabPFN classifier on the suitability dataset, and drop it in without touching any of the API contract.

---

## My Agent Session

Built with [Antigravity (AGY)](https://antigravity.dev) — the full multi-session conversation is what produced the code in this repository, including the endpoint correction, honest attribution logic, and this submission.

---

## Prize Categories

- **Best Use of Render** — TrailMates is deployed as a Render Web Service using a `render.yaml` blueprint. The `/health` endpoint serves Render's health check. All secrets are managed via Render environment variables. The AI pipeline runs entirely server-side on Render.
- **Best Use of a Hugging Face Open-Weight Model** — `Qwen/Qwen2.5-7B-Instruct` via `https://router.huggingface.co/v1/chat/completions`. Attribution is only shown after response validation.
- **Best Use of TabPFN** — Prior Labs `tabpfn` package installed; suitability scorer clearly reports `"TabPFN (Prior Labs tabular model)"` vs `"Heuristic rule-based scorer"` depending on what loaded.
- **Best Use of ElevenLabs** — ElevenLabs SDK integrated for audio trail briefing with graceful browser Web Speech API fallback.
- **Best Use of Sentry** — `AgentSpan` context manager records timing and metadata for every service call; forwarded to Sentry when DSN is configured.
- **Best Use of SerpApi** — Google Maps engine search for real local parks and green spaces when `SERPAPI_API_KEY` and location are present; results tagged `"source": "serpapi-live"`.
