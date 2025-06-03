
from flask import Flask, render_template, request, redirect
import requests
import datetime
import json
import os

app = Flask(__name__)
UTC = datetime.timezone.utc
FALLBACK_FILE = "fallback_earthquakes.json"

@app.route('/')
def home():
    return redirect('/map')

@app.route('/map', methods=["GET"])
def map_view():
    now = datetime.datetime.now(UTC)
    start = request.args.get("start", (now - datetime.timedelta(days=60)).strftime("%Y-%m-%d"))
    minmag = request.args.get("minmag", "")

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start,
        "endtime": now.strftime("%Y-%m-%d"),
        "minlatitude": -90,
        "maxlatitude": 90,
        "minlongitude": -180,
        "maxlongitude": 180,
    }
    if minmag:
        params["minmagnitude"] = minmag

    quake_data = []
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        # Save fallback
        with open(FALLBACK_FILE, "w") as f:
            json.dump(data, f)

    except Exception as e:
        if os.path.exists(FALLBACK_FILE):
            with open(FALLBACK_FILE, "r") as f:
                data = json.load(f)
        else:
            return "<h2>USGS API unavailable and no fallback data found.</h2>"

    for f in data.get("features", []):
        props = f["properties"]
        coords = f["geometry"]["coordinates"]
        quake_data.append({
            "longitude": coords[0],
            "latitude": coords[1],
            "depth_km": coords[2],
            "magnitude": props["mag"],
            "place": props["place"],
            "time": datetime.datetime.fromtimestamp(props["time"] / 1000.0, UTC).strftime("%Y-%m-%dT%H:%M:%S")
        })

    return render_template("map.html", quake_data=quake_data)

if __name__ == "__main__":
    app.run(debug=True)
