# ODEYSSEY — Minimalist Smart Trip Planner

> **College Mini Project**  
> *"Less planning. More exploring."*

**ODEYSSEY** is a minimalist, responsive trip-planning web application designed to solve real travel planning friction. Instead of noisy advertising, overwhelming 50-stop whirlwind schedules, or fake AI promises, Odeyssey provides a transparent, deterministic rule-based planning engine that balances destination constraints, duration, INR budget, and traveler interests into paced, feasible day-by-day itineraries.

---

## 🌟 Key Features

1. **Minimalist Aesthetic & Restrained UI:**
   - Editorial warm off-white and charcoal theme with subtle sage green accents.
   - Clean card-based layouts with generous whitespace and clear typography (Inter).
   - Fully responsive for mobile, tablet, and desktop screens.

2. **Smart Parameterized Trip Generation:**
   - Destination selector with curated Indian locations (Jaipur, Goa, Munnar, Manali, Udaipur, Rishikesh, Varanasi, Hampi) or any custom city.
   - Flexible dates and duration (1 to 14 days) with quick preset pills (Weekend, Classic 3-Day, 5-Day, Full Week).
   - Traveler count and total INR budget with real-time validation.
   - Travel styles: *Budget* (hostels & transit), *Balanced* (3-star hotels & cabs), and *Comfort* (resorts & private rentals).
   - Multi-select interest filtering: Nature, History, Food, Adventure, Culture, Shopping, and Relaxation.

3. **Human-Paced Day-by-Day Itineraries:**
   - Maximum 3 primary activities per day structured into Morning (9:00 AM–12:30 PM), Afternoon (2:00 PM–5:00 PM), and Evening (6:00 PM–8:30 PM) slots.
   - Meaningful activity descriptions, estimated durations, admission fees, and practical local tips.
   - One-click activity removal with instant automatic budget recalculation.

4. **Transparent INR Budget Breakdown:**
   - Itemized categorization: Accommodation, Activities & Entry, Food & Dining, Intercity Transport, Local Commute, and 5% Contingency.
   - Real-time comparison against the user's target budget with dynamic status indicators (*Within Budget* vs *Exceeds Budget*).
   - Editable expense fields for custom fine-tuning.

5. **Live Weather & Map Integration:**
   - Real-time weather forecasts powered by the open **Open-Meteo API** (zero API key required, with in-memory caching and offline fallback).
   - Interactive destination and route mapping powered by **Leaflet** and **OpenStreetMap**.

6. **Browser Local Storage & Offline Friendly:**
   - Bookmarked itineraries are saved in browser `localStorage`.
   - View, export as JSON, print, or reload saved trips into the planner anytime without needing a server account.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Tier                           │
│  - Semantic HTML5 + Responsive CSS3 (CSS Variables, Flex/Grid)│
│  - ES6 Modular JavaScript Controller (static/js/app.js)     │
│  - Leaflet.js + OpenStreetMap Tile Layer                    │
│  - HTML5 Web Storage (localStorage for saved trips)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP JSON REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    Application / Web Tier                   │
│  - Python 3 + Flask (app.py)                                │
│  - REST API Endpoints (/api/health, /api/destinations, ...) │
│  - Template Engine (Jinja2) for clean semantic views        │
└──────────────────────────────┬──────────────────────────────┘
                               │ Internal Function Calls
┌──────────────────────────────▼──────────────────────────────┐
│                      Business Logic Tier                    │
│  - Deterministic Rule-Based Planner (services/planner.py)    │
│  - Interest Scoring, Slot Allocation, Budget Calculation    │
│  - Weather Integration & Cache Manager (services/weather.py)│
└──────────────────────────────┬──────────────────────────────┘
                               │ External HTTP GET
