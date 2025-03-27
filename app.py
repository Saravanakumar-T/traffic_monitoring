import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import datetime
import random
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Load Dataset
@st.cache_data
def load_data():
    file_path = "data/chennai_traffic_data_final.csv"
    df = pd.read_csv(file_path)
    return df

df = load_data()

# Streamlit Title
st.title("🚦 Chennai Traffic & Alternative Route Map")

# Sidebar - Dataset Preview
st.sidebar.header("📂 Dataset Preview")
st.sidebar.write(df.head())

# Dropdown for Start & Destination
st.sidebar.header("📍 Select Route")
locations = df["Location"].unique().tolist()
start_location = st.sidebar.selectbox("Start Location", locations)
destination_location = st.sidebar.selectbox("Destination", locations)

# Get coordinates for selected locations
start_row = df[df["Location"] == start_location].iloc[0]
destination_row = df[df["Location"] == destination_location].iloc[0]
start_coords = (start_row["Latitude"], start_row["Longitude"])
destination_coords = (destination_row["Latitude"], destination_row["Longitude"])

# Get road network graph
G = ox.graph_from_place("Chennai, India", network_type="drive")

# Find nearest nodes in the graph
orig_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
dest_node = ox.distance.nearest_nodes(G, destination_coords[1], destination_coords[0])

# Find shortest route
shortest_route = nx.shortest_path(G, orig_node, dest_node, weight="length")

# Find alternative (low-traffic) route by avoiding high-traffic nodes
high_traffic_nodes = set(df[df["Traffic Density"] == "High"]["Location"])

# Remove high-traffic nodes from the graph
G_low_traffic = G.copy()
for node in list(G.nodes):
    node_location = ox.geocode_to_gdf([ox.graph_to_gdfs(G, nodes=True).loc[node]["geometry"]])
    if node_location.iloc[0]["geometry"] in high_traffic_nodes:
        G_low_traffic.remove_node(node)

# Find alternative route
try:
    alt_route = nx.shortest_path(G_low_traffic, orig_node, dest_node, weight="length")
except:
    alt_route = shortest_route  # If no low-traffic route is found, use shortest route

# Initialize Map
route_map = folium.Map(location=start_coords, zoom_start=12, tiles="CartoDB Positron")

# Plot shortest route (blue)
shortest_path_coords = [(G.nodes[node]["y"], G.nodes[node]["x"]) for node in shortest_route]
folium.PolyLine(shortest_path_coords, color="blue", weight=5, opacity=0.7, tooltip="Shortest Route").add_to(route_map)

# Plot alternative route (green)
alt_path_coords = [(G.nodes[node]["y"], G.nodes[node]["x"]) for node in alt_route]
folium.PolyLine(alt_path_coords, color="green", weight=5, opacity=0.7, tooltip="Low-Traffic Route").add_to(route_map)

# Mark start and destination points
folium.Marker(start_coords, icon=folium.Icon(color="blue", icon="play"), popup=f"Start: {start_location}").add_to(route_map)
folium.Marker(destination_coords, icon=folium.Icon(color="red", icon="flag"), popup=f"Destination: {destination_location}").add_to(route_map)

# Display Map
folium_static(route_map)
