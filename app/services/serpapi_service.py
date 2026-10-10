import os
import logging
import httpx
from typing import Dict, Any, List
from app.services.sentry_service import AgentSpan

logger = logging.getLogger("trailmates.serpapi")

class SerpApiLocalOutdoorsService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")

    async def get_local_outdoors_info(self, location: str, setting: str) -> Dict[str, Any]:
        with AgentSpan(
            name="SerpApi Live Green Space Search",
            op="ai.tool.serpapi",
            description="Searches Google Maps via SerpApi for local parks and green spaces"
        ) as span:
            span.set_data("input.location", location)
            span.set_data("input.setting", setting)

            if self.api_key and location and location != "Nearby Nature":
                try:
                    results = await self._search_serpapi(location, setting)
                    span.set_data("provider", "SerpApi live Google Maps search")
                    return results
                except Exception as e:
                    logger.warning(f"SerpApi search failed: {e}")

            # Static defaults — not live data
            span.set_data("provider", "static-defaults (no SerpApi key or location)")
            return {
                "weather": {
                    "temp_c": 20,
                    "condition": "Check local forecast",
                    "source": "static-default"
                },
                "nearby_spots": [
                    {"name": "Your local park", "type": "Park & Walking Trail", "source": "static-default"},
                    {"name": "Nearby green space", "type": "Outdoor Area", "source": "static-default"}
                ]
            }

    async def _search_serpapi(self, location: str, setting: str) -> Dict[str, Any]:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": f"parks nature trails green spaces in {location}",
            "api_key": self.api_key
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            local_results = data.get("local_results", [])
            spots = []
            for spot in local_results[:3]:
                spots.append({
                    "name": spot.get("title", "Local Trail"),
                    "type": spot.get("type", "Green Space"),
                    "rating": spot.get("rating"),
                    "address": spot.get("address", location),
                    "source": "serpapi-live"
                })

            return {
                # Weather is not fetched from SerpApi — label clearly
                "weather": {"temp_c": None, "condition": "Check local forecast", "source": "static-default"},
                "nearby_spots": spots if spots else [
                    {"name": f"Parks near {location}", "type": "Public Park", "source": "serpapi-live"}
                ]
            }
