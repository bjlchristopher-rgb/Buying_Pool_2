import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="🏠 Canada Home Affordability", layout="wide")

st.title("🏠 Canada Home Affordability Calculator")
st.markdown("**Find out how many people can afford your home by region**")

# REGIONS - Update rates here
REGIONS = {
    "🇨🇦 National": {"down": 0.05, "rate": 0.045, "pop": 20_000_000},
    "🇴🇳 Ontario": {"down": 0.05, "rate": 0.047, "pop": 15_000_000},
    "🇧🇨 BC": {"down": 0.05, "rate": 0.049, "pop": 5_300_000},
    "🇦🇧 Alberta": {"down": 0.05, "rate": 0.043, "pop": 4_500_000},
    "🇶🇨 Quebec": {"down": 0.03, "rate": 0.044, "pop": 9_000_000}
}

# Income distribution
income_range = np.linspace(1, 400_000, 1000)
mu, sigma = 10.45, 0.95
scale = np.exp(mu)

def lognorm_cdf(x, s, scale):
    z = (np.log(x) - np.log(scale)) / s
    return 0.5 * (1 + np.tanh(np.sqrt(2) * z / 2) + np.sqrt(2/np.pi) * np.exp(-z**2/2))

# Mortgage function
def calc_affordable(price, down_pct, rate):
    down_payment = price * down_pct
    loan = price - down_payment
    monthly_rate = rate / 12
    n_payments = 25 * 12
    monthly_payment = loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    income_needed = monthly_payment * 12 / 0.28
    return income_needed, down_payment

# Calculator
col1, col2 = st.columns([1,2])

with col1:
    st.header("🏠 Property")
    price = st.number_input("Purchase Price ($)", 100000, 3000000, 800000, 25000)
    region = st.selectbox("Region", list(REGIONS.keys()))
    
    region_data = REGIONS[region]
    income_needed, down_payment = calc_affordable(price, region_data["down"], region_data["rate"])
    
    # Calculate affordability
    prob = 1 - lognorm_cdf(income_needed, sigma, scale)
    people = prob * region_data["pop"]
    pct = prob * 100

with col2:
    st.header("✅ Results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Can Afford", f"{people:,.0f}", f"{pct:.1f}%")
    c2.metric("Min Income", f"${income_needed:,.0f}")
    c3.metric("Down Payment", f"${down_payment:,.0f}")

# Comparison table
st.subheader("📊 All Regions")
comparison = []
for r_name, r_data in REGIONS.items():
    inc, _ = calc_affordable(price, r_data["down"], r_data["rate"])
    p = 1 - lognorm_cdf(inc, sigma, scale)
    comparison.append([r_name, f"${inc:,.0f}", f"{p*r_data['pop']:,.0f}", f"{p*100:.1f}%"])

df = pd.DataFrame(comparison, columns=["Region", "Min Income", "Can Afford", "% Pop"])
st.dataframe(df, use_container_width=True)

# Chart
st.subheader("📈 Income Distribution")
fig = go.Figure()
fig.add_trace(go.Scatter(x=income_range, y=np.exp(-(np.log(income_range/scale)/sigma)**2/2)/income_range*1000,
                        mode='lines', line=dict(color='#1f77b4', width=4)))
fig.add_vline(x=income_needed, line_dash="dash", line_color="red", 
              annotation_text=f"Need ${income_needed:,.0f}+")
fig.update_layout(height=400, hovermode='x')
fig.update_xaxes(title="Income ($)", tickformat="$,d")
st.plotly_chart(fig, use_container_width=True)
