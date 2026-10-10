import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_homepage_loads():
    """Verify GET / returns 200 and serves HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "TrailMates" in response.text

def test_health_check_endpoint():
    """Verify GET /health returns 200 for Render health checks."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "trailmates"

def test_api_status_endpoint():
    """Verify GET /api/status reports AI status without exposing secrets."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "ai_configured" in data
    assert "model_name" in data
    assert "provider" in data
    assert "HF_TOKEN" not in data # Ensure no secrets exposed

def test_create_plan_valid():
    """Verify POST /api/plan returns a valid structured adventure plan."""
    payload = {
        "activity": "Walking",
        "available_time_min": 30,
        "energy_level": "Medium",
        "setting": "Park",
        "interests": ["Nature", "Mindfulness"],
        "optional_note": "Prefer quiet area"
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "plan" in data
    assert "tabpfn_analytics" in data
    assert "audio_briefing" in data
    
    plan = data["plan"]
    assert "title" in plan
    assert "steps" in plan
    assert "items_to_bring" in plan
    assert "safety_tips" in plan
    assert "phone_free_challenge" in plan
    assert "reflection_question" in plan
    assert "attribution" in plan

def test_create_plan_sanitizes_note():
    """Verify backend sanitizes HTML tags and limits optional note length."""
    payload = {
        "activity": "Birdwatching",
        "available_time_min": 45,
        "energy_level": "Low",
        "setting": "Garden",
        "interests": ["Nature"],
        "optional_note": "<script>alert('xss')</script> Quiet spot near flowers"
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_honest_fallback_attribution():
    """Verify demo mode is clearly labeled when AI token is not set."""
    payload = {
        "activity": "Surprise me",
        "available_time_min": 15,
        "energy_level": "High",
        "setting": "Hiking trail",
        "interests": ["Exploration"]
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "attribution" in data
    assert "is_ai_generated" in data
