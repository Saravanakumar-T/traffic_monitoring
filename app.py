import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import datetime
import random
from geopy.distance import geodesic

# Load Dataset
@st.cache_data
def load_data():
    file_path = "data/chennai_traffic_data_final.csv"
    df = pd.read_csv(file_path)
    return df

df = load_data()

# Streamlit Title
st.title("🚦 Chennai Traffic & Weather Live Map")

# Sidebar - Dataset Preview
st.sidebar.header("📂 Dataset Preview")
st.sidebar.write(df.head())

# Dropdown for Start & Destination
st.sidebar.header("📍 Select Route")
locations = df["Location"].unique().tolist()
start_location = st.sidebar.selectbox("Start Location", locations)
destination_location = st.sidebar.selectbox("Destination", locations)

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

# Add Traffic Data to Map
for _, row in df.iterrows():
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

# Display Main Map
st.write("### 🗺️ Current Traffic Map")
folium_static(chennai_map)

# Find Alternative Low-Traffic Route
st.write("### 🚗 Suggested Alternative Route")
alt_map = folium.Map(location=[13.0827, 80.2707], zoom_start=12, tiles="CartoDB Positron")

start_data = df[df["Location"] == start_location].iloc[0]
dest_data = df[df["Location"] == destination_location].iloc[0]

low_traffic_df = df[df["Traffic Density"] == "Low"]
shortest_distance = float("inf")
best_alternative = None

for _, row in low_traffic_df.iterrows():
    distance = geodesic((start_data["Latitude"], start_data["Longitude"]), (row["Latitude"], row["Longitude"])).km + \
               geodesic((row["Latitude"], row["Longitude"]), (dest_data["Latitude"], dest_data["Longitude"])).km
    if distance < shortest_distance:
        shortest_distance = distance
        best_alternative = row

if best_alternative is not None:
    folium.Marker(
        location=[start_data["Latitude"], start_data["Longitude"]],
        popup=f"Start: {start_location}",
        icon=folium.Icon(color="blue", icon="play")
    ).add_to(alt_map)
    
    folium.Marker(
        location=[best_alternative["Latitude"], best_alternative["Longitude"]],
        popup=f"Alternative Route via {best_alternative['Location']}\nTraffic: {best_alternative['Traffic Density']}",
        icon=folium.Icon(color="green", icon="road")
    ).add_to(alt_map)
    
    folium.Marker(
        location=[dest_data["Latitude"], dest_data["Longitude"]],
        popup=f"Destination: {destination_location}",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(alt_map)
    
    st.success(f"Suggested Alternative Route: {start_location} ➝ {best_alternative['Location']} ➝ {destination_location}")
else:
    st.warning("No low-traffic alternative route found.")

# Display Alternative Route Map
folium_static(alt_map)

# Show Route Details
st.write("### 📍 Route Details")
route_df = df[(df["Location"] == start_location) | (df["Location"] == destination_location)]
if not route_df.empty:
    st.write(route_df[["Location", "Traffic Density", "Estimated Delay (Minutes)", "Alternate Route Available"]])
else:
    st.warning("No traffic data available for the selected route.")

# Summary of High Traffic Areas
high_traffic_summary = df[df["Traffic Density"] == "High"][["Location", "Estimated Delay (Minutes)"]].groupby("Location").mean().reset_index()
st.write("### 🚦 High Traffic Areas & Estimated Delays")
st.write(high_traffic_summary)
