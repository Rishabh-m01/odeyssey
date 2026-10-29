"""
app.py
ODEYSSEY — Minimalist Smart Trip Planner
Flask backend application providing page routes and REST API endpoints.
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from services.planner import (
    validate_trip_request,
    plan_itinerary,
    load_destinations,
    find_curated_destination,
)
from services.weather import get_weather_forecast

# Load environment variables if present
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "odeyssey-college-project-2026-key")


# =============================================================================
# PAGE ROUTES (Clean Semantic Web Views)
# =============================================================================

@app.route("/")
def index():
    """Landing page featuring brand identity, curated destinations, and planner entry."""
    curated = load_destinations()
    return render_template("index.html", destinations=curated)


@app.route("/planner")
def planner():
    """Trip planner interactive interface and itinerary generator."""
    curated = load_destinations()
    prefill_dest = request.args.get("destination", "")
    return render_template("planner.html", destinations=curated, prefill_destination=prefill_dest)


@app.route("/my-trips")
def my_trips():
    """Saved trips view powered by browser local storage."""
    return render_template("my_trips.html")


@app.route("/about")
def about():
    """Project documentation, architecture, and technology overview."""
    return render_template("about.html")


# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@app.route("/api/health", methods=["GET"])
def api_health():
    """Returns basic service health status."""
    return jsonify({
        "status": "healthy",
        "service": "ODEYSSEY Trip Planner API",
        "version": "1.0.0",
        "storage": "Local Browser + In-Memory Python Engine",
    }), 200


@app.route("/api/destinations", methods=["GET"])
def api_destinations():
    """Returns list of curated destinations and their metadata."""
    destinations = load_destinations()
    simplified = [
        {
            "id": d["id"],
            "name": d["name"],
            "state": d["state"],
            "tagline": d["tagline"],
            "overview": d["overview"],
            "best_seasons": d.get("best_seasons", []),
            "coordinates": d.get("coordinates"),
        }
        for d in destinations
    ]
    return jsonify({"success": True, "count": len(simplified), "destinations": simplified}), 200


@app.route("/api/plan", methods=["POST"])
def api_plan():
    """
    Validates submitted trip preferences and generates a structured itinerary,
    budget breakdown, and live weather forecast (if destination coordinates known).
    """
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Request body must be valid JSON.",
        }), 400

    payload = request.get_json()
    is_valid, errors, sanitized = validate_trip_request(payload)

    if not is_valid:
        return jsonify({
            "success": False,
            "error": "Validation failed.",
            "field_errors": errors,
        }), 422

    # Generate itinerary through deterministic rule-based planner
    plan_result = plan_itinerary(sanitized)

    # Attach weather forecast if coordinates exist
    coords = plan_result["destination"].get("coordinates")
    if coords and "lat" in coords and "lon" in coords:
        weather_info = get_weather_forecast(
            lat=coords["lat"],
            lon=coords["lon"],
            days=sanitized["days"],
        )
        plan_result["weather"] = weather_info
    else:
        plan_result["weather"] = {
            "available": False,
            "reason": "Coordinates not available for custom destination.",
            "forecast": [],
        }

    return jsonify(plan_result), 200


@app.route("/api/weather", methods=["GET"])
def api_weather():
    """
    Fetches real-time weather from Open-Meteo for specified lat/lon or destination id.
    """
    lat_val = request.args.get("lat")
    lon_val = request.args.get("lon")
    dest_name = request.args.get("destination")
    days_val = request.args.get("days", 5)

    try:
        days = int(days_val)
    except ValueError:
        days = 5

    lat = None
    lon = None

    if lat_val and lon_val:
        try:
            lat = float(lat_val)
            lon = float(lon_val)
        except ValueError:
            return jsonify({"success": False, "error": "lat and lon must be numeric"}), 400
    elif dest_name:
        curated = find_curated_destination(dest_name)
        if curated and curated.get("coordinates"):
            lat = curated["coordinates"]["lat"]
            lon = curated["coordinates"]["lon"]
        else:
            return jsonify({
                "success": False,
                "error": f"No coordinates found for destination '{dest_name}'.",
            }), 404
    else:
        return jsonify({
            "success": False,
            "error": "Provide either (lat, lon) or 'destination' query parameter.",
        }), 400

    forecast = get_weather_forecast(lat=lat, lon=lon, days=days)
    return jsonify({"success": True, "data": forecast}), 200


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found_handler(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "API route not found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error_handler(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ["1", "true", "yes"]
    print(f"Starting ODEYSSEY server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
