import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Smart Retirement Decision Engine",
    page_icon="📈",
    layout="wide"
)

# ==========================================
# INPUTS
# ==========================================

st.title("📈 Smart Retirement Decision Engine")

st.markdown(
    "Understand how today's financial decisions impact your retirement."
)

st.sidebar.header("Employee Inputs")

age = st.sidebar.number_input(
    "Current Age",
    min_value=18,
    max_value=60,
    value=28
)

retirement_age = st.sidebar.number_input(
    "Retirement Age",
    min_value=50,
    max_value=70,
    value=60
)

salary = st.sidebar.number_input(
    "Annual Salary (₹)",
    min_value=100000,
    value=2000000,
    step=100000
)

emi = st.sidebar.number_input(
    "Monthly EMI (₹)",
    min_value=0,
    value=50000,
    step=5000
)

epf_pct = st.sidebar.slider(
    "EPF Contribution %",
    0,
    20,
    12
)

nps_pct = st.sidebar.slider(
    "NPS Contribution %",
    0,
    20,
    5
)

scenario = st.sidebar.selectbox(
    "Scenario",
    ["Conservative", "Base", "Aggressive"]
)

salary_growth = st.sidebar.slider(
    "Salary Growth %",
    0.0,
    15.0,
    7.0
)

inflation = st.sidebar.slider(
    "Inflation %",
    0.0,
    10.0,
    5.0
)

discount_rate = st.sidebar.slider(
    "Discount Rate %",
    0.0,
    15.0,
    6.0
)

# ==========================================
# ASSUMPTIONS
# ==========================================

if scenario == "Conservative":
    growth = 0.08
elif scenario == "Base":
    growth = 0.10
else:
    growth = 0.12

years = retirement_age - age

monthly_salary = salary / 12

take_home = monthly_salary * (
    1 - (epf_pct + nps_pct) / 100
)

# ==========================================
# RETIREMENT PROJECTION
# ==========================================

annual_contribution = salary * (
    epf_pct + nps_pct
) / 100

retirement_wealth = 0

for _ in range(years):
    retirement_wealth = (
        retirement_wealth * (1 + growth)
        + annual_contribution
    )

required_wealth = salary * 20

gap = max(
    0,
    required_wealth - retirement_wealth
)

# ==========================================
# READINESS SCORE
# ==========================================

wealth_score = min(
    50,
    (retirement_wealth / required_wealth) * 50
)

housing_score = max(
    0,
    25 - (emi / monthly_salary) * 25
)

savings_score = min(
    25,
    (epf_pct + nps_pct) * 1.5
)

score = round(
    wealth_score
    + housing_score
    + savings_score
)

score = max(
    0,
    min(100, score)
)

# ==========================================
# DASHBOARD
# ==========================================

c1, c2, c3 = st.columns(3)

c1.metric(
    "💰 Monthly Take Home",
    f"₹{take_home:,.0f}"
)

c2.metric(
    "🏦 Retirement Wealth",
    f"₹{retirement_wealth:,.0f}"
)

c3.metric(
    "🎯 Readiness Score",
    f"{score}/100"
)

st.divider()

c4, c5 = st.columns(2)

c4.metric(
    "Required Wealth",
    f"₹{required_wealth:,.0f}"
)

c5.metric(
    "Retirement Gap",
    f"₹{gap:,.0f}"
)

# ==========================================
# HOUSING RISK
# ==========================================

st.divider()

emi_ratio = (
    emi / take_home
    if take_home > 0
    else 0
)

if emi_ratio < 0.40:
    risk = "🟢 Safe"
elif emi_ratio < 0.60:
    risk = "🟡 Moderate"
else:
    risk = "🔴 Risky"

st.subheader("🏠 Housing Risk")

st.write(
    f"{risk} | EMI consumes {emi_ratio:.0%} of take-home income."
)

# ==========================================
# RETIREMENT PROGRESS
# ==========================================

st.divider()

st.subheader("📍 Retirement Progress")

progress = min(
    100,
    retirement_wealth / required_wealth * 100
)

st.progress(progress / 100)

st.write(
    f"{progress:.0f}% of target retirement wealth achieved."
)

# ==========================================
# WECARE PLAN
# ==========================================

st.divider()

st.subheader("💼 WeCare Plan")

