import streamlit as st
import pandas as pd
import plotly.express as px
from pytrends.request import TrendReq
import requests
import folium
from streamlit_folium import st_folium
import os
weather_api_key = st.secrets["WEATHER_API_KEY"] 

st.set_page_config(page_title="Specialty Coffee Market Dashboard", layout="wide")

# --- HEADER ---
st.title("☕ Specialty Coffee Intelligence Dashboard")
st.markdown("Get real-time insights on prices, production, consumer trends, and weather.")

# --- SECTION: GREEN COFFEE PRICES ---
st.subheader("💰 Green Coffee Prices")
st.markdown("### ☕ Coffee Price Overview")
st.markdown("This table displays current green coffee prices in USD and MYR, along with 3-month averages for comparison.")
price_data = pd.DataFrame({
    "Country": ["Brazil", "Ethiopia", "Colombia", "Vietnam", "Indonesia"],
    "Current Price (USD/lb)": [1.92, 2.14, 2.05, 1.70, 1.80],
    "3-Month Avg": [1.85, 2.10, 2.00, 1.68, 1.78]
})
# --- BUY OR WAIT LOGIC ---
def buy_or_wait(row):
    if row["Current Price (USD/lb)"] > row["3-Month Avg"]:
        return "🟡 Wait"
    elif row["Current Price (USD/lb)"] < row["3-Month Avg"]:
        return "🟢 Buy"
    else:
        return "⚪ Hold"

price_data["Suggestion"] = price_data.apply(buy_or_wait, axis=1)

# --- USD to MYR Exchange Rate ---
def get_usd_to_myr():
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["rates"]["MYR"]
    return None

rate = get_usd_to_myr()

if rate:
    st.metric("💱 USD to MYR", f"1 USD = {rate:.2f} MYR")
    price_data["Price (MYR)"] = price_data["Current Price (USD/lb)"] * rate
else:
    st.warning("Could not retrieve USD to MYR exchange rate.")

# --- Display updated table ---
st.markdown("### 💡 Current Green Coffee Prices (in MYR)")
st.dataframe(price_data[["Country", "Current Price (USD/lb)", "Price (MYR)", "3-Month Avg", "Suggestion"]])


# --- SECTION: COFFEE PRODUCTION BY COUNTRY ---
st.subheader("🌍 Coffee Production by Country")
st.markdown("""
This table shows estimated annual green coffee production (all grades) for selected countries, along with forecast changes.  
☕ **Note:** Countries included are based on publicly available data. Specialty-grade volumes are a subset of these totals.
""")

# Cleaned production dataset
production_data = pd.DataFrame({
    "Country": ["Brazil", "Vietnam", "Colombia", "Indonesia", "Ethiopia",
                "Kenya", "Uganda", "Guatemala"],
    "Production (’000 bags 60‑kg)": [66400, 30100, 12900, 10900, 8360,
                                     574, 6959, 2250],
    "2025/26 Estimate Change (%)": [0.5, 6.9, None, None, None,
                                     None, None, None]
})

# Display table
st.dataframe(production_data, use_container_width=True)

# Bar chart
fig_prod = px.bar(
    production_data,
    x="Country",
    y="Production (’000 bags 60‑kg)",
    title="Annual Coffee Production Volume by Country",
    labels={"Production (’000 bags 60‑kg)": "Production (’000 60‑kg bags)"}
)
st.plotly_chart(fig_prod, use_container_width=True)


# --- SECTION: CONSUMER TRENDS ---
st.subheader("🔍 Consumer Search Trends (Google)")
pytrends = TrendReq()
keywords = ["Ethiopian coffee", "Geisha coffee", "Anaerobic coffee"]
pytrends.build_payload(kw_list=keywords, timeframe="today 3-m")
trends_data = pytrends.interest_over_time()

if not trends_data.empty:
    st.line_chart(trends_data[keywords])
else:
    st.warning("Google Trends data not available at the moment.")

# --- SECTION: WEATHER (OPTIONAL) ---
from streamlit_folium import st_folium
import folium

