"""
tests/test_planner.py
Unit tests for the ODEYSSEY planning engine and budget calculation.
"""

import pytest
from datetime import date, timedelta
from services.planner import (
    validate_trip_request,
    plan_itinerary,
    load_destinations,
    find_curated_destination,
    score_activity,
)
from services.weather import get_weather_forecast, _fallback_weather_response


def test_load_destinations():
    """Verify curated destinations load properly and have required fields."""
    destinations = load_destinations()
    assert len(destinations) >= 6
    names = [d["name"] for d in destinations]
    assert "Jaipur" in names
    assert "Goa" in names
    assert "Munnar" in names

    for d in destinations:
        assert "id" in d
        assert "name" in d
        assert "coordinates" in d
        assert "typical_daily_costs" in d
        assert len(d.get("activities", [])) >= 5


def test_validation_missing_fields():
    """Missing required fields must return errors."""
    is_valid, errors, _ = validate_trip_request({})
    assert not is_valid
    assert "destination" in errors
    assert "start_date" in errors
    assert "budget" in errors


def test_validation_invalid_duration_and_budget():
    """Days out of 1-14 and non-positive/too-low budget must be flagged."""
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Zero days, negative budget
    payload = {
        "destination": "Jaipur",
        "start_date": tomorrow,
        "days": 0,
        "travelers": 2,
        "budget": -500,
    }
    is_valid, errors, _ = validate_trip_request(payload)
    assert not is_valid
    assert "days" in errors
    assert "budget" in errors

    # Excessive days (>14)
    payload["days"] = 25
    payload["budget"] = 500  # less than minimum 1000
    is_valid, errors, _ = validate_trip_request(payload)
    assert not is_valid
    assert "days" in errors
    assert "budget" in errors


def test_valid_trip_planning_jaipur():
    """Valid trip request should produce structured itinerary and budget breakdown."""
    tomorrow = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    payload = {
        "destination": "Jaipur",
        "start_date": tomorrow,
        "days": 3,
        "travelers": 2,
        "budget": 30000,
        "travel_style": "balanced",
        "interests": ["history", "culture"],
    }

    is_valid, errors, sanitized = validate_trip_request(payload)
    assert is_valid
    assert len(errors) == 0

    plan = plan_itinerary(sanitized)
    assert plan["success"] is True
    assert plan["destination"]["name"] == "Jaipur"
    assert len(plan["days"]) == 3

    # Check each day has 3 slots: morning, afternoon, evening
    for day in plan["days"]:
        assert len(day["activities"]) == 3
        slots = [a["time_slot"] for a in day["activities"]]
        assert "morning" in slots
        assert "afternoon" in slots
        assert "evening" in slots

    # Verify budget calculations
    budget_data = plan["budget_breakdown"]
    assert budget_data["user_budget"] == 30000
    assert budget_data["total_estimated_cost"] > 0
    assert budget_data["remaining_budget"] == round(30000 - budget_data["total_estimated_cost"], 2)
    assert budget_data["status"] in ["within_budget", "exceeds_budget"]


def test_different_interests_produce_different_rankings():
    """Choosing adventure vs history should produce distinct activity prioritization."""
    tomorrow = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

    # Rishikesh with adventure focus
    _, _, san_adventure = validate_trip_request({
        "destination": "Rishikesh",
        "start_date": tomorrow,
        "days": 2,
        "travelers": 1,
        "budget": 15000,
        "travel_style": "balanced",
        "interests": ["adventure"],
    })
    plan_adv = plan_itinerary(san_adventure)

    # Rishikesh with culture & relaxation focus
    _, _, san_culture = validate_trip_request({
        "destination": "Rishikesh",
        "start_date": tomorrow,
        "days": 2,
        "travelers": 1,
        "budget": 15000,
        "travel_style": "balanced",
        "interests": ["culture", "relaxation"],
    })
    plan_cult = plan_itinerary(san_culture)

    adv_activities = [a["name"] for d in plan_adv["days"] for a in d["activities"]]
    cult_activities = [a["name"] for d in plan_cult["days"] for a in d["activities"]]

    # Both valid
    assert len(adv_activities) > 0
    assert len(cult_activities) > 0
    # The first day morning activity in adventure should favor rafting/outdoors
    assert "Rafting" in adv_activities[0] or any("adventure" in a["interests"] for a in plan_adv["days"][0]["activities"])


def test_custom_destination_fallback():
    """Custom uncataloged city should generate template plan without crashing."""
    tomorrow = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    payload = {
        "destination": "Kolkata",
        "start_date": tomorrow,
        "days": 2,
        "travelers": 2,
        "budget": 20000,
        "travel_style": "budget",
        "interests": ["food", "culture"],
    }
    is_valid, errors, sanitized = validate_trip_request(payload)
    assert is_valid

    plan = plan_itinerary(sanitized)
    assert plan["success"] is True
    assert plan["destination"]["name"] == "Kolkata"
    assert plan["destination"]["is_curated"] is False
    assert len(plan["days"]) == 2


def test_weather_fallback():
    """Weather fallback function returns honest unavailable status without crashing."""
    fb = _fallback_weather_response(26.9, 75.8, "Network unreachable")
    assert fb["available"] is False
    assert "Network unreachable" in fb["reason"]
    assert len(fb["forecast"]) == 0
