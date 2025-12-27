#travel_app
import streamlit as st
import json
import pandas as pd
import requests
import random
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

# -------------------- DATA LOADING --------------------
flights_df = pd.read_json("flights.json")
hotels_df = pd.read_json("hotels.json")
places_df = pd.read_json("places.json")

# -------------------- TOOLS --------------------
def search_flights(source, destination, flights_df, top_n=5):
    result = flights_df[
        (flights_df['from'] == source) &
        (flights_df['to'] == destination)
    ]
    return result.sort_values("price").head(top_n)

def find_hotels(city, max_price, hotels_df, top_n=5):
    result = hotels_df[
        (hotels_df['city'] == city) &
        (hotels_df['price_per_night'] <= max_price)
    ]
    return result.sort_values("price_per_night").head(top_n)

def discover_places(city, places_df, top_n=5):
    result = places_df[places_df['city'] == city]
    return result.sort_values("rating", ascending=False).head(top_n)

def get_weather_agent(city, days=3):
    geolocator = Nominatim(user_agent="travel_agent")
    location = geolocator.geocode(city)

    if not location:
        return ["Weather unavailable"] * days

    lat, lon = location.latitude, location.longitude
    start_date = datetime.today().strftime("%Y-%m-%d")
    end_date = (datetime.today() + timedelta(days=days-1)).strftime("%Y-%m-%d")

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max&timezone=auto&start_date={start_date}&end_date={end_date}"
        data = requests.get(url).json()
        temps = data['daily']['temperature_2m_max']
        return [f"{t}°C" for t in temps]
    except:
        return [f"{round(random.uniform(28,35),1)}°C" for _ in range(days)]

def estimate_budget(flight_price, hotel_price, days):
    hotel_total = hotel_price * days
    food = 1000 * days
    return {
        "Flight": flight_price,
        "Hotel": hotel_total,
        "Food & Travel": food,
        "Total": flight_price + hotel_total + food
    }

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="AI Travel Planner", layout="centered")

st.title("🧭 Agentic AI Travel Planner")

cities = sorted(set(flights_df['from']).union(set(flights_df['to'])))

source_city = st.selectbox("Source City", cities)
destination_city = st.selectbox("Destination City", cities)

num_days = st.number_input("Trip Duration (Days)", min_value=1, value=3)

# ✅ ONLY NEW ADDITION
max_hotel_price = st.number_input(
    "Max Hotel Price per Night",
    min_value=500,
    value=5000,
    step=500
)

if st.button("Plan Trip"):
    st.markdown("---")

    flights = search_flights(source_city, destination_city, flights_df)
    hotels = find_hotels(destination_city, max_hotel_price, hotels_df)
    places = discover_places(destination_city, places_df, top_n=num_days * 2)
    weather = get_weather_agent(destination_city, num_days)

    if flights.empty or hotels.empty:
        st.error("No suitable flights or hotels found.")
    else:
        flight = flights.iloc[0]
        hotel = hotels.iloc[0]

        st.subheader(f"Your {num_days}-Day Trip to {destination_city}")

        st.markdown("### ✈️ Flight Selected")
        st.write(f"- {flight['airline']} (₹{flight['price']})")

        st.markdown("### 🏨 Hotel Booked")
        st.write(f"- {hotel['name']} (₹{hotel['price_per_night']}/night, {hotel['stars']}-star)")

        st.markdown("### ☀️ Weather")
        for i, temp in enumerate(weather, 1):
            st.write(f"- Day {i}: {temp}")

        st.markdown("### 📍 Itinerary")
        place_list = places['name'].tolist()
        total_places = len(place_list)

        for i in range(num_days):
          p1 = place_list[(i * 2) % total_places]
          p2 = place_list[(i * 2 + 1) % total_places]
          st.write(f"Day {i+1}: {p1}, {p2}")




        budget = estimate_budget(flight['price'], hotel['price_per_night'], num_days)

        st.markdown("### 💰 Estimated Budget")
        for k, v in budget.items():
            st.write(f"- {k}: ₹{v}")

        st.markdown("---")
        st.write(f"### ✅ Total Cost: ₹{budget['Total']}")