final_salary = salary * (
    (1 + salary_growth / 100) ** years
)

final_monthly_salary = final_salary / 12

wecare_contribution = salary * 0.10

wecare_pension = (
    final_monthly_salary * 0.50
)

commutation_factor = 13

wecare_commuted_value = (
    wecare_pension
    * 12
    * commutation_factor
)

wc1, wc2, wc3 = st.columns(3)

wc1.metric(
    "WeCare Contribution (10%)",
    f"₹{wecare_contribution:,.0f}"
)

wc2.metric(
    "Monthly Pension at Retirement",
    f"₹{wecare_pension:,.0f}"
)

wc3.metric(
    "Commuted Value",
    f"₹{wecare_commuted_value:,.0f}"
)

# ==========================================
# AI COACH
# ==========================================

st.divider()

st.subheader("💡 Smart Recommendations")

recommendations = []

if emi_ratio > 0.60:
    recommendations.append(
        "⚠️ EMI is consuming more than 60% of take-home income."
    )

elif emi_ratio > 0.40:
    recommendations.append(
        "🏠 Housing costs are moderately high."
    )

if nps_pct < 8:
    recommendations.append(
        f"📈 Consider increasing NPS from {nps_pct}% to 8%."
    )

if gap > 10000000:
    recommendations.append(
        f"💰 Retirement shortfall detected: ₹{gap:,.0f}"
    )

if years < 15:
    recommendations.append(
        "⏳ Retirement is approaching. Increasing contributions now may help."
    )

if score >= 80:
    recommendations.append(
        "✅ Retirement readiness appears strong."
    )

if len(recommendations) == 0:
    recommendations.append(
        "✅ Your current retirement strategy appears balanced."
    )

for item in recommendations:
    st.write(item)

# ==========================================
# CURRENT VS RECOMMENDED
# ==========================================

recommended_nps = max(
    nps_pct,
    8
)

recommended_wealth = retirement_wealth * (
    1 + (recommended_nps - nps_pct) * 0.15
)

wealth_gain = (
    recommended_wealth
    - retirement_wealth
)

take_home_loss = (
    monthly_salary
    * (recommended_nps - nps_pct)
    / 100
)

st.divider()

st.subheader("🎯 Current vs Recommended")

col1, col2 = st.columns(2)

with col1:

    st.markdown("### Current Plan")

    st.metric(
        "NPS %",
        f"{nps_pct}%"
    )

    st.metric(
        "Retirement Wealth",
        f"₹{retirement_wealth:,.0f}"
    )

    st.metric(
        "Readiness Score",
        f"{score}/100"
    )

with col2:

    st.markdown("### Recommended Plan")

    st.metric(
        "NPS %",
        f"{recommended_nps}%"
    )

    st.metric(
        "Retirement Wealth",
        f"₹{recommended_wealth:,.0f}"
    )

    st.metric(
        "Potential Score",
        f"{min(100, score + 10)}/100"
    )

st.info(
    f"""
Increasing NPS from {nps_pct}% to {recommended_nps}% may reduce monthly take-home by ₹{take_home_loss:,.0f} but could increase projected retirement wealth by ₹{wealth_gain:,.0f}.
"""
)

# ==========================================
# SCENARIO COMPARISON
# ==========================================

st.divider()

st.subheader("📊 Scenario Comparison")

scenario_df = pd.DataFrame({
    "Scenario": [
        "Conservative",
        "Base",
        "Aggressive"
    ],
    "Projected Wealth": [
        retirement_wealth * 0.85,
        retirement_wealth,
        retirement_wealth * 1.20
    ]
})

fig = px.bar(
    scenario_df,
    x="Scenario",
    y="Projected Wealth",
    text="Projected Wealth",
    title="Projected Retirement Wealth"
)

fig.update_traces(
    texttemplate="₹%{text:,.0f}",
    textposition="outside"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

with st.expander("📋 Assumptions"):

    st.write(
        f"Salary Growth: {salary_growth}%"
    )

    st.write(
        f"Inflation: {inflation}%"
    )

    st.write(
        f"Discount Rate: {discount_rate}%"
    )

    st.write(
        "WeCare Contribution: 10% of salary"
    )

    st.write(
        "WeCare Pension: 50% of final monthly salary"
    )

    st.write(
        "Commutation Factor: 13"
    )