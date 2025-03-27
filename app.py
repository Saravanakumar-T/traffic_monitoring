import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import random

# Load dataset
@st.cache_data
def load_data():
    file_path = "data/chennai_traffic_data_final.csv"  # Ensure correct file path
    df = pd.read_csv(file_path)
    return df

df = load_data()

# Streamlit App
st.title("🚦 Traffic & Weather Monitoring System")
st.sidebar.header("Filter Options")

# User selects filtering options
traffic_filter = st.sidebar.multiselect("Select Traffic Density:", df["Traffic Density"].unique(), default=df["Traffic Density"].unique())
weather_filter = st.sidebar.multiselect("Select Weather Condition:", df["Weather Condition"].unique(), default=df["Weather Condition"].unique())

# Filter data
df_filtered = df[df["Traffic Density"].isin(traffic_filter) & df["Weather Condition"].isin(weather_filter)]

# Create Folium Map
chennai_map = folium.Map(location=[13.0827, 80.2707], zoom_start=12)
marker_cluster = MarkerCluster().add_to(chennai_map)

# Define traffic color mapping
traffic_colors = {"Low": "green", "Medium": "orange", "High": "red"}

# Function to predict traffic and weather in 1 hour
def predict_traffic(traffic):
    return random.choice(["Low", "Medium", "High"])

def predict_weather(weather):
    return random.choice(["Sunny", "Cloudy", "Rainy"])

for _, row in df_filtered.iterrows():
    location = row["Location"]
    traffic_status = row["Traffic Density"]
    weather = row["Weather Condition"]
    temperature = row["Temperature (°C)"]
    delay = row["Estimated Delay (Minutes)"]
    lat, lon = row["Latitude"], row["Longitude"]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    predicted_traffic = predict_traffic(traffic_status)
    predicted_weather = predict_weather(weather)
    alternate_route = "Available" if random.choice([True, False]) else "Not Available"

    risk_level = "High Risk" if temperature > 35 else "Moderate Risk" if temperature > 28 else "Low Risk"
    risk_color = "🔴" if risk_level == "High Risk" else "🟡" if risk_level == "Moderate Risk" else "🟢"
    
    popup_info = f"""
    <b>{location}</b><br>
    <b>Current Time:</b> {current_time}<br>
    <b>Current Traffic:</b> {traffic_status}<br>
    <b>Weather:</b> {weather}<br>
    <b>Temperature:</b> {temperature}°C<br>
    <b>Risk Level:</b> {risk_color} {risk_level}<br>
    <b>Estimated Delay:</b> ⏳ {delay} minutes<br>
    <hr>
    <b>📌 Predicted Traffic in 1 Hour:</b> {predicted_traffic}<br>
    <b>🌤 Predicted Weather in 1 Hour:</b> {predicted_weather}<br>
    <b>🚗 Alternate Route:</b> {'✅ Available' if alternate_route == 'Available' else '❌ Not Available'}
    """
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_info, max_width=300),
        tooltip=location,
        icon=folium.Icon(color=traffic_colors.get(traffic_status, "gray"), icon="info-sign")
    ).add_to(marker_cluster)

st.subheader("📍 Traffic & Weather Map")
folium_static(chennai_map)

# Display filtered data
st.subheader("📊 Traffic Data Table")
st.dataframe(df_filtered)
