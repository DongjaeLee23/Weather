import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('WEATHER_TOKEN')
BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
BASE_GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"

app = Flask(__name__)


def build_weather_query(lat, lon, imperial=False):
    units = "imperial" if imperial else "metric"
    return f"{BASE_WEATHER_API_URL}?lat={lat}&lon={lon}&units={units}&appid={TOKEN}"


def get_weather_data(lat, lon, imperial=False):
    url = build_weather_query(lat, lon, imperial)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@app.route("/autocomplete")
def autocomplete():
    """AJAX endpoint for city autocomplete."""
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    params = {
        "q": query,
        "limit": 5,
        "appid": TOKEN
    }
    try:
        response = requests.get(BASE_GEOCODE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        suggestions = []
        for city in data:
            name = city.get("name")
            state = city.get("state")
            country = city.get("country")
            lat = city.get("lat")
            lon = city.get("lon")
            if name and lat and lon:
                label = name
                if state:
                    label += f", {state}"
                if country:
                    label += f", {country}"
                suggestions.append({
                    "label": label,
                    "lat": lat,
                    "lon": lon
                })
        return jsonify(suggestions)
    except requests.exceptions.RequestException:
        return jsonify([])


@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error_msg = None
    if request.method == "POST":
        lat = request.form.get("lat")
        lon = request.form.get("lon")
        units = request.form.get("units")
        if lat and lon:
            weather_data = get_weather_data(lat, lon, imperial=(units=="imperial"))
        else:
            error_msg = "Please select a valid city from suggestions."
    return render_template("index.html", weather=weather_data, error=error_msg)


if __name__ == "__main__":
    app.run(debug=True)
