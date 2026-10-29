/**
 * static/js/app.js
 * ODEYSSEY — Minimalist Smart Trip Planner
 * Client-side controller for form validation, dynamic itinerary generation,
 * budget live recalculation, Open-Meteo weather display, Leaflet maps, and localStorage persistence.
 */

(function () {
  "use strict";

  // Global state for active itinerary
  let currentTripPlan = null;
  let activeMapInstance = null;

  // Key for browser localStorage
  const STORAGE_KEY = "odeyssey_saved_trips";

  // =========================================================================
  // DOM READY INITIALIZATION
  // =========================================================================
  document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initPlannerForm();
    initPresets();
    initMyTripsPage();
    updateSavedTripsCount();
  });

  // =========================================================================
  // 1. NAVIGATION & GENERAL UI
  // =========================================================================
  function initNavigation() {
    const mobileBtn = document.getElementById("mobileMenuBtn");
    const siteNav = document.getElementById("siteNav");

    if (mobileBtn && siteNav) {
      mobileBtn.addEventListener("click", () => {
        siteNav.classList.toggle("open");
      });
    }
  }

  function updateSavedTripsCount() {
    const badge = document.getElementById("savedCountBadge");
    if (!badge) return;
    const trips = getSavedTrips();
    if (trips.length > 0) {
      badge.textContent = trips.length;
      badge.style.display = "inline-block";
    } else {
      badge.style.display = "none";
    }
  }

  function showToast(message) {
    const existing = document.querySelector(".toast-notice");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "toast-notice";
    toast.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <span>${escapeHtml(message)}</span>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatInr(val) {
    const num = Math.round(Number(val) || 0);
    return "₹" + num.toLocaleString("en-IN");
  }

  // =========================================================================
  // 2. FORM & PRESET CONTROLS
  // =========================================================================
  function initPresets() {
    // Days Counter (+ / -)
    const daysInput = document.getElementById("days");
    const daysDec = document.getElementById("daysDec");
    const daysInc = document.getElementById("daysInc");

    if (daysInput && daysDec && daysInc) {
      daysDec.addEventListener("click", () => {
        let val = parseInt(daysInput.value, 10) || 1;
        if (val > 1) {
          daysInput.value = val - 1;
          syncPresetActive("days", daysInput.value);
        }
      });
      daysInc.addEventListener("click", () => {
        let val = parseInt(daysInput.value, 10) || 1;
        if (val < 14) {
          daysInput.value = val + 1;
          syncPresetActive("days", daysInput.value);
        }
      });
      daysInput.addEventListener("input", () => {
        syncPresetActive("days", daysInput.value);
      });
    }

    // Travelers Counter (+ / -)
    const travelersInput = document.getElementById("travelers");
    const travelersDec = document.getElementById("travelersDec");
    const travelersInc = document.getElementById("travelersInc");

    if (travelersInput && travelersDec && travelersInc) {
      travelersDec.addEventListener("click", () => {
        let val = parseInt(travelersInput.value, 10) || 1;
        if (val > 1) travelersInput.value = val - 1;
      });
      travelersInc.addEventListener("click", () => {
        let val = parseInt(travelersInput.value, 10) || 1;
        if (val < 20) travelersInput.value = val + 1;
      });
    }

    // Preset pills click handler
    document.querySelectorAll(".preset-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        const target = pill.getAttribute("data-target");
        const val = pill.getAttribute("data-val");
        const input = document.getElementById(target);
        if (input) {
          input.value = val;
          syncPresetActive(target, val);
        }
      });
    });

    // Style card selection styling sync
    document.querySelectorAll(".style-card input").forEach((radio) => {
      radio.addEventListener("change", () => {
        document.querySelectorAll(".style-card").forEach((c) => c.classList.remove("active"));
        if (radio.checked) {
          radio.closest(".style-card").classList.add("active");
        }
      });
    });

    // Interests pills toggle sync
    document.querySelectorAll(".interest-pill input").forEach((chk) => {
      chk.addEventListener("change", () => {
        const parent = chk.closest(".interest-pill");
        if (chk.checked) {
          parent.classList.add("active");
        } else {
          parent.classList.remove("active");
        }
      });
    });

    // Advanced options accordion toggle
    const advToggle = document.getElementById("toggleAdvancedBtn");
    const advContent = document.getElementById("advancedContent");
    if (advToggle && advContent) {
      advToggle.addEventListener("click", () => {
        const isHidden = advContent.style.display === "none";
        advContent.style.display = isHidden ? "block" : "none";
        advToggle.classList.toggle("open", isHidden);
      });
    }

    // Reset Form button
    const resetBtn = document.getElementById("resetFormBtn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        const form = document.getElementById("tripPlannerForm");
        if (form) {
          form.reset();
          document.getElementById("destination").value = "Jaipur";
          document.getElementById("days").value = "3";
          document.getElementById("travelers").value = "2";
          document.getElementById("budget").value = "25000";
          syncPresetActive("days", "3");
          syncPresetActive("budget", "25000");
          clearValidationErrors();
        }
      });
    }
  }

  function syncPresetActive(targetField, value) {
    document
      .querySelectorAll(`.preset-pill[data-target="${targetField}"]`)
      .forEach((pill) => {
        if (pill.getAttribute("data-val") === String(value)) {
          pill.classList.add("active");
        } else {
          pill.classList.remove("active");
        }
      });
  }

  // =========================================================================
  // 3. PLANNER FORM SUBMISSION & VALIDATION
  // =========================================================================
  function initPlannerForm() {
    const form = document.getElementById("tripPlannerForm");
    if (!form) return;

    // Check if URL has query parameters from Landing page
    const params = new URLSearchParams(window.location.search);
    if (params.has("destination")) {
      const destInput = document.getElementById("destination");
      if (destInput) destInput.value = params.get("destination");
    }
    if (params.has("days")) {
      const daysInput = document.getElementById("days");
      if (daysInput) {
        daysInput.value = params.get("days");
        syncPresetActive("days", params.get("days"));
      }
    }
    if (params.has("travel_style")) {
      const styleVal = params.get("travel_style");
      const styleRadio = document.querySelector(`input[name="travel_style"][value="${styleVal}"]`);
      if (styleRadio) {
        styleRadio.checked = true;
        document.querySelectorAll(".style-card").forEach((c) => c.classList.remove("active"));
        styleRadio.closest(".style-card").classList.add("active");
      }
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearValidationErrors();

      const payload = collectFormData();
      const clientErrors = validateClient(payload);

      if (Object.keys(clientErrors).length > 0) {
        renderFieldErrors(clientErrors);
        return;
      }

      await submitPlanRequest(payload);
    });
  }

  function collectFormData() {
    const destination = (document.getElementById("destination")?.value || "").trim();
    const startDate = document.getElementById("startDate")?.value || "";
    const days = parseInt(document.getElementById("days")?.value, 10) || 3;
    const travelers = parseInt(document.getElementById("travelers")?.value, 10) || 1;
    const budget = parseFloat(document.getElementById("budget")?.value) || 0;

    const styleEl = document.querySelector('input[name="travel_style"]:checked');
    const travelStyle = styleEl ? styleEl.value : "balanced";

    const interests = [];
    document.querySelectorAll('input[name="interests"]:checked').forEach((chk) => {
      interests.push(chk.value);
    });

    const accommodationPref = document.getElementById("accommodationPref")?.value || "";
    const transportPref = document.getElementById("transportPref")?.value || "";
    const seed = parseInt(document.getElementById("planSeed")?.value, 10) || 0;

    return {
      destination,
      start_date: startDate,
      days,
      travelers,
      budget,
      travel_style: travelStyle,
      interests,
      accommodation_pref: accommodationPref,
      transport_pref: transportPref,
      seed,
    };
  }

  function validateClient(data) {
    const errors = {};
    if (!data.destination) {
      errors["destination"] = "Please enter a destination city or region.";
    } else if (data.destination.length < 2) {
      errors["destination"] = "Destination name must be at least 2 characters.";
    }

    if (!data.start_date) {
      errors["start_date"] = "Please select a start date.";
    }

    if (!data.days || data.days < 1 || data.days > 14) {
      errors["days"] = "Duration must be between 1 and 14 days.";
    }

    if (!data.travelers || data.travelers < 1 || data.travelers > 20) {
      errors["travelers"] = "Travelers must be between 1 and 20.";
    }

    if (!data.budget || data.budget <= 0) {
      errors["budget"] = "Please enter a valid total budget.";
    } else if (data.budget < 1000) {
      errors["budget"] = "Budget should be at least ₹1,000 for realistic planning.";
    }

    return errors;
  }

  function renderFieldErrors(errors) {
    for (const [field, msg] of Object.entries(errors)) {
      const errEl = document.getElementById(`error-${field}`);
      if (errEl) {
        errEl.textContent = msg;
        errEl.classList.add("active");
      }
    }
  }

  function clearValidationErrors() {
    document.querySelectorAll(".field-error").forEach((el) => {
      el.textContent = "";
      el.classList.remove("active");
    });
  }

  async function submitPlanRequest(payload) {
    const btn = document.getElementById("generatePlanBtn");
    const emptyCard = document.getElementById("emptyStateCard");
    const loadingCard = document.getElementById("loadingStateCard");
    const itineraryView = document.getElementById("itineraryView");

    // UI Loading state
    if (btn) {
      btn.disabled = true;
      btn.querySelector(".btn-text").textContent = "Planning Trip...";
      btn.querySelector(".btn-spinner").style.display = "inline-block";
    }

    if (emptyCard) emptyCard.style.display = "none";
    if (itineraryView) itineraryView.style.display = "none";
    if (loadingCard) loadingCard.style.display = "block";

    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        currentTripPlan = result;
        renderItinerary(result);
        if (loadingCard) loadingCard.style.display = "none";
        if (itineraryView) {
          itineraryView.style.display = "block";
          itineraryView.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      } else {
        if (loadingCard) loadingCard.style.display = "none";
        if (emptyCard) emptyCard.style.display = "block";

        if (result.field_errors) {
          renderFieldErrors(result.field_errors);
        } else {
          alert("Error generating trip: " + (result.error || "Please try again."));
        }
      }
    } catch (err) {
      console.error("Fetch plan error:", err);
      if (loadingCard) loadingCard.style.display = "none";
      if (emptyCard) emptyCard.style.display = "block";
      alert("Failed to communicate with planning engine. Please check your connection.");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.querySelector(".btn-text").textContent = "Generate Itinerary";
        btn.querySelector(".btn-spinner").style.display = "none";
      }
    }
  }

  // =========================================================================
  // 4. ITINERARY RENDERING ENGINE
  // =========================================================================
  function renderItinerary(data) {
    const container = document.getElementById("itineraryView");
    if (!container) return;

    const dest = data.destination;
    const params = data.trip_params;
    const days = data.days;
    const budget = data.budget_breakdown;
    const weather = data.weather;

    // Build Weather HTML
    let weatherHtml = "";
    if (weather && weather.available && weather.forecast && weather.forecast.length > 0) {
      const forecastCols = weather.forecast
        .map(
          (f) => `
        <div class="weather-day-col">
          <div class="weather-date-label">Day ${f.day_index}</div>
          <div class="weather-icon-temp">${f.icon} ${Math.round(f.max_temp_c)}°C</div>
          <div class="weather-condition">${escapeHtml(f.condition)}</div>
          <div class="weather-precip">🌧️ ${f.precipitation_probability}%</div>
        </div>
      `
        )
        .join("");

      weatherHtml = `
        <div class="weather-widget">
          <div class="weather-header">
            <span class="weather-title">
              <span>Forecast</span> &bull; ${escapeHtml(dest.name)}
            </span>
            <span class="weather-attribution">via Open-Meteo API</span>
          </div>
          <div class="weather-grid">
            ${forecastCols}
          </div>
        </div>
      `;
    } else if (weather && !weather.available) {
      weatherHtml = `
        <div class="weather-widget">
          <div class="weather-header">
            <span class="weather-title">Weather Forecast</span>
            <span class="weather-attribution">Seasonal Averages</span>
          </div>
          <p class="field-help" style="margin:0;">
            ${escapeHtml(weather.note || "Live forecast unavailable. Best visit season: " + (dest.best_seasons || []).join(", "))}
          </p>
        </div>
      `;
    }

    // Build Days HTML
    const daysHtml = days
      .map((day) => {
        const activitiesHtml = day.activities
          .map((act) => {
            const costLabel = act.cost_inr > 0 ? formatInr(act.cost_inr) + " entry" : "Free entry";
            const tags = (act.interests || [])
              .map((t) => `<span class="act-interest-tag">${escapeHtml(t)}</span>`)
              .join("");

            return `
            <div class="activity-slot-item" id="act-item-${act.id}" data-cost="${act.cost_inr}">
              <div class="slot-top-row">
                <div class="slot-badge-group">
                  <span class="slot-tag ${act.time_slot}">${escapeHtml(act.time_slot)}</span>
                  <span class="activity-cost-badge">${costLabel}</span>
                </div>
                <button type="button" class="act-remove-btn" title="Remove activity" onclick="ODEYSSEY.removeActivity('${act.id}')">
                  ✕ Remove
                </button>
              </div>

              <div class="activity-name">${escapeHtml(act.name)}</div>
              <p class="activity-desc">${escapeHtml(act.short_desc || "")}</p>

              ${
                act.tips
                  ? `<div class="activity-tip-box"><strong>Local Tip:</strong> ${escapeHtml(act.tips)}</div>`
                  : ""
              }

              <div class="activity-bottom-bar">
                <div class="activity-tags-row">
                  ${tags}
                  <span class="act-interest-tag">⏳ ${act.duration_hours || 2}h</span>
                </div>
                <div class="act-links-row">
                  <a href="${act.map_url}" target="_blank" rel="noopener" class="act-map-link">
                    📍 Map / Directions &rarr;
                  </a>
                </div>
              </div>
            </div>
          `;
          })
          .join("");

        return `
        <div class="day-card" id="day-card-${day.day_number}">
          <div class="day-card-header">
            <div class="day-title-left">
              <span class="day-number-tag">Day ${day.day_number}</span>
              <span class="day-date-string">${escapeHtml(day.day_formatted || day.date)}</span>
            </div>
            <span class="day-theme-pill">${escapeHtml(day.theme)}</span>
          </div>

          <div class="day-activities-list">
            ${activitiesHtml}
          </div>
        </div>
      `;
      })
      .join("");

    // Build Budget Breakdown HTML
    const cats = budget.categories;
    const isWithin = budget.status === "within_budget";
    const statusClass = isWithin ? "status-within" : "status-exceeds";
    const alertClass = isWithin ? "alert-within" : "alert-exceeds";
    const statusText = isWithin ? "Within Budget" : "Exceeds Budget";

    const suggestionsHtml =
      budget.suggestions && budget.suggestions.length > 0
        ? `<ul class="budget-suggestions">${budget.suggestions
            .map((s) => `<li>${escapeHtml(s)}</li>`)
            .join("")}</ul>`
        : "";

    const categoriesTableRows = Object.entries(cats)
      .map(([key, cat]) => {
        return `
        <tr data-cat-key="${key}">
          <td class="cat-label-cell">${escapeHtml(cat.label)}</td>
          <td class="cat-basis-cell">${escapeHtml(cat.basis)}</td>
          <td class="cat-amount-cell">
            <span class="cat-display-amt" id="cat-amt-${key}">${formatInr(cat.amount)}</span>
            <input 
              type="number" 
              class="cat-adjust-input" 
              id="cat-input-${key}" 
              value="${cat.amount}" 
              style="display:none;" 
              oninput="ODEYSSEY.recalculateBudget()"
            >
          </td>
        </tr>
      `;
      })
      .join("");

    // Complete Container Output
    container.innerHTML = `
      <div class="itinerary-container">
        <!-- Hero Summary Card -->
        <div class="trip-hero-card">
          <div class="trip-hero-top">
            <div class="trip-title-group">
              <span class="trip-dest-state">${escapeHtml(dest.state)}</span>
              <h2 class="trip-dest-name">${escapeHtml(dest.name)}</h2>
            </div>
            <div class="trip-meta-badges">
              <span class="meta-badge badge-accent">${params.days} Days</span>
              <span class="meta-badge">${params.travelers} Traveler${params.travelers > 1 ? "s" : ""}</span>
              <span class="meta-badge">${escapeHtml(params.travel_style.toUpperCase())}</span>
              <span class="meta-badge">From ${escapeHtml(params.start_date)}</span>
            </div>
          </div>

          <p class="trip-overview-text">${escapeHtml(dest.overview)}</p>

          ${weatherHtml}

          <!-- Toolbar Actions -->
          <div class="trip-actions-bar">
            <button type="button" class="btn btn-primary btn-sm" id="saveTripBtn" onclick="ODEYSSEY.saveCurrentTrip()">
              💾 Save to My Trips
            </button>
            <button type="button" class="btn btn-secondary btn-sm" onclick="ODEYSSEY.regeneratePlan()">
              🔄 Regenerate Plan
            </button>
            <button type="button" class="btn btn-outline btn-sm" onclick="window.print()">
              🖨️ Print / Save PDF
            </button>
            <button type="button" class="btn btn-outline btn-sm" onclick="ODEYSSEY.exportPlanText()">
              📄 Export Text
            </button>
            <button type="button" class="btn btn-outline btn-sm" onclick="ODEYSSEY.toggleBudgetAdjustment()">
              ✏️ Adjust Cost Table
            </button>
          </div>
        </div>

        <!-- Day-by-Day Section -->
        <div class="days-section">
          <div class="section-header" style="margin-bottom: 16px;">
            <h3 class="section-title" style="font-size: 1.4rem;">Day-by-Day Itinerary</h3>
            <p class="section-subtitle">Morning, Afternoon, and Evening activities curated for sensible pacing.</p>
          </div>
          <div class="days-container">
            ${daysHtml}
          </div>
        </div>

        <!-- Budget Breakdown Module -->
        <div class="budget-card">
          <div class="budget-card-header">
            <h3 class="budget-card-title">INR Expense Breakdown</h3>
            <p class="budget-card-subtitle">
              Calculated from authentic baseline assumptions for ${params.travelers} traveler(s) over ${params.days} day(s).
            </p>
          </div>

          <div class="budget-summary-banner">
            <div class="budget-summary-item">
              <span class="bs-label">Your Set Budget</span>
              <span class="bs-amount" id="budgetDisplayTarget">${formatInr(budget.user_budget)}</span>
            </div>

            <div class="budget-summary-item">
              <span class="bs-label">Total Estimated Cost</span>
              <span class="bs-amount" id="budgetDisplayTotal">${formatInr(budget.total_estimated_cost)}</span>
            </div>

            <div class="budget-summary-item">
              <span class="bs-label">Remaining Balance</span>
              <span class="bs-amount" id="budgetDisplayBalance">${formatInr(budget.remaining_budget)}</span>
              <span class="bs-status-badge ${statusClass}" id="budgetStatusBadge">${statusText}</span>
            </div>
          </div>

          <div class="budget-health-alert ${alertClass}" id="budgetHealthAlert">
            <div id="budgetHealthMsg">${escapeHtml(budget.message)}</div>
            ${suggestionsHtml}
          </div>

          <table class="budget-categories-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Calculation Basis</th>
                <th style="text-align: right;">Amount (INR)</th>
              </tr>
            </thead>
            <tbody id="budgetCategoriesTbody">
              ${categoriesTableRows}
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total Calculated Estimate</td>
                <td style="text-align: right;" id="budgetTableFooterTotal">${formatInr(budget.total_estimated_cost)}</td>
              </tr>
            </tfoot>
          </table>

          <div class="budget-disclaimer">
            <strong>Price Disclaimer:</strong> Estimates reflect realistic tourist averages in India for the selected style.
            They are not verified live supplier booking rates. Actual costs may vary slightly based on seasonal surge and personal choices.
          </div>
        </div>

        <!-- Interactive Map Container -->
        <div class="map-card" id="mapCardContainer">
          <div class="map-card-header">
            <h3 class="map-card-title">Destination Route Map</h3>
            <span class="field-help">OpenStreetMap + Leaflet</span>
          </div>
          <div class="map-view-box" id="leafletMap">
            <div class="map-fallback-box" id="mapFallbackBox" style="display:none;">
              <p>Map view is unavailable or offline.</p>
              <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(dest.name)}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">
                Open ${escapeHtml(dest.name)} on Google Maps &rarr;
              </a>
            </div>
          </div>
        </div>
      </div>
    `;

    // Initialize Map with markers
    renderLeafletMap(dest, days);
  }

  // =========================================================================
  // 5. LEAFLET MAP INTEGRATION
  // =========================================================================
  function renderLeafletMap(destination, days) {
    const mapEl = document.getElementById("leafletMap");
    const fallbackBox = document.getElementById("mapFallbackBox");
    if (!mapEl) return;

    if (typeof L === "undefined") {
      // Leaflet library not loaded or offline
      if (fallbackBox) fallbackBox.style.display = "flex";
      return;
    }

    // Clean up previous map if exists
    if (activeMapInstance) {
      activeMapInstance.remove();
      activeMapInstance = null;
    }

    const coords = destination.coordinates;
    if (!coords || !coords.lat || !coords.lon) {
      if (fallbackBox) fallbackBox.style.display = "flex";
      return;
    }

    try {
      activeMapInstance = L.map("leafletMap").setView([coords.lat, coords.lon], 12);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(activeMapInstance);

      // Collect all activities with coordinates
      const markers = [];
      days.forEach((day) => {
        day.activities.forEach((act) => {
          if (act.coordinates && act.coordinates.lat && act.coordinates.lon) {
            const marker = L.marker([act.coordinates.lat, act.coordinates.lon]).addTo(activeMapInstance);
            marker.bindPopup(`
              <div style="font-family:sans-serif; min-width:160px;">
                <div style="font-size:11px; text-transform:uppercase; color:#87947A; font-weight:700;">Day ${day.day_number} &bull; ${act.time_slot}</div>
                <div style="font-weight:600; font-size:13px; margin:3px 0;">${escapeHtml(act.name)}</div>
                <div style="font-size:11px; color:#555;">${escapeHtml(act.short_desc || "")}</div>
                <a href="${act.map_url}" target="_blank" style="font-size:11px; color:#87947A; display:inline-block; margin-top:4px;">Directions &rarr;</a>
              </div>
            `);
            markers.push(marker);
          }
        });
      });

      if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        activeMapInstance.fitBounds(group.getBounds().pad(0.15));
      }
    } catch (e) {
      console.warn("Leaflet map initialization skipped:", e);
      if (fallbackBox) fallbackBox.style.display = "flex";
    }
  }

  // =========================================================================
  // 6. DYNAMIC ACTIVITY REMOVAL & BUDGET RECALCULATION
  // =========================================================================
  function removeActivity(activityId) {
    if (!currentTripPlan) return;

    let removedCost = 0;
    let activityFound = false;

    // Search and remove from memory model
    currentTripPlan.days.forEach((day) => {
      const idx = day.activities.findIndex((a) => a.id === activityId);
      if (idx !== -1) {
        removedCost = day.activities[idx].cost_inr || 0;
        day.activities.splice(idx, 1);
        activityFound = true;
      }
    });

    if (!activityFound) return;

    // Remove DOM element
    const domEl = document.getElementById(`act-item-${activityId}`);
    if (domEl) {
      domEl.style.transition = "all 0.25s ease";
      domEl.style.opacity = "0";
      domEl.style.transform = "scale(0.96)";
      setTimeout(() => domEl.remove(), 250);
    }

    // Recalculate activities ticket entry in budget
    const travelers = currentTripPlan.trip_params.travelers || 1;
    let remainingEntryTotal = 0;
    currentTripPlan.days.forEach((day) => {
      day.activities.forEach((a) => {
        remainingEntryTotal += (a.cost_inr || 0) * travelers;
      });
    });

    // Update categories
    const cats = currentTripPlan.budget_breakdown.categories;
    if (cats.activities_entry) {
      cats.activities_entry.amount = remainingEntryTotal;
      const input = document.getElementById("cat-input-activities_entry");
      if (input) input.value = remainingEntryTotal;
      const display = document.getElementById("cat-amt-activities_entry");
      if (display) display.textContent = formatInr(remainingEntryTotal);
    }

    recalculateBudget();
    showToast("Activity removed. Budget updated.");
  }

  function toggleBudgetAdjustment() {
    const isEditing = document.querySelector(".cat-adjust-input")?.style.display !== "none";
    document.querySelectorAll(".cat-adjust-input").forEach((inp) => {
      inp.style.display = isEditing ? "none" : "inline-block";
    });
    document.querySelectorAll(".cat-display-amt").forEach((span) => {
      span.style.display = isEditing ? "inline-block" : "none";
    });

    if (!isEditing) {
      showToast("Cost table unlocked. You can now tweak individual category amounts.");
    }
  }

  function recalculateBudget() {
    if (!currentTripPlan) return;

    const cats = currentTripPlan.budget_breakdown.categories;
    let newSubtotal = 0;

    for (const key of Object.keys(cats)) {
      const input = document.getElementById(`cat-input-${key}`);
      let val = cats[key].amount;
      if (input && input.value !== "") {
        val = parseFloat(input.value) || 0;
        cats[key].amount = val;
      }
      newSubtotal += val;
      const display = document.getElementById(`cat-amt-${key}`);
      if (display) display.textContent = formatInr(val);
    }

    const userBudget = currentTripPlan.budget_breakdown.user_budget;
    const remaining = userBudget - newSubtotal;

    currentTripPlan.budget_breakdown.total_estimated_cost = newSubtotal;
    currentTripPlan.budget_breakdown.remaining_budget = remaining;

    // Update DOM summary
    const totalEl = document.getElementById("budgetDisplayTotal");
    const balEl = document.getElementById("budgetDisplayBalance");
    const badgeEl = document.getElementById("budgetStatusBadge");
    const footerTotalEl = document.getElementById("budgetTableFooterTotal");
    const healthAlert = document.getElementById("budgetHealthAlert");
    const healthMsg = document.getElementById("budgetHealthMsg");

    if (totalEl) totalEl.textContent = formatInr(newSubtotal);
    if (footerTotalEl) footerTotalEl.textContent = formatInr(newSubtotal);
    if (balEl) balEl.textContent = formatInr(remaining);

    const isWithin = remaining >= 0;
    if (badgeEl) {
      badgeEl.className = `bs-status-badge ${isWithin ? "status-within" : "status-exceeds"}`;
      badgeEl.textContent = isWithin ? "Within Budget" : "Exceeds Budget";
    }

    if (healthAlert && healthMsg) {
      healthAlert.className = `budget-health-alert ${isWithin ? "alert-within" : "alert-exceeds"}`;
      healthMsg.textContent = isWithin
        ? `Adjusted total is within your budget with a remaining buffer of ${formatInr(remaining)}.`
        : `Adjusted total exceeds your set budget by ${formatInr(Math.abs(remaining))}.`;
    }
  }

  // =========================================================================
  // 7. REGENERATION & EXPORT
  // =========================================================================
  function regeneratePlan() {
    const seedInput = document.getElementById("planSeed");
    if (seedInput) {
      seedInput.value = parseInt(seedInput.value, 10) + 1;
    }
    const form = document.getElementById("tripPlannerForm");
    if (form) {
      form.dispatchEvent(new Event("submit"));
    }
  }

  function exportPlanText() {
    if (!currentTripPlan) return;
    const dest = currentTripPlan.destination.name;
    const params = currentTripPlan.trip_params;
    const budget = currentTripPlan.budget_breakdown;

    let text = `=====================================================\n`;
    text += `ODEYSSEY TRIP PLAN: ${dest.toUpperCase()}\n`;
    text += `Duration: ${params.days} Days | Travelers: ${params.travelers} | Style: ${params.travel_style}\n`;
    text += `Dates: Starting ${params.start_date}\n`;
    text += `=====================================================\n\n`;

    currentTripPlan.days.forEach((d) => {
      text += `DAY ${d.day_number}: ${d.day_formatted} (${d.theme})\n`;
      text += `-----------------------------------------------------\n`;
      d.activities.forEach((a) => {
        text += `• [${a.time_slot.toUpperCase()}] ${a.name} (${a.duration_hours}h, Est. Cost: ₹${a.cost_inr})\n`;
        text += `  Reason: ${a.short_desc}\n`;
        if (a.tips) text += `  Tip: ${a.tips}\n`;
      });
      text += `\n`;
    });

    text += `BUDGET SUMMARY (INR)\n`;
    text += `-----------------------------------------------------\n`;
    text += `User Budget: ${formatInr(budget.user_budget)}\n`;
    text += `Estimated Total: ${formatInr(budget.total_estimated_cost)}\n`;
    text += `Balance: ${formatInr(budget.remaining_budget)} (${budget.status})\n\n`;
    text += `Exported from ODEYSSEY — Less planning. More exploring.\n`;

    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ODEYSSEY-${dest.replace(/\s+/g, "_")}-Plan.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast("Itinerary exported as text file.");
  }

  // =========================================================================
  // 8. BROWSER LOCAL STORAGE (MY TRIPS)
  // =========================================================================
  function getSavedTrips() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn("Unable to access localStorage:", e);
      return [];
    }
  }

  function saveCurrentTrip() {
    if (!currentTripPlan) return;

    const trips = getSavedTrips();
    const tripToSave = {
      id: "trip_" + Date.now(),
      saved_at: new Date().toISOString(),
      plan: currentTripPlan,
    };

    // Avoid duplicate immediate saves of the exact same destination & date
    const exists = trips.some(
      (t) =>
        t.plan.destination.name === currentTripPlan.destination.name &&
        t.plan.trip_params.start_date === currentTripPlan.trip_params.start_date &&
        t.plan.trip_params.days === currentTripPlan.trip_params.days
    );

    if (exists) {
      showToast("This trip is already saved in My Trips.");
      return;
    }

    trips.unshift(tripToSave);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
    updateSavedTripsCount();
    showToast("Trip saved successfully to My Trips (Local Storage).");

    const saveBtn = document.getElementById("saveTripBtn");
    if (saveBtn) {
      saveBtn.textContent = "✓ Saved in My Trips";
      saveBtn.classList.remove("btn-primary");
      saveBtn.classList.add("btn-outline");
    }
  }

  function deleteSavedTrip(tripId) {
    let trips = getSavedTrips();
    trips = trips.filter((t) => t.id !== tripId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
    updateSavedTripsCount();
    initMyTripsPage();
    showToast("Trip removed from local storage.");
  }

  function clearAllSavedTrips() {
    if (confirm("Are you sure you want to remove all saved trips from this device?")) {
      localStorage.removeItem(STORAGE_KEY);
      updateSavedTripsCount();
      initMyTripsPage();
      showToast("All saved trips have been cleared.");
    }
  }

  function initMyTripsPage() {
    const grid = document.getElementById("savedTripsGrid");
    const emptyState = document.getElementById("emptyTripsState");
    const clearBtn = document.getElementById("clearAllTripsBtn");
    if (!grid) return;

    const trips = getSavedTrips();

    if (trips.length === 0) {
      if (emptyState) emptyState.style.display = "block";
      if (clearBtn) clearBtn.style.display = "none";
      grid.innerHTML = "";
      return;
    }

    if (emptyState) emptyState.style.display = "none";
    if (clearBtn) {
      clearBtn.style.display = "inline-block";
      clearBtn.onclick = clearAllSavedTrips;
    }

    grid.innerHTML = trips
      .map((item) => {
        const p = item.plan;
        const dest = p.destination;
        const params = p.trip_params;
        const budget = p.budget_breakdown;
        const savedDate = new Date(item.saved_at).toLocaleDateString("en-IN", {
          day: "numeric",
          month: "short",
          year: "numeric",
        });

        return `
        <article class="saved-trip-card">
          <div class="st-header">
            <div>
              <span class="card-state">${escapeHtml(dest.state)}</span>
              <h3 class="st-dest">${escapeHtml(dest.name)}</h3>
            </div>
            <span class="st-date-badge">Saved ${savedDate}</span>
          </div>

          <div class="st-params-row">
            <span class="meta-badge">${params.days} Days</span>
            <span class="meta-badge">${params.travelers} Traveler${params.travelers > 1 ? "s" : ""}</span>
            <span class="meta-badge">${escapeHtml(params.travel_style.toUpperCase())}</span>
          </div>

          <div class="st-cost-summary">
            <div>
              <div class="st-cost-label">Est. Total Cost</div>
              <div class="st-cost-val">${formatInr(budget.total_estimated_cost)}</div>
            </div>
            <div style="text-align: right;">
              <div class="st-cost-label">Target Budget</div>
              <div style="font-weight:600; font-size:0.95rem;">${formatInr(budget.user_budget)}</div>
            </div>
          </div>

          <div class="st-actions">
            <button type="button" class="btn btn-primary btn-sm btn-block" onclick="ODEYSSEY.openTripModal('${item.id}')">
              View Itinerary
            </button>
            <button type="button" class="btn btn-outline btn-sm" title="Delete" onclick="ODEYSSEY.deleteSavedTrip('${item.id}')">
              ✕
            </button>
          </div>
        </article>
      `;
      })
      .join("");
  }

  function openTripModal(tripId) {
    const trips = getSavedTrips();
    const item = trips.find((t) => t.id === tripId);
    if (!item) return;

    const modal = document.getElementById("tripModalBackdrop");
    const content = document.getElementById("modalTripContent");
    const title = document.getElementById("modalTripTitle");
    const closeBtn = document.getElementById("closeTripModalBtn");
    const exportBtn = document.getElementById("modalExportBtn");
    const printBtn = document.getElementById("modalPrintBtn");
    const loadBtn = document.getElementById("modalLoadInPlannerBtn");

    if (!modal || !content) return;

    const plan = item.plan;
    title.textContent = `${plan.destination.name} (${plan.trip_params.days} Days)`;

    let daysHtml = plan.days
      .map(
        (d) => `
      <div style="margin-bottom:16px; border-bottom:1px solid #DFDACF; padding-bottom:10px;">
        <h4 style="font-size:0.95rem; font-weight:700; color:#87947A; margin-bottom:6px;">Day ${d.day_number}: ${d.day_formatted} (${d.theme})</h4>
        <ul style="padding-left:18px; font-size:0.875rem; color:#242620; line-height:1.5;">
          ${d.activities
            .map(
              (a) => `
            <li>
              <strong>[${a.time_slot.toUpperCase()}] ${escapeHtml(a.name)}</strong> 
              (${a.cost_inr > 0 ? "₹" + a.cost_inr : "Free"}) — ${escapeHtml(a.short_desc || "")}
            </li>
          `
            )
            .join("")}
        </ul>
      </div>
    `
      )
      .join("");

    content.innerHTML = `
      <div style="margin-bottom:16px;">
        <p style="font-size:0.875rem; color:#6B7062;">${escapeHtml(plan.destination.overview)}</p>
      </div>
      <div style="background:#FAF9F5; border:1px solid #DFDACF; border-radius:6px; padding:12px; margin-bottom:20px; display:flex; justify-content:space-between;">
        <span><strong>Travelers:</strong> ${plan.trip_params.travelers}</span>
        <span><strong>Travel Style:</strong> ${plan.trip_params.travel_style}</span>
        <span><strong>Est. Total:</strong> ${formatInr(plan.budget_breakdown.total_estimated_cost)}</span>
      </div>
      <div>${daysHtml}</div>
    `;

    modal.style.display = "flex";

    closeBtn.onclick = () => (modal.style.display = "none");
    modal.onclick = (e) => {
      if (e.target === modal) modal.style.display = "none";
    };

    exportBtn.onclick = () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(plan, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `ODEYSSEY-${plan.destination.name}-plan.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    };

    printBtn.onclick = () => window.print();

    loadBtn.onclick = () => {
      // Re-fill planner form and open
      sessionStorage.setItem("odeyssey_load_plan", JSON.stringify(plan));
      window.location.href = `/planner?destination=${encodeURIComponent(plan.destination.name)}&days=${plan.trip_params.days}&travel_style=${plan.trip_params.travel_style}`;
    };
  }

  // =========================================================================
  // EXPOSE GLOBAL API FOR INLINE HANDLERS
  // =========================================================================
  window.ODEYSSEY = {
    removeActivity,
    recalculateBudget,
    toggleBudgetAdjustment,
    regeneratePlan,
    exportPlanText,
    saveCurrentTrip,
    deleteSavedTrip,
    openTripModal,
  };
})();
