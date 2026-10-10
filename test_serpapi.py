import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.serpapi_service import SerpApiLocalOutdoorsService

async def main():
    svc = SerpApiLocalOutdoorsService()
    print("SerpApi Key configured:", bool(svc.api_key))
    
    res = await svc.get_local_outdoors_info("Seattle, WA", "Park")
    print("Weather info:", res.get("weather"))
    print("Nearby Spots:", res.get("nearby_spots"))

if __name__ == "__main__":
    asyncio.run(main())
