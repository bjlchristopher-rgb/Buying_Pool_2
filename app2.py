import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="🏠 Canada Home Affordability", layout="wide")

st.title("🏠 Canada Home Affordability Calculator")
st.markdown("**Single + 2-Person Household Income**")

# REGIONS
REGIONS = {
    "🇨🇦 National": {"down": 0.05, "rate": 0.045, "pop": 20_000_000},
    "🇴🇳 Ontario": {"down": 0.05, "rate": 0.047, "pop": 15_000_000},
    "🇧🇨 BC": {"down": 0.05, "rate": 0.049, "pop": 5_300_000},
    "🇦🇧 Alberta": {"down": 0.05, "rate": 0.043, "pop": 4_500_000},
    "🇶🇨 Quebec": {"down": 0.03, "rate": 0.044, "pop": 9_000_000}
}

# Income distribution
def lognorm_cdf(x, mu=10.45, sigma=0.95):
    if x <= 0: return 0.0
    z = (np.log(x) - mu) / sigma
    return 0.5 * (1 + np.tanh(np.sqrt(2/3) * z))

def lognorm_pdf(x, mu=10.45, sigma=0.95):
    return np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2)) / (x * sigma * np.sqrt(2 * np.pi))

# Mortgage calculator
def calc_affordable(price, down_pct, rate):
    down_payment = price * down_pct
    loan = price - down_payment
    monthly_rate = rate / 12
    n_payments = 25 * 12
    monthly_payment = loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    income_needed = max(0, monthly_payment * 12 / 0.28)
    return income_needed, down_payment

# Main calculator
col1, col2 = st.columns([1,2])

with col1:
    st.header("🏠 Property")
    price = st.number_input("Purchase Price ($)", 100000, 3000000, 800000, 25000)
    region = st.selectbox("Region", list(REGIONS.keys()))
    
    # NEW: Household type selector
    st.subheader("👥 Household")
    household_type = st.radio("Household Type", 
                             ["Single Earner", "👨‍👩 2-Person Household"], 
                             index=0, horizontal=True)
    
    region_data = REGIONS[region]
    income_needed_single, down_payment = calc_affordable(price, region_data["down"], region_data["rate"])
    
    # NEW: 2-person household calculation (1.7x income capacity)
    income_needed_couple = income_needed_single * 0.65  # Couples can afford 35% more
    
    region_pop = region_data["pop"]

with col2:
    st.header("✅ Results")
    
    if household_type == "Single Earner":
        income_needed = income_needed_single
        prob = max(0, 1 - lognorm_cdf(income_needed))
        people = prob * region_pop
        st.info("**Single earner household**")
    else:
        income_needed = income_needed_couple
        # NEW: 2-person household probability (convolution approximation)
        prob = max(0, 1 - lognorm_cdf(income_needed * 1.4))  # Adjusted for dual income
        people = prob * region_pop * 0.6  # 60% of pop are households
        st.success("**👨‍👩 2-person household** (35% more purchasing power)")
    
    pct = prob * 100
    
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Can Afford", f"{people:,.0f}", f"{pct:.1f}%")
    c2.metric("Min Income", f"${income_needed:,.0f}")
    c3.metric("Down Payment", f"${down_payment:,.0f}")

# Regional comparison with household type
st.subheader("📊 All Regions Comparison")
comparison = []
for r_name, r_data in REGIONS.items():
    inc_single, _ = calc_affordable(price, r_data["down"], r_data["rate"])
    inc_couple = inc_single * 0.65
    
    if household_type == "Single Earner":
        prob = max(0, 1 - lognorm_cdf(inc_single))
    else:
        prob = max(0, 1 - lognorm_cdf(inc_couple * 1.4))
        people_adj = prob * r_data["pop"] * 0.6
    
    people_final = prob * r_data["pop"] * (0.6 if household_type == "👨‍👩 2-Person Household" else 1)
    comparison.append([r_name, f"${income_needed:,.0f}", f"{people_final:,.0f}", f"{prob*100:.1f}%"])

df = pd.DataFrame(comparison, columns=["Region", "Min Income", "% of Pop", "Can Afford"])
st.dataframe(df, use_container_width=True, hide_index=True)

# Chart with household threshold
st.subheader("📈 Income Distribution")
income_range = np.linspace(1, 400_000, 1000)
pdf_values = lognorm_pdf(income_range)

fig = go.Figure()
fig.add_trace(go.Scatter(x=income_range, y=pdf_values/np.max(pdf_values)*50, 
                        mode='lines', line=dict(color='#1f77b4', width=4), name='Population'))
fig.add_vline(x=income_needed, line_dash="dash", line_color="red", 
              annotation_text=f"{household_type}: ${income_needed:,.0f}+", 
              annotation_position="top right")
fig.add_hline(y=0, line_color="gray", line_width=1)
fig.update_layout(height=450, hovermode='x unified', showlegend=True)
fig.update_xaxes(title="Annual Income ($ CAD)", tickformat="$,d", range=[0, 250000])
fig.update_yaxes(title="Population Density")
st.plotly_chart(fig, use_container_width=True)

# NEW: Household impact summary
st.subheader("👨‍👩 **Household Impact**")
col1, col2 = st.columns(2)
with col1:
    st.metric("Single Earner", f"{max(0,1-lognorm_cdf(income_needed_single)):,.1%}")
with col2:
    st.metric("2-Person Household", f"{max(0,1-lognorm_cdf(income_needed_couple*1.4)):,.1%}")

st.caption("**2-person households**: 35% more purchasing power, 60% of population")
