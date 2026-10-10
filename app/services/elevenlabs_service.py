import os
import logging
import httpx
import base64
from typing import Dict, Any, Optional
from app.services.sentry_service import AgentSpan

logger = logging.getLogger("trailmates.elevenlabs")

class ElevenLabsAudioService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        # Default warm natural voice (e.g., '21m00Tcm4TlvDq8ikWAM' - Rachel or 'EXAVITQu4vr4xnSDxMaL' - Sarah)
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    async def generate_audio_briefing(self, adventure_plan: Dict[str, Any]) -> Dict[str, Any]:
        with AgentSpan(
            name="ElevenLabs Audio Trail Guide",
            op="ai.model.elevenlabs",
            description="Synthesizes inspiring audio briefing MP3 using ElevenLabs voice AI"
        ) as span:
            title = adventure_plan.get("title", "Your Outdoor Adventure")
            tagline = adventure_plan.get("tagline", "Enjoy your time outside.")
            steps = adventure_plan.get("steps", [])
            challenge = adventure_plan.get("offline_challenge", {})

            # Construct script to read aloud
            script = f"Welcome to {title}. {tagline}. "
            if steps:
                script += f"First, {steps[0].get('description', '')}. "
            if challenge:
                script += f"Your offline challenge today: {challenge.get('challenge_name', '')}. {challenge.get('description', '')}. "
            script += "Now, put your phone in your pocket, take a deep breath, and enjoy the real world!"

            span.set_data("script.length_chars", len(script))
            span.set_data("voice_id", self.voice_id)

            if self.api_key:
                try:
                    audio_b64, mime_type = await self._synthesize_elevenlabs(script)
                    span.set_data("provider", "ElevenLabs Live API")
                    span.set_data("status", "success")
                    return {
                        "has_audio": True,
                        "audio_base64": audio_b64,
                        "mime_type": mime_type,
                        "script": script,
                        "voice": "ElevenLabs Natural Outdoor Voice"
                    }
                except Exception as e:
                    logger.warning(f"ElevenLabs TTS generation failed: {e}")

            # Web Speech fallback
            span.set_data("provider", "Browser Web Speech API Fallback")
            return {
                "has_audio": False,
                "script": script,
                "use_web_speech": True,
                "voice": "Browser Neural Voice"
            }

    async def _synthesize_elevenlabs(self, text: str):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            audio_bytes = resp.content
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return audio_b64, "audio/mpeg"