# Coordinates for specialty regions
regions = {
    "Yirgacheffe, Ethiopia": [6.16, 38.2],
    "Antioquia, Colombia": (6.4956, -75.5550),
    "Neiva, Colombia": [2.94, -75.28],
    "Huehuetenango, Guatemala": [15.32, -91.47],
    "Boquete, Panama": [8.78, -82.44],
    "Tarrazú, Costa Rica": [9.65, -84.02]
}

# Fetch live weather for each region
weather_points = []
for name, coords in regions.items():
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={coords[0]}&lon={coords[1]}&appid={weather_api_key}&units=metric"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        weather_points.append({
            "name": name,
            "coords": coords,
            "temp": temp,
            "desc": desc
        })

# --- Display Weather Map ---
st.markdown("## 🗺️ Weather Map: Specialty Coffee Growing Regions")
st.markdown("Live temperature and weather across known specialty origins.")

weather_map = folium.Map(location=[0, 0], zoom_start=2)

for point in weather_points:
    lat, lon = point["coords"]
    tooltip = f"{point['name']}<br>🌡️ Temp: {point['temp']}K<br>🌤️ Weather: {point['desc']}"
    folium.Marker(
        location=[lat, lon],
        tooltip=tooltip,
        icon=folium.Icon(color="green", icon="cloud")
    ).add_to(weather_map)

st_folium(weather_map, width=700, height=500)


# Build the map
m = folium.Map(location=[6, -30], zoom_start=2, tiles="CartoDB positron")

for point in weather_points:
    popup_text = f"{point['name']}<br>🌡️ {point['temp']}°C<br>{point['desc'].title()}"
    folium.Marker(
        location=point["coords"],
        popup=popup_text,
        icon=folium.Icon(color="green", icon="cloud")
    ).add_to(m)

# Show the map in Streamlit
st.subheader("🗺️ Weather Map: Specialty Coffee Growing Regions")
st.caption("Live temperature and weather across known specialty origins.")
st_folium(m, width=700, height=500)


# --- SECTION: SPECIALTY FOCUS ---
st.subheader("🧬 Specialty Focus: High-Scoring Coffee Origins")
st.markdown("These origins consistently produce specialty-grade coffees scoring 80+ SCA points, often in small volumes.")

specialty_data = pd.DataFrame({
    "Country": [
        "Panama", "Yemen", "Ethiopia", "Costa Rica", "Guatemala", "Colombia", "El Salvador", "Burundi", "Rwanda", "Brazil"
    ],
    "Notable Region / Producer": [
        "Boquete (Hacienda La Esmeralda)", 
        "Haraz (Qima Coffee)", 
        "Yirgacheffe / Sidamo", 
        "Tarrazú", 
        "Huehuetenango", 
        "Wilton Benitez / La Palma y El Tucán", 
        "Santa Ana", 
        "Ngozi", 
        "Gakenke", 
        "Daterra"
    ],
    "Avg. SCA Score": [
        90.5, 88.0, 88.5, 87.0, 86.5, 88.0, 86.0, 86.5, 86.5, 85.0
    ],
    "Auction Price (USD/lb)": [
        350.25, 180.00, 120.00, 105.00, 95.00, 110.00, 90.00, 85.00, 82.00, 75.00
    ]
})

# --- Add MYR Conversion ---
if rate:
    specialty_data["Price (MYR/lb)"] = specialty_data["Auction Price (USD/lb)"] * rate

    # --- Add Buy or Wait Logic ---
    def buy_or_wait_specialty(row):
        if row["Auction Price (USD/lb)"] >= 150:
            return "🟡 Wait"
        elif row["Auction Price (USD/lb)"] <= 100:
            return "🟢 Buy"
        else:
            return "⚪ Hold"

    specialty_data["Suggestion"] = specialty_data.apply(buy_or_wait_specialty, axis=1)

    # Format currency
    specialty_data["Auction Price (USD/lb)"] = specialty_data["Auction Price (USD/lb)"].apply(lambda x: f"${x:.2f}")
    specialty_data["Price (MYR/lb)"] = specialty_data["Price (MYR/lb)"].apply(lambda x: f"RM{x:,.2f}")

else:
    st.warning("Couldn't fetch USD to MYR rate. Showing USD prices only.")

# --- Display Table ---
st.dataframe(specialty_data)


