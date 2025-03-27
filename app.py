import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import datetime
import random

# Load Dataset
@st.cache_data
def load_data():
    file_path = "data/chennai_traffic_data_final.csv"
    df = pd.read_csv(file_path)
    return df

df = load_data()

# Streamlit Title
st.title("🚦 Chennai Traffic & Weather Live Map")

# Sidebar: User Input for Start and Destination
st.sidebar.header("🛣️ Route Planner")
start_point = st.sidebar.selectbox("Select Start Location", df["Location"].unique())
destination = st.sidebar.selectbox("Select Destination", df["Location"].unique())

# Get Current Time
current_time = datetime.datetime.now()
next_hour_time = current_time + datetime.timedelta(hours=1)

# Function to Predict Traffic and Weather for Next Hour
def predict_traffic(traffic_now):
    return random.choice(["Low", "Medium", "High"]) if traffic_now == "High" else traffic_now

def predict_weather(weather_now):
    return random.choice(["Sunny", "Cloudy", "Rainy", "Foggy", "Stormy"])

df["Predicted Traffic"] = df["Traffic Density"].apply(predict_traffic)
df["Predicted Weather"] = df["Weather Condition"].apply(predict_weather)

# Initialize Main Map
chennai_map = folium.Map(location=[13.0827, 80.2707], zoom_start=12, tiles="CartoDB Positron")

# Filter Start & Destination Data
route_df = df[(df["Location"] == start_point) | (df["Location"] == destination)]

# Add Traffic Data to Main Route Map
for _, row in route_df.iterrows():
    risk_level = "🔴 High Risk" if row["Traffic Density"] == "High" else ("🟠 Medium Risk" if row["Traffic Density"] == "Medium" else "🟢 Low Risk")
    alt_route = "✅ Available" if row["Alternate Route Available"] == "Yes" else "❌ Not Available"
    
    popup_text = f"""
    <b>Location:</b> {row['Location']}<br>
    <b>Current Time:</b> {current_time.strftime("%Y-%m-%d %H:%M:%S")}<br>
    <b>Traffic:</b> {row['Traffic Density']}<br>
    <b>Weather:</b> {row['Weather Condition']}<br>
    <b>Temperature:</b> {row['Temperature (°C)']}°C<br>
    <b>Risk Level:</b> {risk_level}<br>
    <b>Estimated Delay:</b> ⏳ {row['Estimated Delay (Minutes)']} min<br>
    <b>📌 Predicted Traffic (Next Hour):</b> {row['Predicted Traffic']}<br>
    <b>📌 Predicted Weather (Next Hour):</b> {row['Predicted Weather']}<br>
    <b>Alternate Route:</b> {alt_route}
    """
    
    marker_color = "red" if row["Traffic Density"] == "High" else ("orange" if row["Traffic Density"] == "Medium" else "green")
    
    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=popup_text,
        icon=folium.Icon(color=marker_color)
    ).add_to(chennai_map)

# Display Main Route Map
st.subheader("🛣️ Main Route Traffic Details")
folium_static(chennai_map)

# Alternative Route Suggestion
alternative_df = df[df["Alternate Route Available"] == "Yes"]
low_traffic_alt = alternative_df[alternative_df["Traffic Density"] == "Low"]

if not low_traffic_alt.empty:
    st.subheader("🚗 Suggested Alternative Route (Lower Traffic)")
    alt_map = folium.Map(location=[13.0827, 80.2707], zoom_start=12, tiles="CartoDB Positron")
    
    for _, row in low_traffic_alt.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"Alternative Route - {row['Location']} (Low Traffic)",
            icon=folium.Icon(color="green")
        ).add_to(alt_map)
    
    folium_static(alt_map)
else:
    st.subheader("❌ No Alternative Routes Available with Low Traffic")
