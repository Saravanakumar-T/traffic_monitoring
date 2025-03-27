import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import datetime
import random
import networkx as nx
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

# Create Graph for Route Calculation
G = nx.Graph()

# Add Nodes (Locations)
for _, row in df.iterrows():
    G.add_node(row["Location"], pos=(row["Latitude"], row["Longitude"]))

# Add Edges (Roads between locations based on proximity)
for _, row1 in df.iterrows():
    for _, row2 in df.iterrows():
        if row1["Location"] != row2["Location"]:
            dist = geodesic((row1["Latitude"], row1["Longitude"]), (row2["Latitude"], row2["Longitude"])).km
            if dist < 5:  # Connect locations within 5 km range
                G.add_edge(row1["Location"], row2["Location"], weight=dist)

# Find Shortest Route
shortest_route = []
if start_location in G and destination_location in G:
    try:
        shortest_route = nx.shortest_path(G, source=start_location, target=destination_location, weight="weight")
    except nx.NetworkXNoPath:
        st.warning("No direct road connection found between the selected locations!")

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
folium_static(chennai_map)

# Show Route Details
st.write("### 📍 Route Details")
route_df = df[df["Location"].isin(shortest_route)]
if not route_df.empty:
    st.write(route_df[["Location", "Traffic Density", "Estimated Delay (Minutes)", "Alternate Route Available"]])
else:
    st.warning("No traffic data available for the selected route.")

# Alternative Route Map
if shortest_route:
    alt_map = folium.Map(location=[13.0827, 80.2707], zoom_start=12, tiles="CartoDB Positron")

    for i in range(len(shortest_route) - 1):
        loc1 = df[df["Location"] == shortest_route[i]].iloc[0]
        loc2 = df[df["Location"] == shortest_route[i + 1]].iloc[0]
        folium.PolyLine([(loc1["Latitude"], loc1["Longitude"]), (loc2["Latitude"], loc2["Longitude"])],
                        color="blue", weight=4, opacity=0.7).add_to(alt_map)
    
    # Add Start and End Markers
    start_loc = df[df["Location"] == start_location].iloc[0]
    dest_loc = df[df["Location"] == destination_location].iloc[0]

    folium.Marker(
        location=[start_loc["Latitude"], start_loc["Longitude"]],
        popup=f"Start: {start_location}",
        icon=folium.Icon(color="blue", icon="play")
    ).add_to(alt_map)

    folium.Marker(
        location=[dest_loc["Latitude"], dest_loc["Longitude"]],
        popup=f"Destination: {destination_location}",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(alt_map)

    st.write("### 🛣️ Alternative Route with Low Traffic")
    folium_static(alt_map)
else:
    st.warning("No alternative route found between the selected locations!")

# Summary of High Traffic Areas
high_traffic_summary = df[df["Traffic Density"] == "High"][["Location", "Estimated Delay (Minutes)"]].groupby("Location").mean().reset_index()
st.write("### 🚦 High Traffic Areas & Estimated Delays")
st.write(high_traffic_summary)
