import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.elevenlabs_service import ElevenLabsAudioService

async def main():
    svc = ElevenLabsAudioService()
    print("ElevenLabs API Key configured:", bool(svc.api_key))
    
    sample_plan = {
        "title": "The Mindful Forest Escape",
        "tagline": "A quick 15-minute nature walk.",
        "steps": [{"description": "Step outside and take 3 deep outdoor breaths."}],
        "offline_challenge": {
            "challenge_name": "Sensory Reset",
            "description": "Listen for 3 distinct bird calls."
        }
    }
    
    res = await svc.generate_audio_briefing(sample_plan)
    print("Has Audio Base64:", res.get("has_audio"))
    print("Voice Used:", res.get("voice"))
    print("Script Preview:", res.get("script")[:80])

if __name__ == "__main__":
    asyncio.run(main())
