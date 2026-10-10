import asyncio
import sys

# Ensure UTF-8 stdout encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

from app.main import generate_adventure, AdventureRequest

async def main():
    req = AdventureRequest(
        available_time_min=30,
        energy_level="Medium",
        setting="Forest Trail 🌲",
        interests=["Fall Foliage 🍁", "Birdwatching 🐦"],
        location="Seattle, WA"
    )
    print("Testing TrailMates Multi-Agent Workflow Pipeline...")
    res = await generate_adventure(req)
    print("Workflow executed successfully!")
    print("TabPFN Analytics:", res["tabpfn_analytics"])
    print("Adventure Plan Title:", res["adventure_plan"]["title"])
    print("Audio Briefing Voice:", res["audio_briefing"]["voice"])
    print("Recorded Spans:", res["sentry_trace_summary"])

if __name__ == "__main__":
    asyncio.run(main())
