"""
tests/test_api.py
Integration tests for ODEYSSEY Flask routes and REST API endpoints.
"""

import json
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """GET /api/health returns 200 OK and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_destinations_endpoint(client):
    """GET /api/destinations returns curated list."""
    response = client.get("/api/destinations")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] >= 6
    assert len(data["destinations"]) == data["count"]


def test_plan_endpoint_valid(client):
    """POST /api/plan returns complete itinerary and budget for valid payload."""
    payload = {
        "destination": "Goa",
        "start_date": "2026-11-15",
        "days": 4,
        "travelers": 2,
        "budget": 35000,
        "travel_style": "balanced",
        "interests": ["nature", "relaxation"],
    }
    response = client.post(
        "/api/plan",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["destination"]["name"] == "Goa"
    assert len(data["days"]) == 4
    assert "budget_breakdown" in data
    assert "weather" in data


def test_plan_endpoint_invalid_json(client):
    """POST /api/plan without JSON returns 400 Bad Request."""
    response = client.post("/api/plan", data="not json", content_type="text/plain")
    assert response.status_code == 400


def test_plan_endpoint_validation_failure(client):
    """POST /api/plan with missing required fields returns 422 Unprocessable Entity."""
    response = client.post(
        "/api/plan",
        data=json.dumps({"destination": ""}),
        content_type="application/json",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert data["success"] is False
    assert "field_errors" in data
    assert "destination" in data["field_errors"]


def test_weather_endpoint_by_destination(client):
    """GET /api/weather?destination=Jaipur returns weather forecast."""
    response = client.get("/api/weather?destination=Jaipur&days=3")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data


def test_page_routes(client):
    """Web pages return 200 OK HTML."""
    for path in ["/", "/planner", "/my-trips", "/about"]:
        res = client.get(path)
        assert res.status_code == 200
        assert b"ODEYSSEY" in res.data
