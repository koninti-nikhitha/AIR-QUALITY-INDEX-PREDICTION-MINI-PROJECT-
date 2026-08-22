from flask import Flask, jsonify, request
import pandas as pd

app = Flask(__name__)

# ------------------------------
# LOAD DATASET
# ------------------------------
data = pd.read_csv("datasets/city_day.csv")

# Clean column names (important)
data.columns = data.columns.str.strip()

# ------------------------------
# DEFAULT ROUTE (FIXES NOT FOUND)
# ------------------------------
@app.route("/")
def home():
    return "✅ AQI Backend is Running! Use /get-data?city=Delhi"

# ------------------------------
# GET DATA API
# ------------------------------
@app.route("/get-data", methods=["GET"])
def get_data():
    city = request.args.get("city")

    df = data.copy()

    # Filter by city
    if "City" in df.columns and city:
        df = df[df["City"] == city]

    # Remove missing values
    df = df.dropna(subset=["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"])

    # If no data found
    if df.empty:
        return jsonify({"error": "No data available"}), 404

    # Pick random row
    row = df.sample(1)

    result = {
        "pm25": float(row["PM2.5"].values[0]),
        "pm10": float(row["PM10"].values[0]),
        "no2": float(row["NO2"].values[0]),
        "so2": float(row["SO2"].values[0]),
        "co": float(row["CO"].values[0]),
        "o3": float(row["O3"].values[0])
    }

    return jsonify(result)

# ------------------------------
# RUN SERVER
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)