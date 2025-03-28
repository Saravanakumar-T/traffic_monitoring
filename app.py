import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import datetime
import random

# Load Dataset with Caching
@st.cache_data
def load_data():
    file_path = "data/chennai_traffic_data_final.csv"
    df = pd.read_csv(file_path, usecols=["Location", "Latitude", "Longitude", "Traffic Density", "Weather Condition", "Temperature (°C)", "Estimated Delay (Minutes)", "Alternate Route Available"])
    return df

df = load_data()

# Streamlit Title
st.title("🚦 Chennai Traffic & Weather Live Map")

# Sidebar - Dataset Preview
st.sidebar.header("📂 Dataset Preview")
MAX_PREVIEW_ROWS = 5  # Limit preview rows
st.sidebar.write(df.head(MAX_PREVIEW_ROWS))

# Get Current Time
current_time = datetime.datetime.now()

# Function to Predict Traffic and Weather for Next Hour
@st.cache_data
def predict_traffic_and_weather(df):
    def predict_traffic(traffic_now):
        return random.choice(["Low", "Medium", "High"]) if traffic_now == "High" else traffic_now

    def predict_weather(weather_now):
        return random.choice(["Sunny", "Cloudy", "Rainy", "Foggy", "Stormy"])

    df["Predicted Traffic"] = df["Traffic Density"].apply(predict_traffic)
    df["Predicted Weather"] = df["Weather Condition"].apply(predict_weather)
    return df

df = predict_traffic_and_weather(df)

# Optimize Map Initialization with Caching
@st.cache_data
def create_map(data):
    chennai_map = folium.Map(location=[13.0827, 80.2707], zoom_start=12, tiles="CartoDB Positron")
    MAX_MARKERS = 500  # Limit markers to improve performance
    if len(data) > MAX_MARKERS:
        data = data.sample(MAX_MARKERS, random_state=42)
    
    for _, row in data.iterrows():
        marker_color = "red" if row["Traffic Density"] == "High" else ("orange" if row["Traffic Density"] == "Medium" else "green")
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"""
            <b>Location:</b> {row['Location']}<br>
            <b>Traffic:</b> {row['Traffic Density']}<br>
            <b>Weather:</b> {row['Weather Condition']}<br>
            <b>Temperature:</b> {row['Temperature (°C)']}°C<br>
            <b>Estimated Delay:</b> ⏳ {row['Estimated Delay (Minutes)']} min<br>
            <b>Predicted Traffic (Next Hour):</b> {row['Predicted Traffic']}<br>
            <b>Predicted Weather (Next Hour):</b> {row['Predicted Weather']}<br>
            <b>Alternate Route:</b> {'✅ Available' if row['Alternate Route Available'] == 'Yes' else '❌ Not Available'}
            """,
            icon=folium.Icon(color=marker_color)
        ).add_to(chennai_map)
    
    return chennai_map

chennai_map = create_map(df)
folium_static(chennai_map)

# Summary of High Traffic Areas
high_traffic_summary = df[df["Traffic Density"] == "High"][["Location", "Estimated Delay (Minutes)"]].groupby("Location").mean().reset_index()
st.write("### 🚦 High Traffic Areas & Estimated Delays")
st.write(high_traffic_summary)