┌──────────────────────────────▼──────────────────────────────┐
│                    External Services Tier                   │
│  - Open-Meteo Weather API (https://api.open-meteo.com)       │
│  - OpenStreetMap Geocoding & Tiles                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Directory Structure

```
odeyssey/
├── app.py                     # Main Flask application and REST API endpoints
├── conftest.py                # Pytest configuration and sys.path setup
├── requirements.txt           # Python package dependencies
├── .env                       # Local environment variables
├── .env.example               # Template for environment configuration
├── .gitignore                 # Version control ignore rules
├── run.bat / run.ps1          # One-click startup scripts
├── test.bat / test.ps1        # One-click test runner scripts
├── data/
│   └── destinations.json      # Curated dataset of Indian destinations & activities
├── services/
│   ├── __init__.py
│   ├── planner.py             # Rule-based itinerary & budget estimation engine
│   └── weather.py             # Open-Meteo weather client with caching & fallback
├── static/
│   ├── css/
│   │   └── style.css          # Minimalist design system and responsive styles
│   └── js/
│       └── app.js             # Client controller, maps, budget, and storage
├── templates/
│   ├── base.html              # Base HTML layout with navigation & footer
│   ├── index.html             # Landing page with hero & curated cards
│   ├── planner.html           # Interactive itinerary planner interface
│   ├── my_trips.html          # Saved trips drawer & localStorage manager
│   ├── about.html             # Project documentation, architecture & viva notes
│   ├── 404.html               # Semantic 404 error page
│   └── 500.html               # Semantic 500 error page
└── tests/
    ├── test_api.py            # Integration tests for REST endpoints and routes
    └── test_planner.py        # Unit tests for scoring, budgeting & validation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (Python 3.14.6 is configured in `.venv`)
- **Git** (version 2.55+ detected)

*(No external Node.js build step is required for the existing production-ready stack! All UI assets are natively served with zero bundle overhead.)*

### Running the Application

You can start the development server using either of these methods:

**Method 1 (One-Click Script):**
- Double-click `run.bat`, OR
- In PowerShell:
  ```powershell
  .\run.ps1
  ```

**Method 2 (Command Line):**
```powershell
# Using the local virtual environment
.\.venv\Scripts\python.exe app.py
```

The website will be live at:
👉 **http://127.0.0.1:5000**

---

## 🧪 Running Automated Tests

ODEYSSEY includes 14 comprehensive unit and integration tests covering API endpoints, input validation, interest ranking, and weather fallbacks.

Run the tests using either:

**Method 1 (One-Click Script):**
- Double-click `test.bat`, OR
- In PowerShell:
  ```powershell
  .\test.ps1
  ```

**Method 2 (Command Line):**
```powershell
.\.venv\Scripts\pytest.exe -v
```

Expected output:
```
tests/test_api.py::test_health_endpoint PASSED
tests/test_api.py::test_destinations_endpoint PASSED
tests/test_api.py::test_plan_endpoint_valid PASSED
tests/test_api.py::test_plan_endpoint_invalid_json PASSED
tests/test_api.py::test_plan_endpoint_validation_failure PASSED
tests/test_api.py::test_weather_endpoint_by_destination PASSED
tests/test_api.py::test_page_routes PASSED
tests/test_planner.py::test_load_destinations PASSED
tests/test_planner.py::test_validation_missing_fields PASSED
tests/test_planner.py::test_validation_invalid_duration_and_budget PASSED
tests/test_planner.py::test_valid_trip_planning_jaipur PASSED
tests/test_planner.py::test_different_interests_produce_different_rankings PASSED
tests/test_planner.py::test_custom_destination_fallback PASSED
tests/test_planner.py::test_weather_fallback PASSED
============================== 14 passed in 3.34s ==============================
```

---

## 🌐 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Service status, engine version, and storage mode |
| `/api/destinations` | `GET` | List of curated destinations with metadata & coordinates |
| `/api/plan` | `POST` | Validates preferences, generates day schedule, computes budget & weather |
| `/api/weather` | `GET` | Real-time weather by `(lat, lon)` or `?destination=` query |

### Sample `/api/plan` Request Payload:

```json
{
  "destination": "Jaipur",
  "start_date": "2026-11-10",
  "days": 3,
  "travelers": 2,
  "budget": 25000,
  "travel_style": "balanced",
  "interests": ["history", "food", "culture"]
}
```

---

## 🔑 External APIs & Credentials

- **Weather (Open-Meteo):** Free, CC BY 4.0 licensed, requires **no API keys** or accounts.
- **Maps (OpenStreetMap & Leaflet):** Free, open-source cartography, requires **no API keys**.
- **No external paid API keys or secret credentials are required to run this project.** All features are fully functional out of the box.

---

## 🎓 College Viva / Project Presentation Q&A

1. **Why rule-based planning instead of a generative AI API?**  
   Generative AI (e.g. LLMs) frequently hallucinate non-existent attractions, closed venues, and wildly incorrect costs. A rule-based expert system guarantees factual accuracy, deterministic repeatability, sub-second generation times, zero operational API costs, and full privacy.

2. **How is the budget calculated?**  
   Costs are computed from verified regional baselines in `destinations.json`:
   $$\text{Total} = (\text{Daily Room Rate} \times \text{Rooms} \times \text{Nights}) + (\text{Food/Day} \times \text{Travelers} \times \text{Days}) + \sum \text{Entry Fees} + \text{Transit} + 5\% \text{ Contingency}$$

3. **Where are trips saved?**  
   Trips are saved in browser `localStorage`. This allows instant offline availability, zero user friction (no login/password required), and complete data ownership by the user.

---

## 📄 License

Developed for educational demonstration as a college mini-project.
OpenStreetMap &copy; OpenStreetMap contributors. Weather by Open-Meteo.com.
