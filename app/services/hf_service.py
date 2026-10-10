import os
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.services.sentry_service import AgentSpan

logger = logging.getLogger("trailmates.hf")

# Default model — HF-recommended conversational LLM (no gated license)
# Qwen2.5-7B-Instruct is on HF's recommended list and available via hf-inference provider
DEFAULT_HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Official HF Inference Providers Router base URL (from HF docs, Oct 2026)
# https://huggingface.co/docs/api-inference/tasks/chat-completion
# base_url = "https://router.huggingface.co/v1"
# Full endpoint:
HF_ROUTER_ENDPOINT = "https://router.huggingface.co/v1/chat/completions"

# Fallback: model-specific serverless endpoint
# https://huggingface.co/docs/api-inference/en/getting-started
HF_SERVERLESS_ENDPOINT_TEMPLATE = (
    "https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
)

SYSTEM_PROMPT = """You are TrailMates, a friendly outdoor companion AI.
Your goal is to help users spend less time on screens and step outside into nature.
Given the user's outdoor preferences, generate a practical, grounded, step-by-step outdoor adventure.

You MUST respond strictly in valid JSON format matching this schema:
{
  "title": "Creative Adventure Title",
  "description": "A warm, inspiring 1-2 sentence overview of the activity.",
  "total_duration_min": 30,
  "steps": [
    {
      "step_number": 1,
      "title": "Step Title",
      "description": "Specific action to do outdoors",
      "duration_min": 10
    }
  ],
  "items_to_bring": ["Item 1", "Item 2", "Item 3"],
  "safety_tips": ["Safety tip 1", "Leave no trace tip 2"],
  "phone_free_challenge": {
    "name": "Challenge Name",
    "instructions": "Screen-free sensory challenge",
    "phone_rule": "Put phone on Do Not Disturb!"
  },
  "reflection_question": "A thoughtful question to consider after finishing the walk."
}
Do not add any markdown formatting or extra text outside the JSON object.
"""


