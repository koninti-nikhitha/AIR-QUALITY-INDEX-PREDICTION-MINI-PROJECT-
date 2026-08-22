import streamlit as st
import requests
import numpy as np
import joblib
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="AQI Monitoring System", layout="wide")
st.title("🌍 Air Quality Monitoring System")

# ------------------------------
# SIDEBAR
# ------------------------------
st.sidebar.header("Select City")
city = st.sidebar.selectbox("City", ["Delhi", "Bengaluru", "Hyderabad", "Mumbai", "Ahmedabad"])

# ------------------------------
# AUTO REFRESH
# ------------------------------
st_autorefresh(interval=10000, key="refresh")

# ------------------------------
# LOAD MODELS
# ------------------------------
@st.cache_resource
def load_models():
    aqi_model = joblib.load("aqi_model.pkl")
    forecast_model = joblib.load("forecast_model.pkl")
    return aqi_model, forecast_model

aqi_model, forecast_model = load_models()

# ------------------------------
# FETCH DATA FROM BACKEND
# ------------------------------
st.header(f"📡 Air Quality Data ({city})")

try:
    url = f"http://127.0.0.1:5000/get-data?city={city}"
    response = requests.get(url, timeout=5)

    if response.status_code == 200:
        data = response.json()

        pm25 = data["pm25"]
        pm10 = data["pm10"]
        no2 = data["no2"]
        so2 = data["so2"]
        co = data["co"]
        o3 = data["o3"]
    else:
        st.error("❌ API Error")
        st.stop()

except:
    st.error("⚠ Backend not running!")
    st.stop()

# ------------------------------
# DISPLAY METRICS
# ------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("PM2.5", round(pm25,2))
col2.metric("PM10", round(pm10,2))
col3.metric("NO2", round(no2,2))

col4, col5, col6 = st.columns(3)
col4.metric("SO2", round(so2,2))
col5.metric("CO", round(co,2))
col6.metric("O3", round(o3,2))

# ------------------------------
# AQI PREDICTION
# ------------------------------
input_data = np.array([[pm25, pm10, no2, so2, co, o3]])
prediction = aqi_model.predict(input_data)[0]

st.subheader(f"Predicted AQI: {round(prediction,2)}")

# ------------------------------
# AQI CATEGORY
# ------------------------------
def get_category(aqi):
    if aqi <= 50:
        return "Good", "green"
    elif aqi <= 100:
        return "Satisfactory", "yellow"
    elif aqi <= 200:
        return "Moderately Polluted", "orange"
    elif aqi <= 300:
        return "Poor", "red"
    elif aqi <= 400:
        return "Very Poor", "purple"
    else:
        return "Severe", "maroon"

category, color = get_category(prediction)

st.markdown(f"### AQI Category: <span style='color:{color}'>{category}</span>", unsafe_allow_html=True)

# ------------------------------
# ALERT
# ------------------------------
if prediction > 300:
    st.error("🚨 Severe Pollution! Avoid going outside.")
elif prediction > 200:
    st.warning("⚠ Very unhealthy air quality.")
elif prediction > 100:
    st.info("Moderate air quality. Take precautions.")
else:
    st.success("Good air quality.")

# ------------------------------
# GAUGE
# ------------------------------
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=prediction,
    title={'text': "AQI Level"},
    gauge={
        'axis': {'range': [0, 500]},
        'steps': [
            {'range': [0, 50], 'color': "green"},
            {'range': [50, 100], 'color': "yellow"},
            {'range': [100, 200], 'color': "orange"},
            {'range': [200, 300], 'color': "red"},
            {'range': [300, 500], 'color': "purple"},
        ],
    }
))

st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# HEALTH RECOMMENDATIONS
# ------------------------------
st.header("🩺 Health Recommendations")

st.subheader("🔴 Important Suggestions (Based on AQI)")

if prediction > 300:
    st.error("• Avoid outdoor exposure completely\n• Use air purifier\n• Wear N95 mask")
elif prediction > 200:
    st.warning("• Limit outdoor activities\n• Avoid exercise outside\n• Keep windows closed")
elif prediction > 100:
    st.info("• Reduce prolonged outdoor exertion\n• Stay hydrated")
else:
    st.success("• Safe for normal activities")

# Detailed groups
health = {
    "👶 Babies": [
        "Keep indoors",
        "Use air purifier",
        "Avoid smoke exposure"
    ],
    "🧒 Children": [
        "Avoid outdoor sports",
        "Wear mask if AQI is high",
        "Maintain hygiene"
    ],
    "🧑 Adults": [
        "Limit heavy exercise",
        "Stay hydrated",
        "Avoid polluted areas"
    ],
    "🤰 Pregnant Women": [
        "Avoid traffic areas",
        "Limit outdoor walking",
        "Use mask"
    ],
    "❤️ Heart Patients": [
        "Avoid exertion",
        "Keep medicines ready",
        "Stay indoors"
    ],
    "😷 Asthma Patients": [
        "Carry inhaler",
        "Avoid dust exposure",
        "Stay alert for symptoms"
    ],
    "👴 Elderly": [
        "Stay indoors",
        "Monitor breathing",
        "Consult doctor if needed"
    ]
}

for group, tips in health.items():
    with st.expander(group):
        for tip in tips:
            st.write(f"✔ {tip}")

# ------------------------------
# FORECAST
# ------------------------------
st.header("📈 7-Day AQI Forecast")

future = forecast_model.make_future_dataframe(periods=7)
forecast = forecast_model.predict(future)

forecast_7 = forecast[['ds', 'yhat']].tail(7)
forecast_7.columns = ["Date", "Predicted AQI"]

st.dataframe(forecast_7)
st.line_chart(forecast_7.set_index("Date"))

# ------------------------------
# DOWNLOAD
# ------------------------------
csv = forecast_7.to_csv(index=False)
st.download_button("⬇ Download Forecast", csv, "aqi_forecast.csv")

# ------------------------------
# YEARLY TREND
# ------------------------------
st.header("📊 Yearly AQI Trend")

df = pd.read_csv("datasets/city_day.csv")
df['Date'] = pd.to_datetime(df['Date'])

if "City" in df.columns:
    df = df[df["City"] == city]

df['Year'] = df['Date'].dt.year
yearly = df.groupby("Year")["AQI"].mean().reset_index()

st.line_chart(yearly.set_index("Year"))

# ------------------------------
# COMPARISON
# ------------------------------
if len(yearly) >= 2:
    last = yearly.iloc[-1]['AQI']
    prev = yearly.iloc[-2]['AQI']

    if last > prev:
        st.error(f"AQI Increased ⬆ ({round(last-prev,2)})")
    else:
        st.success(f"AQI Decreased ⬇ ({round(prev-last,2)})")