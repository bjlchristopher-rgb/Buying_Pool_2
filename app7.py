import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="🏠 Canada Mortgage Calculator", layout="wide")

st.title("🏠 Canada Mortgage Affordability PRO")
st.markdown("**CMHC Stress Test • FIXED New Construction**")

# REGIONS
REGIONS = {
    "🇨🇦 National": {"rate": 0.045, "pop": 20_000_000},
    "🇴🇳 Ontario": {"rate": 0.047, "pop": 15_000_000},
    "🇧🇨 BC": {"rate": 0.049, "pop": 5_300_000},
    "🇦🇧 Alberta": {"rate": 0.043, "pop": 4_500_000},
    "🇶🇨 Quebec": {"rate": 0.044, "pop": 9_000_000}
}

def lognorm_cdf(x, mu=10.45, sigma=0.95):
    if x <= 0: return 0.0
    z = (np.log(x) - mu) / sigma
    return 0.5 * (1 + np.tanh(np.sqrt(2/3) * z))

def lognorm_pdf(x, mu=10.45, sigma=0.95):
    return np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2)) / (x * sigma * np.sqrt(2 * np.pi))

def calculate_down_payment(price):
    if price <= 500000:
        return price * 0.05
    elif price <= 1500000:
        first_500k = 500000 * 0.05
        above_500k = (price - 500000) * 0.10
        return first_500k + above_500k
    else:
        return price * 0.20

def calc_stress_test_payment(price, contract_rate, first_time_buyer, new_construction):
    down_payment = calculate_down_payment(price)
    loan = price - down_payment
    
    # Stress test rate
    stress_rate = max(0.0525, contract_rate + 0.02)
    
    # FIXED: Clear amortization logic + visual feedback
    if first_time_buyer or new_construction:
        amortization_years = 30
    else:
        amortization_years = 25
    
    n_payments = amortization_years * 12
    monthly_rate = stress_rate / 12
    
    monthly_payment = loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    income_needed = monthly_payment * 12 / 0.39
    
    return income_needed, down_payment, stress_rate, amortization_years

# ===========================================
# MAIN INPUTS - FIXED VISUAL FEEDBACK
# ===========================================
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.header("🏠 Property 1")
    price1 = st.number_input("Price ($)", 100000, 3000000, 800000, 25000, key="p1")

with col2:
    st.header("🏠 Property 2")
    price2 = st.number_input("Price ($)", 100000, 3000000, 1000000, 25000, key="p2")

with col3:
    st.header("👥 Buyer Profile")
    household_type = st.radio("Household", ["Single (40%)", "👨‍👩 Couple (60%)"], horizontal=True)
    
    # FIXED: Clear visual status + immediate feedback
    col_ft, col_nc = st.columns(2)
    first_time = col_ft.checkbox("🆕 First-Time (30yr amort)", value=True)
    new_constr = col_nc.checkbox("🏗️ New Build (30yr amort)", value=False)
    
    # FIXED: IMMEDIATE VISUAL CONFIRMATION
    amort_status = "30 years" if (first_time or new_constr) else "25 years"
    st.info(f"**Amortization: {amort_status}** {'(First-Time/New Build)' if first_time or new_constr else '(Standard)'}")

region = st.selectbox("Region", list(REGIONS.keys()))
region_data = REGIONS[region]
region_pop = region_data["pop"]

# ===========================================
# CALCULATIONS
# ===========================================
income1_single, down1, stress1, amort1 = calc_stress_test_payment(price1, region_data["rate"], first_time, new_constr)
income2_single, down2, stress2, amort2 = calc_stress_test_payment(price2, region_data["rate"], first_time, new_constr)

if household_type == "Single (40%)":
    income1_needed = income1_single
    income2_needed = income2_single
    pop_mult = 0.40
else:
    income1_needed = income1_single * 0.75
    income2_needed = income2_single * 0.75
    pop_mult = 0.60

prob1 = max(0, 1 - lognorm_cdf(income1_needed))
prob2 = max(0, 1 - lognorm_cdf(income2_needed))
people1 = prob1 * region_pop * pop_mult
people2 = prob2 * region_pop * pop_mult
buyer_difference = people1 - people2

# ===========================================
# RESULTS
# ===========================================
st.subheader("📊 Real CMHC Stress Test Results")

