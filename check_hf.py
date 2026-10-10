import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.hf_service import HuggingFaceInferenceService

async def test_hf():
    svc = HuggingFaceInferenceService()
    print("HF Service configured:", svc.is_configured())
    print("HF Model Name:", svc.model_name)
    
    plan = await svc.generate_plan(
        activity="Walking",
        time_min=30,
        energy_level="Medium",
        setting="Park",
        interests=["Nature"],
        optional_note="Quiet walk"
    )
    print("Generated Plan Title:", plan.get("title"))
    print("Is AI Generated:", plan.get("is_ai_generated"))
    print("Attribution:", plan.get("attribution"))

if __name__ == "__main__":
    asyncio.run(test_hf())
