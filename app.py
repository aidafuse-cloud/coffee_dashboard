import streamlit as st
import pandas as pd
import plotly.express as px
from pytrends.request import TrendReq
import requests

st.set_page_config(page_title="Specialty Coffee Market Dashboard", layout="wide")

# --- HEADER ---
st.title("☕ Specialty Coffee Intelligence Dashboard")
st.markdown("Get real-time insights on prices, production, consumer trends, and weather.")

# --- SECTION: GREEN COFFEE PRICES ---
st.subheader("💰 Green Coffee Prices")
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


# --- SECTION: PRODUCTION TRENDS ---
st.subheader("🌍 Coffee Production by Country")
production = pd.DataFrame({
    "Country": ["Brazil", "Ethiopia", "Colombia", "Vietnam", "Indonesia"],
    "2021": [3550, 471, 858, 1680, 750],
    "2022": [3400, 500, 900, 1720, 770]
})
prod_melt = production.melt(id_vars="Country", var_name="Year", value_name="Production (000 tons)")
fig_prod = px.bar(prod_melt, x="Country", y="Production (000 tons)", color="Year", barmode="group")
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
st.subheader("🌦️ Weather Snapshots – Top Coffee Regions")
weather_api_key = "e00472f60c950f601599d6d44e561ccc"
cities = {
    "Brazil": "Varginha",
    "Colombia": "Medellin",
    "Ethiopia": "Addis Ababa"
}

cols = st.columns(len(cities))
for i, (country, city) in enumerate(cities.items()):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        with cols[i]:
            st.metric(label=country, value=f"{temp}°C", delta=desc)
    else:
        with cols[i]:
            st.error(f"{country} weather unavailable")

st.markdown("—")
st.caption("Built for specialty café market strategy | v1.0")