col_a, col_b = st.columns(2)

with col_a:
    st.header(f"**Property 1: ${price1:,}**")
    st.metric("Potential Buyers", f"{people1:,.0f}", f"{prob1*100:.1f}%")
    st.metric("Stress Test Income", f"${income1_needed:,.0f}")
    st.metric("Down Payment", f"${down1:,.0f}")
    st.caption(f"*{stress1*100:.1f}% stress • **{amort1}yr**")

with col_b:
    st.header(f"**Property 2: ${price2:,}**")
    st.metric("Potential Buyers", f"{people2:,.0f}", f"{prob2*100:.1f}%")
    st.metric("Stress Test Income", f"${income2_needed:,.0f}")
    st.metric("Down Payment", f"${down2:,.0f}")
    st.caption(f"*{stress2*100:.1f}% stress • **{amort2}yr**")

# BUYER DIFFERENCE
st.markdown("---")
col_diff1, col_diff2 = st.columns([1, 3])

with col_diff1:
    if abs(price1 - price2) > 50000:
        if buyer_difference > 0:
            st.metric("**🏆 Winner**", "**Property 1**", f"+{buyer_difference:,.0f}")
            st.success(f"**Property 1 wins with {buyer_difference:,.0f} more buyers**")
        elif buyer_difference < 0:
            st.metric("**🏆 Winner**", "**Property 2**", f"+{abs(buyer_difference):,.0f}")
            st.error(f"**Property 2 wins with {abs(buyer_difference):,.0f} more buyers**")
        else:
            st.warning("**Tie**")

with col_diff2:
    st.metric("**Buyer Difference**", f"{buyer_difference:,.0f}", f"{(people1-people2)/max(people1,people2)*100:+.1f}%")

# ===========================================
# TABLE + CHART
# ===========================================
col_table, col_chart = st.columns([1, 2])

with col_table:
    st.subheader("📋 All Regions")
    comparison = []
    for r_name, r_data in REGIONS.items():
        i1, d1, s1, a1 = calc_stress_test_payment(price1, r_data["rate"], first_time, new_constr)
        i2, d2, s2, a2 = calc_stress_test_payment(price2, r_data["rate"], first_time, new_constr)
        i1_adj = i1 * (0.75 if "Couple" in household_type else 1.0)
        i2_adj = i2 * (0.75 if "Couple" in household_type else 1.0)
        p1 = max(0, 1 - lognorm_cdf(i1_adj)) * r_data["pop"] * pop_mult
        p2 = max(0, 1 - lognorm_cdf(i2_adj)) * r_data["pop"] * pop_mult
        comparison.append([r_name, f"{p1:,.0f}", f"{p2:,.0f}"])
    
    df = pd.DataFrame(comparison, columns=["Region", f"${price1:,}", f"${price2:,}"])
    st.dataframe(df, use_container_width=True)

with col_chart:
    st.subheader("📈 Income Distribution")
    income_range = np.linspace(1, 400_000, 1000)
    pdf_values = lognorm_pdf(income_range)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=income_range, y=pdf_values/np.max(pdf_values)*50,
                            mode='lines', line=dict(color='#1f77b4', width=4)))
    fig.add_vline(x=income1_needed, line_dash="dash", line_color="blue",
                  annotation_text=f"Prop1: ${income1_needed:,.0f}", annotation_position="top left")
    fig.add_vline(x=income2_needed, line_dash="dash", line_color="orange",
                  annotation_text=f"Prop2: ${income2_needed:,.0f}", annotation_position="top right")
    fig.update_layout(height=450, hovermode='x unified')
    fig.update_xaxes(title="Income ($)", tickformat="$,d")
    st.plotly_chart(fig, use_container_width=True)

# FIXED DEBUG INFO
st.markdown("---")
st.caption(f"**Debug**: Prop1={amort1}yr | Prop2={amort2}yr | New Build={new_constr} | First-Time={first_time}")

with st.expander("📜 **CMHC Rules**"):
    st.markdown("""
    ✅ **Down**: 5% first $500K + 10% next + 20% over $1.5M
    ✅ **Stress Test**: 5.25% or contract+2% (39% GDS)  
    ✅ **30yr Amort**: First-time OR New Construction
    ✅ **25yr Amort**: Standard resale
    """)
