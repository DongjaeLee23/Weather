import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("WEATHER_API_KEY")  # WeatherAPI key

app = Flask(__name__)

# ---------- Weather Helpers ----------
def get_weather_data(lat, lon, units="metric"):
    """Current weather (for fallback/form POST)."""
    try:
        response = requests.get("http://api.weatherapi.com/v1/current.json", params={
            "key": TOKEN,
            "q": f"{lat},{lon}",
            "aqi": "no"
        })
        response.raise_for_status()
        data = response.json()

        # convert temp if units == "imperial"
        if units == "imperial":
            data["current"]["temp"] = data["current"]["temp_f"]
        else:
            data["current"]["temp"] = data["current"]["temp_c"]

        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_forecast_data(lat, lon, units="metric", days=7):
    try:
        response = requests.get("http://api.weatherapi.com/v1/forecast.json", params={
            "key": TOKEN,
            "q": f"{lat},{lon}",
            "days": days,
            "aqi": "no",
            "alerts": "no"
        })
        response.raise_for_status()
        data = response.json()

        # Normalize units
        if units == "imperial":
            data["current"]["temp"] = data["current"]["temp_f"]
            for day in data["forecast"]["forecastday"]:
                day["day"]["avgtemp"] = day["day"]["avgtemp_f"]
        else:
            data["current"]["temp"] = data["current"]["temp_c"]
            for day in data["forecast"]["forecastday"]:
                day["day"]["avgtemp"] = day["day"]["avgtemp_c"]

        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



def get_city_suggestions(query, limit=5):
    """Autocomplete city suggestions."""
    if not query:
        return []

    try:
        response = requests.get("http://api.weatherapi.com/v1/search.json", params={
            "key": TOKEN,
            "q": query
        })
        response.raise_for_status()
        data = response.json()
        suggestions = []
        for city in data[:limit]:
            label = f"{city['name']}, {city.get('region','')}, {city['country']}".strip(", ")
            suggestions.append({
                "label": label,
                "lat": city["lat"],
                "lon": city["lon"]
            })
        return suggestions
    except requests.exceptions.RequestException:
        return []

# ---------- Routes ----------
@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "")
    return jsonify(get_city_suggestions(query))


@app.route("/weather")
def weather():
    """AJAX endpoint for current + forecast data."""
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    units = request.args.get("units", "metric")
    if not lat or not lon:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    data = get_forecast_data(lat, lon, units=units)
    return jsonify(data)


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page with search + form submit (fallback)."""
    weather_data = None
    error_msg = None
    if request.method == "POST":
        lat = request.form.get("lat")
        lon = request.form.get("lon")
        units = request.form.get("units", "metric")
        if lat and lon:
            weather_data = get_weather_data(lat, lon, units=units)
        else:
            error_msg = "Please select a valid city from suggestions."
    return render_template("index.html", weather=weather_data, error=error_msg)


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)
