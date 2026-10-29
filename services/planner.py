"""
services/planner.py
Core rule-based trip planning and budget estimation engine for ODEYSSEY.
Implements deterministic ranking, daily scheduling, and transparent expense estimation.
"""

import json
import math
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

# Load destinations dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "destinations.json")


def load_destinations() -> List[Dict[str, Any]]:
    """Loads the curated destination database from destinations.json."""
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


DESTINATIONS_DATA = load_destinations()

VALID_STYLES = ["budget", "balanced", "comfort"]
VALID_INTERESTS = [
    "nature",
    "history",
    "food",
    "adventure",
    "culture",
    "shopping",
    "relaxation",
]
VALID_ACCOMMODATION = ["hostel_homestay", "standard_hotel", "boutique_resort"]
VALID_TRANSPORT = ["public_train", "cab_rental", "flight_local"]


def validate_trip_request(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Validates input fields.
    Returns:
        (is_valid, errors_dict, sanitized_payload)
    """
    errors = {}
    sanitized = {}

    # Destination
    destination = payload.get("destination", "").strip()
    if not destination:
        errors["destination"] = "Destination is required (e.g., Jaipur, Goa, Munnar)."
    elif len(destination) < 2:
        errors["destination"] = "Destination name must be at least 2 characters."
    sanitized["destination"] = destination

    # Start date
    start_date_str = payload.get("start_date", "").strip()
    if not start_date_str:
        errors["start_date"] = "Start date is required."
    else:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            sanitized["start_date"] = start_date_str
            sanitized["start_date_obj"] = start_date
        except ValueError:
            errors["start_date"] = "Invalid date format. Use YYYY-MM-DD."

    # Days
    days_val = payload.get("days", 3)
    try:
        days = int(days_val)
        if days < 1 or days > 14:
            errors["days"] = "Duration must be between 1 and 14 days."
        else:
            sanitized["days"] = days
    except (TypeError, ValueError):
        errors["days"] = "Duration must be a valid number of days (1-14)."

    # Travelers
    travelers_val = payload.get("travelers", 1)
    try:
        travelers = int(travelers_val)
        if travelers < 1 or travelers > 20:
            errors["travelers"] = "Travelers must be between 1 and 20."
        else:
            sanitized["travelers"] = travelers
    except (TypeError, ValueError):
        errors["travelers"] = "Travelers must be a valid number (1-20)."

    # Budget
    budget_val = payload.get("budget")
    if budget_val is None or budget_val == "":
        errors["budget"] = "Total budget in INR is required."
    else:
        try:
            budget = float(budget_val)
            if budget <= 0:
                errors["budget"] = "Budget must be greater than zero."
            elif budget < 1000:
                errors["budget"] = "Budget must be at least ₹1,000 for realistic trip planning."
            else:
                sanitized["budget"] = round(budget, 2)
        except (TypeError, ValueError):
            errors["budget"] = "Budget must be a valid numeric value."

    # Travel style
    style = payload.get("travel_style", "balanced").lower().strip()
    if style not in VALID_STYLES:
        errors["travel_style"] = f"Travel style must be one of: {', '.join(VALID_STYLES)}."
    else:
        sanitized["travel_style"] = style

    # Interests
    raw_interests = payload.get("interests", [])
    if isinstance(raw_interests, str):
        raw_interests = [i.strip() for i in raw_interests.split(",") if i.strip()]
    elif not isinstance(raw_interests, list):
        raw_interests = []

    cleaned_interests = [i.lower() for i in raw_interests if i.lower() in VALID_INTERESTS]
    if not cleaned_interests:
        # Sensible fallback if none selected
        cleaned_interests = ["culture", "relaxation"]
    sanitized["interests"] = cleaned_interests

    # Optional preferences
    sanitized["accommodation_pref"] = payload.get("accommodation_pref", "").strip() or None
    sanitized["transport_pref"] = payload.get("transport_pref", "").strip() or None
    sanitized["seed"] = payload.get("seed", 0)  # Seed for regeneration variations

    is_valid = len(errors) == 0
    return is_valid, errors, sanitized


def find_curated_destination(dest_name: str) -> Dict[str, Any] | None:
    """Finds a matching curated destination from destinations.json."""
    norm = dest_name.strip().lower()
    for d in DESTINATIONS_DATA:
        if d["id"].lower() == norm or d["name"].lower() == norm:
            return d
        if norm in d["name"].lower() or d["name"].lower() in norm:
            return d
    return None


def generate_fallback_activities(dest_name: str, interests: List[str]) -> List[Dict[str, Any]]:
    """
    Rule-based generator for destinations not in the curated dataset.
    Generates sensible activity templates aligned with selected interests.
    """
    templates = [
        {
            "id": "gen-morning-walk",
            "name": f"Morning Heritage & Landmarks Walk in {dest_name}",
            "time_slot": "morning",
            "duration_hours": 2.5,
            "cost_inr": 50,
            "interests": ["history", "culture"],
            "short_desc": f"Explore historic quarters, prominent public squares, and architecture of {dest_name}.",
            "tips": "Start early to enjoy quieter streets and softer morning light.",
        },
        {
            "id": "gen-local-breakfast",
            "name": f"Traditional Breakfast & Street Flavor Trail in {dest_name}",
            "time_slot": "morning",
            "duration_hours": 1.5,
            "cost_inr": 150,
            "interests": ["food", "culture"],
            "short_desc": f"Sample time-honored morning specialties and beverage culture popular in {dest_name}.",
            "tips": "Look for stalls crowded with local residents for the freshest batches.",
        },
        {
            "id": "gen-nature-park",
            "name": f"Scenic Park & Botanical Garden Leisure in {dest_name}",
            "time_slot": "morning",
            "duration_hours": 2.0,
            "cost_inr": 40,
            "interests": ["nature", "relaxation"],
            "short_desc": f"Unwind amidst greenery, walking paths, and peaceful open spaces in {dest_name}.",
            "tips": "A calm pause away from the vehicular hum of the city.",
        },
        {
            "id": "gen-museum-art",
            "name": f"Local Cultural Museum & Art Heritage in {dest_name}",
            "time_slot": "afternoon",
            "duration_hours": 2.5,
            "cost_inr": 100,
            "interests": ["culture", "history"],
            "short_desc": f"Discover historical artifacts, regional crafts, and cultural exhibits of {dest_name}.",
            "tips": "Check photography guidelines at the counter before entering galleries.",
        },
        {
            "id": "gen-craft-market",
            "name": f"Old Town Crafts & Souvenir Market in {dest_name}",
            "time_slot": "afternoon",
            "duration_hours": 2.5,
            "cost_inr": 0,
            "interests": ["shopping", "culture"],
            "short_desc": f"Browse regional textiles, handmade artifacts, and artisanal keepsakes in {dest_name}.",
            "tips": "Support independent artisans directly where possible.",
        },
        {
            "id": "gen-outdoor-view",
            "name": f"Scenic Ridge / Riverside Trail in {dest_name}",
            "time_slot": "afternoon",
            "duration_hours": 3.0,
            "cost_inr": 50,
            "interests": ["adventure", "nature"],
            "short_desc": f"Moderate outdoor trail offering elevated scenic views over the {dest_name} landscape.",
            "tips": "Carry hydration and wear shoes suitable for uneven steps.",
        },
        {
            "id": "gen-sunset-point",
            "name": f"Sunset Viewpoint & Quiet Promenade in {dest_name}",
            "time_slot": "evening",
            "duration_hours": 2.0,
            "cost_inr": 0,
            "interests": ["relaxation", "nature"],
            "short_desc": f"Gather at the community viewpoint to watch dusk settle over {dest_name}.",
            "tips": "Arrive 30 minutes before official sundown for the best colors.",
        },
        {
            "id": "gen-evening-bazaar",
            "name": f"Evening Food Street & Night Market in {dest_name}",
            "time_slot": "evening",
            "duration_hours": 2.5,
            "cost_inr": 200,
            "interests": ["food", "shopping", "culture"],
            "short_desc": f"Experience the lively twilight ambiance, dessert carts, and street delicacies of {dest_name}.",
            "tips": "Keep small INR currency notes handy for quick street transactions.",
        },
        {
            "id": "gen-cultural-music",
            "name": f"Traditional Performing Arts / Live Music Evening in {dest_name}",
            "time_slot": "evening",
            "duration_hours": 2.0,
            "cost_inr": 250,
            "interests": ["culture", "relaxation"],
            "short_desc": f"Enjoy an acoustic or regional cultural performance in {dest_name}.",
            "tips": "Confirm starting timings as evening programs typically start punctually.",
        },
    ]
    return templates


def score_activity(activity: Dict[str, Any], selected_interests: List[str]) -> float:
    """
    Computes a relevance score based on match count with selected interests.
    Activities with multiple matching tags receive higher priority.
    """
    act_interests = set(activity.get("interests", []))
    sel_interests = set(selected_interests)
    matches = len(act_interests.intersection(sel_interests))
    # Slight base bonus for having rich descriptions
    score = matches * 10.0
    if matches > 0:
        score += 5.0
    return score


def plan_itinerary(sanitized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based scheduling algorithm:
    1. Look up destination in dataset or generate fallback template.
    2. Rank all candidate activities according to user interests.
    3. Partition activities by time slot: morning, afternoon, evening.
    4. Distribute non-repeating activities across the days (max 3 per day).
    5. Calculate realistic budget breakdown and balance check.
    6. Return complete structured response with metadata and notes.
    """
    dest_name = sanitized["destination"]
    days = sanitized["days"]
    travelers = sanitized["travelers"]
    budget = sanitized["budget"]
    style = sanitized["travel_style"]
    interests = sanitized["interests"]
    accommodation_pref = sanitized["accommodation_pref"]
    transport_pref = sanitized["transport_pref"]
    start_date_obj = sanitized["start_date_obj"]
    seed_val = sanitized.get("seed", 0)

    curated = find_curated_destination(dest_name)
    is_curated = curated is not None

    if is_curated:
        display_name = curated["name"]
        state = curated["state"]
        tagline = curated["tagline"]
        overview = curated["overview"]
        coordinates = curated.get("coordinates")
        best_seasons = curated.get("best_seasons", ["Year-round"])
        candidate_activities = [dict(act) for act in curated["activities"]]
        daily_costs_table = curated.get("typical_daily_costs", {}).get(style, {})
        transport_baseline_table = curated.get("transport_baseline", {})
    else:
        display_name = dest_name.title()
        state = "Regional Hub"
        tagline = f"A customized discovery itinerary for {display_name}."
        overview = (
            f"A structured, interest-aligned trip plan for {display_name} based on "
            f"your preference for {', '.join(interests)}."
        )
        coordinates = None  # No fake coordinates
        best_seasons = ["October to March (typical for regional travel)"]
        candidate_activities = generate_fallback_activities(display_name, interests)
        # Default baseline cost assumptions for custom destination
        default_costs = {
            "budget": {"accommodation": 850, "food": 500, "local_transport": 250, "misc": 150},
            "balanced": {"accommodation": 2200, "food": 1050, "local_transport": 600, "misc": 300},
            "comfort": {"accommodation": 5500, "food": 2200, "local_transport": 1400, "misc": 700},
        }
        daily_costs_table = default_costs.get(style, default_costs["balanced"])
        transport_baseline_table = {
            "public_train": 900,
            "cab_rental": 2400,
            "flight_local": 4500,
        }

    # Rank candidate activities by user interests
    for act in candidate_activities:
        act["relevance_score"] = score_activity(act, interests)

    # Deterministic shuffle / rotation based on seed for regeneration support
    rng = random.Random(seed_val + len(dest_name))
    rng.shuffle(candidate_activities)

    # Sort primarily by relevance score descending
    candidate_activities.sort(key=lambda a: a["relevance_score"], reverse=True)

    # Split activities by slot
    mornings = [a for a in candidate_activities if a.get("time_slot") == "morning"]
    afternoons = [a for a in candidate_activities if a.get("time_slot") == "afternoon"]
    evenings = [a for a in candidate_activities if a.get("time_slot") == "evening"]
    flexibles = [a for a in candidate_activities if a.get("time_slot") not in ["morning", "afternoon", "evening"]]

    # Helper to pick next activity for a slot
    used_ids = set()

    def pick_activity(pool: List[Dict[str, Any]], fallback_pool: List[Dict[str, Any]], slot_name: str) -> Dict[str, Any]:
        # Try finding an unused one from pool
        for item in pool:
            if item["id"] not in used_ids:
                used_ids.add(item["id"])
                return dict(item)
        # Try from flexibles
        for item in flexibles:
            if item["id"] not in used_ids:
                used_ids.add(item["id"])
                clone = dict(item)
                clone["time_slot"] = slot_name
                return clone
        # Try from fallback pool
        for item in fallback_pool:
            if item["id"] not in used_ids:
                used_ids.add(item["id"])
                clone = dict(item)
                clone["time_slot"] = slot_name
                return clone
        # If exhausted all unique items, recycle highest scored with suffix
        source = pool if pool else candidate_activities
        chosen = dict(source[len(used_ids) % len(source)])
        chosen["id"] = f"{chosen['id']}-day{len(used_ids) + 1}"
        chosen["time_slot"] = slot_name
        return chosen

    # Build Day-by-Day schedule
    itinerary_days = []
    total_activity_entry_fees_single = 0

    for day_idx in range(days):
        current_date = start_date_obj + timedelta(days=day_idx)
        current_date_str = current_date.strftime("%Y-%m-%d")
        current_day_name = current_date.strftime("%A, %b %d")

        # Pick Morning, Afternoon, Evening
        morning_act = pick_activity(mornings, candidate_activities, "morning")
        afternoon_act = pick_activity(afternoons, candidate_activities, "afternoon")
        evening_act = pick_activity(evenings, candidate_activities, "evening")

        # Add Google Maps query link if coordinates available or destination name
        for act in [morning_act, afternoon_act, evening_act]:
            coords = act.get("coordinates")
            if coords:
                act["map_url"] = f"https://www.google.com/maps/search/?api=1&query={coords['lat']},{coords['lon']}"
            else:
                query_str = f"{act['name']}, {display_name}".replace(" ", "+")
                act["map_url"] = f"https://www.google.com/maps/search/?api=1&query={query_str}"

        day_activities = [morning_act, afternoon_act, evening_act]
        day_entry_total = sum(act.get("cost_inr", 0) for act in day_activities)
        total_activity_entry_fees_single += day_entry_total

        # Daily theme/focus
        top_day_tags = list(set([t for act in day_activities for t in act.get("interests", [])]))[:3]

        itinerary_days.append({
            "day_number": day_idx + 1,
            "date": current_date_str,
            "day_formatted": current_day_name,
            "theme": ", ".join([t.title() for t in top_day_tags]) if top_day_tags else "City Discovery",
            "activities": day_activities,
            "estimated_day_activity_cost": day_entry_total * travelers,
            "note": (
                "Remember to stay hydrated and leave 30-45 minutes between locations "
                "for comfortable travel and meal pauses."
            ),
        })

    # =========================================================================
    # BUDGET BREAKDOWN CALCULATION (Transparent & Mathematically Exact)
    # =========================================================================
    # 1. Accommodation
    # Base daily rates from table
    base_hotel_rate = daily_costs_table.get("accommodation", 2200)
    # Adjust if specific preference chosen
    if accommodation_pref == "hostel_homestay":
        hotel_rate = min(base_hotel_rate, 900)
    elif accommodation_pref == "boutique_resort":
        hotel_rate = max(base_hotel_rate, 5500)
    elif accommodation_pref == "standard_hotel":
        hotel_rate = 2400
    else:
        hotel_rate = base_hotel_rate

    # Room logic: 2 travelers per standard room (ceil)
    rooms_needed = math.ceil(travelers / 2)
    # Nights: for N days, standard stay is max(1, days - 1); 1-day trip has 0 nights or 1 day base
    nights = days if days == 1 else (days - 1)
    total_accommodation = rooms_needed * hotel_rate * nights

    # 2. Food
    daily_food_rate = daily_costs_table.get("food", 1000)
    total_food = daily_food_rate * days * travelers

    # 3. Local Transport (taxis/autos/metro inside destination)
    daily_local_transit_rate = daily_costs_table.get("local_transport", 600)
    # Cab seats ~3-4 people; if group > 3, scale vehicle count
    vehicles_needed = math.ceil(travelers / 3)
    total_local_transport = daily_local_transit_rate * vehicles_needed * days

    # 4. Activities & Entry Fees
    total_activities_fees = total_activity_entry_fees_single * travelers

    # 5. Intercity / Baseline Transport (getting to destination)
    if transport_pref == "flight_local":
        transit_per_person = transport_baseline_table.get("flight_local", 4800)
        total_intercity_transport = transit_per_person * travelers
    elif transport_pref == "cab_rental":
        cab_baseline = transport_baseline_table.get("cab_rental", 2500)
        total_intercity_transport = cab_baseline * vehicles_needed
    else:  # public_train / default
        transit_per_person = transport_baseline_table.get("public_train", 900)
        total_intercity_transport = transit_per_person * travelers

    # 6. Miscellaneous (water, tips, snacks, small buffer ~5%)
    subtotal_before_misc = (
        total_accommodation
        + total_food
        + total_local_transport
        + total_activities_fees
        + total_intercity_transport
    )
    total_misc = round(subtotal_before_misc * 0.05)

    # Total estimated cost
    total_estimated_cost = subtotal_before_misc + total_misc
    remaining_budget = round(budget - total_estimated_cost, 2)

    # Budget Health Analysis
    if remaining_budget >= 0:
        budget_status = "within_budget"
        budget_message = (
            f"Your plan is well within your budget. You have an estimated buffer of "
            f"₹{remaining_budget:,.0f} for personal shopping or extra experiences."
        )
        saving_suggestions = []
    else:
        budget_status = "exceeds_budget"
        deficit = abs(remaining_budget)
        budget_message = (
            f"Estimated trip expenses exceed your budget by ₹{deficit:,.0f}. "
            f"Review suggested adjustments below to bring the trip within limits."
        )
        saving_suggestions = []
        if style != "budget":
            saving_suggestions.append(
                "Switching your Travel Style to 'Budget' (hostels & public transit) can save up to 40%."
            )
        if days > 3:
            saving_suggestions.append(
                f"Shortening the trip by 1 day would reduce accommodation and food costs by approximately ₹{(hotel_rate * rooms_needed + daily_food_rate * travelers):,.0f}."
            )
        saving_suggestions.append(
            "Opting for sleeper or 3AC trains instead of flights significantly cuts transport expense."
        )

    budget_breakdown = {
        "user_budget": budget,
        "total_estimated_cost": round(total_estimated_cost, 2),
        "remaining_budget": remaining_budget,
        "status": budget_status,
        "message": budget_message,
        "suggestions": saving_suggestions,
        "categories": {
            "accommodation": {
                "label": "Accommodation",
                "amount": round(total_accommodation, 2),
                "basis": f"₹{hotel_rate:,}/room/night × {rooms_needed} room(s) × {nights} night(s)",
            },
            "food": {
                "label": "Food & Dining",
                "amount": round(total_food, 2),
                "basis": f"₹{daily_food_rate:,}/traveler/day × {travelers} traveler(s) × {days} day(s)",
            },
            "local_transport": {
                "label": "Local Commute & Transfers",
                "amount": round(total_local_transport, 2),
                "basis": f"₹{daily_local_transit_rate:,}/day × {vehicles_needed} vehicle(s) × {days} day(s)",
            },
            "activities_entry": {
                "label": "Activities & Entry Tickets",
                "amount": round(total_activities_fees, 2),
                "basis": f"Sum of {len(itinerary_days) * 3} activity admission fees for {travelers} traveler(s)",
            },
            "intercity_transport": {
                "label": "Intercity Transport Estimate",
                "amount": round(total_intercity_transport, 2),
                "basis": f"Baseline for selected '{transport_pref or 'train/bus'}' mode for {travelers} traveler(s)",
            },
            "miscellaneous": {
                "label": "Contingency & Incidentals",
                "amount": round(total_misc, 2),
                "basis": "5% emergency contingency, bottled water, porterage & tips",
            },
        },
    }

    # Destination travel notes
    travel_notes = [
        f"Ideal season: {', '.join(best_seasons)}.",
        "Keep digital copies of photo IDs on your phone for hotel check-ins.",
        "Carry some physical cash notes for small street vendors and rickshaw fares.",
    ]
    if is_curated:
        travel_notes.append("Suggested places and entry fees reflect curated sample averages for Indian tourism.")
    else:
        travel_notes.append("Generated itinerary framework based on your selected interests. Check individual venue opening times.")

    return {
        "success": True,
        "destination": {
            "name": display_name,
            "state": state,
            "tagline": tagline,
            "overview": overview,
            "is_curated": is_curated,
            "coordinates": coordinates,
            "best_seasons": best_seasons,
        },
        "trip_params": {
            "start_date": sanitized["start_date"],
            "days": days,
            "travelers": travelers,
            "budget": budget,
            "travel_style": style,
            "interests": interests,
            "accommodation_pref": accommodation_pref,
            "transport_pref": transport_pref,
            "seed": seed_val,
        },
        "days": itinerary_days,
        "budget_breakdown": budget_breakdown,
        "travel_notes": travel_notes,
    }
