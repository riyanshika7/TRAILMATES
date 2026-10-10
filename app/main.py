import os
import logging
import re
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

from app.services.sentry_service import init_sentry, IN_MEMORY_TRACES, AgentSpan
from app.services.tabpfn_service import TabPFNAdventureEngine
from app.services.hf_service import HuggingFaceInferenceService
from app.services.elevenlabs_service import ElevenLabsAudioService
from app.services.serpapi_service import SerpApiLocalOutdoorsService

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("trailmates")

# Initialize Sentry
init_sentry()

app = FastAPI(
    title="TrailMates AI — Touch Grass Outdoor Companion",
    description="Open-Source AI Outdoor Adventure Companion built with Gemma 2 / Llama 3, TabPFN, ElevenLabs, and Sentry Agent Tracing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate core services
tabpfn_engine = TabPFNAdventureEngine()
hf_service = HuggingFaceInferenceService()
elevenlabs_service = ElevenLabsAudioService()
serpapi_service = SerpApiLocalOutdoorsService()

# Input Validation Models (Pydantic v2)
class PlanRequest(BaseModel):
    activity: str = Field(default="Walking", description="Selected outdoor activity")
    available_time_min: int = Field(default=30, ge=15, le=120, description="Available time in minutes")
    energy_level: str = Field(default="Medium", description="Energy level (Low, Medium, High)")
    setting: str = Field(default="Park", description="Outdoor setting")
    interests: List[str] = Field(default_factory=lambda: ["Nature"], description="Selected interests")
    optional_note: Optional[str] = Field(default=None, max_length=200, description="Optional user note")

    @field_validator("optional_note", mode="before")
    def sanitize_note(cls, v):
        if v:
            v = re.sub(r'<[^>]*>', '', str(v)).strip()
            return v[:200]
        return v

    @field_validator("energy_level", mode="before")
    def validate_energy(cls, v):
        if v not in ["Low", "Medium", "High"]:
            return "Medium"
        return v

    @field_validator("available_time_min", mode="before")
    def validate_time(cls, v):
        try:
            val = int(v)
            allowed = [15, 30, 45, 60, 90, 120]
            if val not in allowed:
                return min(allowed, key=lambda x: abs(x - val))
            return val
        except Exception:
            return 30

@app.get("/health")
async def health_check():
    """Health check endpoint for Render deployment."""
    return {"status": "healthy", "service": "trailmates", "version": "1.0.0"}

@app.get("/api/status")
async def api_status():
    """Reports system status & AI configuration without exposing secrets."""
    return {
        "ai_configured": hf_service.is_configured(),
        "model_name": hf_service.model_name,
        "provider": "Hugging Face Inference Providers",
        "tabpfn_available": True,
        "audio_available": True,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/api/plan")
async def create_plan(req: PlanRequest):
    logger.info(f"Plan request: activity={req.activity}, time={req.available_time_min}m, energy={req.energy_level}, setting={req.setting}")

    with AgentSpan(
        name="TrailMates AI Plan Generator Workflow",
        op="agent.workflow.plan",
        description="Coordinates TabPFN -> HF Open-Weight -> ElevenLabs -> SerpApi pipeline"
    ) as main_span:
        try:
            # 1. Map energy string to 1-3 numeric code for TabPFN
            energy_num = 1 if req.energy_level == "Low" else (2 if req.energy_level == "Medium" else 3)

            # 2. Run TabPFN Feasibility Prediction
            tabpfn_res = tabpfn_engine.predict_suitability(
                time_available=req.available_time_min,
                energy_level=energy_num,
                setting_str=req.setting,
                temp_c=20
            )

            # 3. Search SerpApi local outdoors / green spaces
            local_info = await serpapi_service.get_local_outdoors_info(
                location="Nearby Outdoors",
                setting=req.setting
            )

            # 4. Generate plan via Hugging Face Open-Weight model (or honest fallback)
            plan = await hf_service.generate_plan(
                activity=req.activity,
                time_min=req.available_time_min,
                energy_level=req.energy_level,
                setting=req.setting,
                interests=req.interests,
                optional_note=req.optional_note,
                tabpfn_metrics=tabpfn_res
            )

            # 5. Generate ElevenLabs Audio Briefing
            audio_briefing = await elevenlabs_service.generate_audio_briefing(plan)

            # Construct unified response payload
            response_payload = {
                "success": True,
                "plan": plan,
                "tabpfn_analytics": tabpfn_res,
                "local_info": local_info,
                "audio_briefing": audio_briefing,
                "is_ai_generated": plan.get("is_ai_generated", False),
                "attribution": plan.get("attribution", ""),
                "sentry_trace_summary": {
                    "spans_recorded": len(IN_MEMORY_TRACES),
                    "total_duration_ms": main_span.duration_ms
                }
            }

            main_span.set_data("plan_title", plan.get("title", ""))
            main_span.set_data("is_ai_generated", plan.get("is_ai_generated", False))

            return response_payload

        except Exception as e:
            logger.error(f"Error in plan generation: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

# Backward compatibility alias route
@app.post("/api/adventure")
async def generate_adventure_alias(req: PlanRequest):
    return await create_plan(req)

@app.get("/api/traces")
async def get_traces():
    return {"count": len(IN_MEMORY_TRACES), "traces": IN_MEMORY_TRACES}

# Static Files & Homepage
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if os.path.exists("static/index.html"):
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>TrailMates AI Backend Running</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