class HuggingFaceInferenceService:
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        self.model_name = os.getenv("HF_MODEL", DEFAULT_HF_MODEL).strip()

        # Official HF router endpoint (corrected from /hf-inference/v1 → /v1)
        self.router_url = HF_ROUTER_ENDPOINT

        # Per-model serverless fallback
        self.serverless_url = HF_SERVERLESS_ENDPOINT_TEMPLATE.format(model=self.model_name)

    def is_configured(self) -> bool:
        return bool(self.hf_token)

    async def generate_plan(
        self,
        activity: str,
        time_min: int,
        energy_level: str,
        setting: str,
        interests: List[str],
        optional_note: Optional[str] = None,
        tabpfn_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        with AgentSpan(
            name="Hugging Face Open-Weight Model Inference",
            op="ai.model.huggingface",
            description=f"Generates outdoor adventure plan via {self.model_name}"
        ) as span:
            span.set_data("hf_model", self.model_name)
            span.set_data("activity", activity)
            span.set_data("time_min", time_min)
            span.set_data("energy_level", energy_level)
            span.set_data("setting", setting)
            span.set_data("is_token_configured", self.is_configured())

            if not self.is_configured():
                logger.info("HF_TOKEN not configured — returning rule-based demo plan.")
                span.set_data("fallback_reason", "HF_TOKEN missing")
                return self._generate_rule_based_demo_plan(
                    activity, time_min, energy_level, setting, interests,
                    optional_note, tabpfn_metrics
                )

            prompt = (
                f"Create a personalized outdoor adventure plan:\n"
                f"- Primary Activity: {activity}\n"
                f"- Time Available: {time_min} minutes\n"
                f"- Energy Level: {energy_level}\n"
                f"- Outdoor Setting: {setting}\n"
                f"- Interests: {', '.join(interests) if interests else 'General Exploration'}\n"
                f"- User Note: {optional_note or 'None'}\n"
                f"- TabPFN Suitability Pace: "
                f"{tabpfn_metrics.get('recommended_pace', 'Moderate pace') if tabpfn_metrics else 'Moderate'}\n\n"
                f"Ensure the plan fits exactly {time_min} minutes. "
                f"Focus on mindfulness, sensory observation, and getting off screens.\n"
                f"Return JSON only — no markdown, no extra text."
            )

            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 1200,
            }

            async with httpx.AsyncClient(timeout=25.0) as client:

                # ── Attempt 1: Official HF Router /v1/chat/completions ──────────
                try:
                    logger.info(f"Trying HF Router: {self.router_url}")
                    resp = await client.post(self.router_url, json=payload, headers=headers)
                    logger.info(f"HF Router status: {resp.status_code}")

                    if resp.status_code == 200:
                        result = self._extract_ai_result(resp, source="HF Router /v1")
                        if result:
                            span.set_data("status", "success")
                            span.set_data("endpoint_used", "router_v1")
                            return result
                    else:
                        logger.warning(f"HF Router non-200: {resp.status_code} — {resp.text[:300]}")

                except Exception as exc:
                    logger.warning(f"HF Router attempt failed: {exc}")

                # ── Attempt 2: Per-model serverless /v1/chat/completions ─────────
                try:
                    logger.info(f"Trying HF Serverless: {self.serverless_url}")
                    resp = await client.post(self.serverless_url, json=payload, headers=headers)
                    logger.info(f"HF Serverless status: {resp.status_code}")

                    if resp.status_code == 200:
                        result = self._extract_ai_result(resp, source=f"HF Serverless ({self.model_name})")
                        if result:
                            span.set_data("status", "success")
                            span.set_data("endpoint_used", "serverless_v1")
                            return result
                    else:
                        logger.warning(f"HF Serverless non-200: {resp.status_code} — {resp.text[:300]}")

                except Exception as exc:
                    logger.warning(f"HF Serverless attempt failed: {exc}")

            # ── All endpoints failed → honest rule-based fallback ────────────
            span.set_data("fallback_reason", "All HF API endpoints failed or timed out")
            logger.warning("All HF endpoints failed — using rule-based fallback.")
            demo = self._generate_rule_based_demo_plan(
                activity, time_min, energy_level, setting, interests,
                optional_note, tabpfn_metrics
            )
            # Never badge a rule-based plan as AI-generated
            demo["is_ai_generated"] = False
            demo["attribution"] = (
                "Demo plan — AI inference error or timeout. Using rule-based fallback."
            )
            return demo

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_ai_result(self, resp: httpx.Response, source: str) -> Optional[Dict[str, Any]]:
        """
        Parses the OpenAI-compatible chat completion response.
        Returns a plan dict ONLY if the model actually returned content.
        Never returns a fallback plan disguised as AI output.
        """
        try:
            data = resp.json()
        except Exception as exc:
            logger.warning(f"JSON parse error from {source}: {exc}")
            return None

        # Validate OpenAI-compatible structure
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            logger.warning(f"{source}: response has no 'choices' field — {str(data)[:200]}")
            return None

        message = choices[0].get("message", {})
        raw_text = message.get("content", "").strip()

        if not raw_text:
            logger.warning(f"{source}: model returned empty content.")
            return None

        # Verify it's genuine model output (not an error message in JSON)
        if len(raw_text) < 80:
            logger.warning(f"{source}: suspiciously short response ({len(raw_text)} chars): {raw_text}")
            return None

        try:
            plan_data = self._parse_json_response(raw_text)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(f"{source}: JSON parse failed — {exc}. Raw: {raw_text[:200]}")
            return None

        # Confirm the parsed object has the required keys of a real plan
        if "title" not in plan_data or "steps" not in plan_data:
            logger.warning(f"{source}: parsed JSON missing 'title' or 'steps'.")
            return None

        # Record which model actually responded (from response body if available)
        responding_model = data.get("model", self.model_name)
        logger.info(f"AI plan successfully generated by {responding_model} via {source}")

        plan_data["is_ai_generated"] = True
        plan_data["attribution"] = (
            f"Generated by open-weight AI — {responding_model} via Hugging Face"
        )
        plan_data["model_name"] = responding_model
        plan_data["inference_source"] = source
        return plan_data

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Strips markdown code fences and parses JSON."""
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean = clean[start : end + 1]
        return json.loads(clean)

    def _generate_rule_based_demo_plan(
        self,
        activity: str,
        time_min: int,
        energy_level: str,
        setting: str,
        interests: List[str],
        optional_note: Optional[str],
        tabpfn_metrics: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        act_title = activity if activity != "Surprise me" else "Mindful Exploration"

        if "Any" in setting or not setting:
            setting_clean = "Outdoors"
        elif "Park" in setting:
            setting_clean = "Park"
        elif "Garden" in setting:
            setting_clean = "Garden"
        elif "Neighborhood" in setting:
            setting_clean = "Neighborhood"
        elif "Trail" in setting or "Hiking" in setting:
            setting_clean = "Forest Trail"
        else:
            setting_clean = setting.split()[0]

        step_1_m = max(3, int(time_min * 0.2))
        step_2_m = max(8, int(time_min * 0.6))
        step_3_m = max(4, time_min - step_1_m - step_2_m)

        title = (
            f"The {act_title} Outdoor Escape"
            if setting_clean == "Outdoors"
            else f"The {act_title} in the {setting_clean}"
        )

        return {
            "title": title,
            "description": (
                f"A refreshing {time_min}-minute screen-free adventure "
                f"tailored to your {energy_level.lower()} energy level."
            ),
            "total_duration_min": time_min,
            "steps": [
                {
                    "step_number": 1,
                    "title": "Unplug & Transition Outside",
                    "description": (
                        f"Step out into your nearby {setting.lower()}. "
                        "Put your phone on Do Not Disturb and take 3 slow outdoor breaths."
                    ),
                    "duration_min": step_1_m,
                },
                {
                    "step_number": 2,
                    "title": f"Engage in {act_title}",
                    "description": (
                        f"Move at a {energy_level.lower()} pace. Notice 3 unique natural details "
                        "(leaf patterns, light reflections, or bird movements) without taking out your phone."
                    ),
                    "duration_min": step_2_m,
                },
                {
                    "step_number": 3,
                    "title": "Grounding Sit & Pause",
                    "description": (
                        "Find a bench, rock, or comfortable patch of grass. "
                        "Sit quietly and feel the breeze against your face."
                    ),
                    "duration_min": step_3_m,
                },
            ],
            "items_to_bring": [
                "Water bottle 💧",
                "Comfortable walking shoes 👟",
                "Weather jacket / sweater 🧥",
                "Phone in DO-NOT-DISTURB mode 📱🔒",
            ],
            "safety_tips": [
                "Stay aware of your surroundings and pedestrian traffic 🚶",
                "Respect local flora & fauna — leave no trace 🌿",
                "Stay hydrated and dress for current weather 🌤️",
            ],
            "phone_free_challenge": {
                "name": "The 5-4-3-2-1 Sensory Challenge",
                "instructions": (
                    "Identify 5 natural textures, 4 ambient outdoor sounds, "
                    "3 leaf colours, 2 natural scents, and feel 1 cool breeze."
                ),
                "phone_rule": "Keep your screen in your pocket until you finish your final step!",
            },
            "reflection_question": (
                "What is one small natural detail you noticed today "
                "that you would have missed while staring at a screen?"
            ),
            "is_ai_generated": False,
            "attribution": "Demo plan — AI inference is not configured or currently unavailable",
            "model_name": self.model_name,
        }
