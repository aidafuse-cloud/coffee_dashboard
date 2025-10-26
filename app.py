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

st.markdown("### ☕ World Green Coffee Price Overview")
st.markdown("This table displays movement of current green coffee prices in USD and MYR, along with 3-month averages for comparison.")
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


# === SECTION: CONSUMER SEARCH TRENDS (GOOGLE) ===
st.subheader("🔍 Consumer Search Trends (Google)")
st.caption("Trends based on Google searches over the past 3 months")

from pytrends.request import TrendReq

@st.cache_data(ttl=600)
def fetch_google_trends(keywords):
    pytrends = TrendReq()
    try:
        pytrends.build_payload(kw_list=keywords, timeframe="today 3-m")
        df = pytrends.interest_over_time()
        return df if not df.empty else None
    except Exception:
        return None

keywords = ["Ethiopian coffee", "Geisha coffee", "Anaerobic coffee"]
df_trends = fetch_google_trends(keywords)

if df_trends is not None and not df_trends.empty:
    fig = px.line(
        df_trends[keywords],
        labels={"value": "Search Interest", "date": "Date"},
        title="Search Interest Over Time",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Unable to fetch Google Trends data at the moment. Please try again later.")

# === SECTION: Weather ===
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
st.caption("Additional specialty regions can be plotted as more data becomes available.")
st.caption("Live temperature and weather across known specialty origins.")
st_folium(m, width=700, height=500)


# === SECTION: SPECIALTY FOCUS ===
st.subheader("🎯 Specialty Focus: High-Scoring Coffee Origins")
st.markdown("These origins consistently produce specialty-grade coffees scoring 80+ SCA points, often in small volumes.")

# 🧠 Explanation + Interactive Threshold Sliders
with st.expander("📊 How suggestions are made (click to expand)"):
    st.markdown(
        """
        💡 **How suggestions are made**:
        - ✅ **Buy**: Current price is significantly lower than average for similar quality (below selected RM threshold).
        - 🟡 **Wait**: Prices are very high and may not reflect stable market value (above selected RM threshold).
        - ⚪️ **Hold**: Fair or average range — consider holding off until better opportunities.

        _You can adjust the thresholds below to reflect your local risk tolerance or purchasing goals._
        """
    )

# === Threshold sliders ===
buy_threshold = st.slider("✅ Buy if below (RM/lb)", min_value=200, max_value=600, value=400, step=10)
wait_threshold = st.slider("🟡 Wait if above (RM/lb)", min_value=600, max_value=2000, value=700, step=10)

# === Data ===
specialty_data = pd.DataFrame({
    "Country": [
        "Panama", "Yemen", "Ethiopia", "Costa Rica", "Guatemala", "Colombia",
        "El Salvador", "Burundi", "Rwanda", "Brazil"
    ],
    "Notable Region / Producer": [
        "Boquete (Hacienda La Esmeralda)", "Haraz (Qima Coffee)", "Yirgacheffe / Sidamo", "Tarrazú",
        "Huehuetenango", "Wilton Benitez / La Palma y El Tucán", "Santa Ana", "Ngozi", "Gakenke", "Daterra"
    ],
    "Avg. SCA Score": [90.5, 88.0, 88.5, 87.0, 86.5, 88.0, 86.0, 86.5, 86.5, 85.0],
    "Auction Price (USD/lb) (raw)": [350.25, 180.00, 120.00, 105.00, 95.00, 110.00, 90.00, 85.00, 82.00, 75.00]
})

# === Get latest rate from earlier fetch ===
# Assuming `rate` variable is defined above this block

if rate:
    # Compute MYR raw price for logic
    specialty_data["Price (MYR/lb) (raw)"] = specialty_data["Auction Price (USD/lb) (raw)"] * rate

    # Suggestion logic (MYR-only)
    def get_suggestion(row):
        price_myr = row["Price (MYR/lb) (raw)"]
        if price_myr < buy_threshold:
            return "✅ Buy"
        elif price_myr > wait_threshold:
            return "🟡 Wait"
        else:
            return "⚪️ Hold"

    specialty_data["Suggestion"] = specialty_data.apply(get_suggestion, axis=1)

    # Format currency for display
    specialty_data["Auction Price (USD/lb)"] = specialty_data["Auction Price (USD/lb) (raw)"].apply(lambda x: f"${x:.2f}")
    specialty_data["Price (MYR/lb)"] = specialty_data["Price (MYR/lb) (raw)"].apply(lambda x: f"RM{x:,.2f}")

    # Drop raw columns
    specialty_data = specialty_data.drop(columns=["Auction Price (USD/lb) (raw)", "Price (MYR/lb) (raw)"])

else:
    st.warning("Couldn't fetch USD to MYR rate. Showing USD prices only.")

    # Show Hold-only fallback if no rate
    specialty_data["Suggestion"] = "⚪️ Hold"

    # Format available USD price
    specialty_data["Auction Price (USD/lb)"] = specialty_data["Auction Price (USD/lb) (raw)"].apply(lambda x: f"${x:.2f}")
    specialty_data = specialty_data.drop(columns=["Auction Price (USD/lb) (raw)"])


# === Display Final Table ===
st.dataframe(specialty_data)

# 📌 Source citation
st.markdown(
    """
    <div style='font-size: 0.85em; color: gray; margin-top: 12px;'>
    📌 <strong>Data Sources:</strong><br>
    • 🟫 <em>Green coffee prices</em>: Aggregated from <a href='https://www.coffeeexporter.org' target='_blank'>Coffee Exporter Alliance</a> and public auction results (e.g. Cup of Excellence, Qima Coffee)<br>
    • 🌍 <em>Production by country</em>: Based on latest reports from the <a href='https://www.ico.org/' target='_blank'>International Coffee Organization (ICO)</a> and <a href='https://sca.coffee' target='_blank'>Specialty Coffee Association (SCA)</a><br>
    • 💱 <em>Exchange rates</em>: Live rates from <a href='https://exchangerate.host' target='_blank'>exchangerate.host</a><br><br>
    🔄 This dashboard is powered by live and periodically updated data. Figures may vary slightly based on source refresh frequency.
    </div>
    """,
    unsafe_allow_html=True
)


