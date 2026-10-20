import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Smart Retirement Decision Engine",
    page_icon="📈",
    layout="wide",
)

SCENARIO_RETURNS = {
    "Conservative": 0.08,
    "Base": 0.10,
    "Aggressive": 0.12,
}
RETIREMENT_TARGET_MULTIPLE = 20
WECARE_CONTRIBUTION_RATE = 0.10
WECARE_PENSION_RATE = 0.50
WECARE_COMMUTATION_FACTOR = 13
RECOMMENDED_NPS_RATE = 8


def inr(value: float) -> str:
    """Format a numeric value as Indian rupees."""
    return f"₹{value:,.0f}"


def project_retirement(
    current_salary: float,
    years: int,
    epf_pct: float,
    nps_pct: float,
    salary_growth: float,
    investment_return: float,
    current_age: int,
) -> dict:
    """Project salary-linked contributions and accumulated wealth.

    Assumptions:
    - Salary grows at a constant annual rate.
    - EPF and NPS percentages are applied to projected annual salary.
    - Contributions are invested at the end of each year.
    - A single assumed return is applied to the combined contribution pool.
    """
    balance = 0.0
    total_contributions = 0.0
    records = []
    contribution_rate = (epf_pct + nps_pct) / 100

    for year in range(1, years + 1):
        projected_salary = current_salary * (1 + salary_growth) ** year
        annual_contribution = projected_salary * contribution_rate
        opening_balance = balance
        investment_growth = opening_balance * investment_return
        balance = opening_balance + investment_growth + annual_contribution
        total_contributions += annual_contribution

        records.append(
            {
                "Year": year,
                "Age": current_age + year,
                "Projected Annual Salary": projected_salary,
                "Annual EPF/NPS Contribution": annual_contribution,
                "Opening Balance": opening_balance,
                "Investment Growth": investment_growth,
                "Closing Balance": balance,
            }
        )

    return {
        "wealth": balance,
        "total_contributions": total_contributions,
        "records": records,
    }


def readiness_score(
    wealth: float,
    target_wealth: float,
    emi_ratio: float | None,
    epf_pct: float,
    nps_pct: float,
) -> int:
    """Return a custom illustrative readiness score out of 100."""
    if target_wealth > 0:
        wealth_score = min(50.0, max(0.0, wealth / target_wealth * 50))
    else:
        wealth_score = 50.0

    if emi_ratio is None:
        housing_score = 0.0
    else:
        housing_score = max(0.0, 25.0 - emi_ratio * 25.0)

    savings_score = min(25.0, max(0.0, (epf_pct + nps_pct) * 1.5))
    return max(0, min(100, round(wealth_score + housing_score + savings_score)))


def housing_risk(emi_ratio: float | None) -> tuple[str, str]:
    if emi_ratio is None:
        return "🔴 High / unavailable", "Take-home income is zero or negative in this simplified model."
    if emi_ratio < 0.40:
        return "🟢 Lower", "EMI is below 40% of calculated monthly take-home."
    if emi_ratio < 0.60:
        return "🟡 Moderate", "EMI is between 40% and 60% of calculated monthly take-home."
    return "🔴 High", "EMI is at least 60% of calculated monthly take-home."


def format_shortfall(gap: float) -> str:
    if gap > 0:
        return f"Shortfall: {inr(gap)}"
    return f"Surplus: {inr(abs(gap))}"


# =========================================================
# HEADER
# =========================================================
st.title("📈 Smart Retirement Decision Engine")
st.markdown(
    "Explore how today's financial decisions and economic assumptions "
    "can influence retirement outcomes."
)
st.caption(
    "Educational decision-support model using illustrative assumptions; "
    "not personalised financial advice."
)


# =========================================================
# SIDEBAR INPUTS
# =========================================================
st.sidebar.header("👤 Employee Inputs")

age = st.sidebar.number_input(
    "Current Age", min_value=18, max_value=60, value=28, step=1
)
retirement_age = st.sidebar.number_input(
    "Retirement Age", min_value=19, max_value=70, value=60, step=1
)
salary = st.sidebar.number_input(
    "Annual Salary (₹)", min_value=100000, value=2000000, step=100000
)
emi = st.sidebar.number_input(
    "Monthly EMI (₹)", min_value=0, value=50000, step=5000
)
epf_pct = st.sidebar.slider(
    "EPF Contribution (%)", min_value=0, max_value=20, value=12
)
nps_pct = st.sidebar.slider(
    "NPS Contribution (%)", min_value=0, max_value=20, value=5
)

st.sidebar.divider()
st.sidebar.header("📊 Projection Assumptions")
scenario = st.sidebar.selectbox(
    "Investment Return Scenario", list(SCENARIO_RETURNS.keys()), index=1
)
salary_growth_pct = st.sidebar.slider(
    "Annual Salary Growth (%)", min_value=0.0, max_value=15.0,
    value=7.0, step=0.5
)
inflation_pct = st.sidebar.slider(
    "Annual Inflation (%)", min_value=0.0, max_value=10.0,
    value=5.0, step=0.5
)
discount_rate_pct = st.sidebar.slider(
    "Discount Rate (%)", min_value=0.0, max_value=15.0,
    value=6.0, step=0.5
)

# Validate the relationship between the two age inputs before calculating.
if retirement_age <= age:
    st.error(
        "Retirement Age must be greater than Current Age. "
        "Please update the ages in the sidebar to continue."
    )
    st.stop()


# =========================================================
# NORMALISE ASSUMPTIONS AND RUN THE SELECTED PROJECTION
# =========================================================
years = int(retirement_age - age)
salary_growth = salary_growth_pct / 100
inflation = inflation_pct / 100
discount_rate = discount_rate_pct / 100
selected_return = SCENARIO_RETURNS[scenario]

current_monthly_salary = salary / 12
monthly_take_home = current_monthly_salary * (1 - (epf_pct + nps_pct) / 100)

current_projection = project_retirement(
    current_salary=salary,
    years=years,
    epf_pct=epf_pct,
    nps_pct=nps_pct,
    salary_growth=salary_growth,
    investment_return=selected_return,
    current_age=int(age),
)
retirement_wealth = current_projection["wealth"]
final_salary = salary * (1 + salary_growth) ** years

# Planning heuristic: target = 20 times projected final annual salary.
required_wealth = final_salary * RETIREMENT_TARGET_MULTIPLE
gap = required_wealth - retirement_wealth

# Convert terminal values into today's purchasing-power terms.
real_wealth_today = retirement_wealth / ((1 + inflation) ** years)
real_target_today = required_wealth / ((1 + inflation) ** years)

# Discount terminal values to today using the separate discount-rate input.
present_value_wealth = retirement_wealth / ((1 + discount_rate) ** years)
present_value_target = required_wealth / ((1 + discount_rate) ** years)
present_value_gap = present_value_target - present_value_wealth

emi_ratio = (emi / monthly_take_home) if monthly_take_home > 0 else None
risk_label, risk_description = housing_risk(emi_ratio)
score = readiness_score(
    wealth=retirement_wealth,
    target_wealth=required_wealth,
    emi_ratio=emi_ratio,
    epf_pct=epf_pct,
    nps_pct=nps_pct,
)


# =========================================================
# MAIN DASHBOARD
# =========================================================
st.subheader("📍 Retirement Dashboard")
c1, c2, c3 = st.columns(3)
c1.metric("💰 Monthly Take-Home*", inr(monthly_take_home))
c2.metric("🏦 Projected Retirement Wealth", inr(retirement_wealth))
c3.metric("🎯 Readiness Score", f"{score}/100")

c4, c5, c6 = st.columns(3)
c4.metric("Required Retirement Wealth", inr(required_wealth))
c5.metric(
    "Retirement Gap",
    inr(gap),
    delta=("Shortfall" if gap > 0 else "Target met / surplus"),
    delta_color=("inverse" if gap > 0 else "normal"),
)
c6.metric("Projected Final Annual Salary", inr(final_salary))

st.caption(
    "*Monthly take-home here means salary after the selected EPF/NPS "
    "contributions only. It excludes income tax and other payroll deductions."
)


# =========================================================
# INFLATION AND PRESENT VALUE
# =========================================================
st.divider()
st.subheader("💹 Future Value vs Today's Value")
v1, v2, v3 = st.columns(3)
v1.metric("Wealth in Future Rupees", inr(retirement_wealth))
v2.metric("Wealth in Today's Purchasing Power", inr(real_wealth_today))
v3.metric("Present Value at Discount Rate", inr(present_value_wealth))

pv1, pv2 = st.columns(2)
pv1.metric("Target in Today's Purchasing Power", inr(real_target_today))
pv2.metric("Present-Value Target Gap", inr(present_value_gap))
st.caption(
    f"Today's purchasing power uses {inflation_pct:.1f}% annual inflation. "
    f"Present values use {discount_rate_pct:.1f}% annual discounting. "
    "These are distinct measures, displayed separately."
)


# =========================================================
# HOUSING RISK
# =========================================================
st.divider()
st.subheader("🏠 Housing Affordability")
h1, h2, h3 = st.columns(3)
h1.metric("Monthly EMI", inr(emi))
h2.metric(
    "EMI / Monthly Take-Home",
    f"{emi_ratio:.1%}" if emi_ratio is not None else "N/A",
)
h3.metric("Housing Risk Indicator", risk_label)
st.write(risk_description)
if monthly_take_home <= 0:
    st.warning(
        "The selected contribution percentages leave no positive monthly "
        "take-home in this simplified calculation. The housing risk indicator "
        "is therefore marked high/unavailable."
    )


# =========================================================
# RETIREMENT PROGRESS
# =========================================================
st.divider()
st.subheader("📍 Retirement Progress")
progress = retirement_wealth / required_wealth if required_wealth > 0 else 0.0
st.progress(min(1.0, max(0.0, progress)))
st.write(f"{progress:.1%} of the illustrative retirement wealth target is projected.")
if gap <= 0:
    st.success("Projected wealth meets or exceeds the selected target under these assumptions.")
else:
    st.info(f"{format_shortfall(gap)} against the selected retirement target.")


# =========================================================
# WECARE ESTIMATE
# =========================================================
st.divider()
st.subheader("💼 WeCare Plan — Illustrative Estimate")
wecare_annual_contribution = salary * WECARE_CONTRIBUTION_RATE
wecare_monthly_pension = (final_salary / 12) * WECARE_PENSION_RATE
wecare_commuted_value = (
    wecare_monthly_pension * 12 * WECARE_COMMUTATION_FACTOR
)

w1, w2, w3 = st.columns(3)
w1.metric("Illustrative Annual Contribution (10%)", inr(wecare_annual_contribution))
w2.metric("Estimated Monthly Pension", inr(wecare_monthly_pension))
w3.metric("Illustrative Commuted Value", inr(wecare_commuted_value))
st.caption(
    "This estimate assumes a contribution equal to 10% of current annual salary, "
    "a pension equal to 50% of projected final monthly salary, and a commutation "
    "factor of 13. These are model assumptions, not verified official scheme terms. "
    "Confirm the applicable scheme rules before relying on these figures."
)


# =========================================================
# SMART RECOMMENDATIONS
# =========================================================
st.divider()
st.subheader("💡 Smart Recommendations")
recommendations = []

if monthly_take_home <= 0:
    recommendations.append(
        "Review contribution settings because they leave no positive monthly take-home."
    )

if emi_ratio is None:
    recommendations.append(
        "Housing affordability cannot be assessed reliably until calculated take-home is positive."
    )
elif emi_ratio >= 0.60:
    recommendations.append(
        "EMI is at least 60% of calculated take-home. Review housing affordability and other expenses."
    )
elif emi_ratio >= 0.40:
    recommendations.append(
        "Housing costs are moderately high relative to calculated take-home."
    )
else:
    recommendations.append(
        "EMI is below 40% of calculated take-home under this simplified measure."
    )

if nps_pct < RECOMMENDED_NPS_RATE:
    recommendations.append(
        f"Explore the impact of increasing NPS from {nps_pct}% to "
        f"{RECOMMENDED_NPS_RATE}% on take-home and projected wealth."
    )

if gap > 0:
    recommendations.append(
        f"The current projection is below the illustrative target by {inr(gap)}."
    )
else:
    recommendations.append(
        "The projection meets or exceeds the illustrative target under these assumptions."
    )

if years < 15:
    recommendations.append(
        "Retirement is fewer than 15 years away. Review contribution levels and assumptions carefully."
    )

for recommendation in recommendations:
    st.write(f"• {recommendation}")


# =========================================================
# CURRENT VS RECOMMENDED PLAN
# =========================================================
st.divider()
st.subheader("🎯 Current vs Recommended")
recommended_nps = max(nps_pct, RECOMMENDED_NPS_RATE)

recommended_projection = project_retirement(
    current_salary=salary,
    years=years,
    epf_pct=epf_pct,
    nps_pct=recommended_nps,
    salary_growth=salary_growth,
    investment_return=selected_return,
    current_age=int(age),
)
recommended_wealth = recommended_projection["wealth"]
recommended_monthly_take_home = current_monthly_salary * (
    1 - (epf_pct + recommended_nps) / 100
)
recommended_emi_ratio = (
    emi / recommended_monthly_take_home
    if recommended_monthly_take_home > 0
    else None
)
recommended_score = readiness_score(
    wealth=recommended_wealth,
    target_wealth=required_wealth,
    emi_ratio=recommended_emi_ratio,
    epf_pct=epf_pct,
    nps_pct=recommended_nps,
)
wealth_gain = recommended_wealth - retirement_wealth
monthly_take_home_reduction = current_monthly_salary * (
    recommended_nps - nps_pct
) / 100

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Current Plan")
    st.metric("NPS Contribution", f"{nps_pct}%")
    st.metric("Projected Retirement Wealth", inr(retirement_wealth))
    st.metric("Readiness Score", f"{score}/100")
with col2:
    st.markdown("### Recommended Contribution Plan")
    st.metric("NPS Contribution", f"{recommended_nps}%")
    st.metric("Projected Retirement Wealth", inr(recommended_wealth), delta=inr(wealth_gain))
    st.metric("Readiness Score", f"{recommended_score}/100")

st.info(
    f"Changing NPS from {nps_pct}% to {recommended_nps}% changes calculated "
    f"monthly take-home by approximately {inr(monthly_take_home_reduction)} "
    f"and projected retirement wealth by {inr(wealth_gain)} over {years} years, "
    "holding salary growth and investment return assumptions constant. "
    "This is a simplified projection, not a recommendation that 8% is suitable for everyone."
)
if recommended_nps == nps_pct:
    st.caption("NPS is already at or above the illustrative 8% threshold, so no increase is applied.")


# =========================================================
# INDEPENDENT SCENARIO COMPARISON
# =========================================================
st.divider()
st.subheader("📊 Scenario Comparison")
scenario_rows = []
for scenario_name, scenario_return in SCENARIO_RETURNS.items():
    scenario_projection = project_retirement(
        current_salary=salary,
        years=years,
        epf_pct=epf_pct,
        nps_pct=nps_pct,
        salary_growth=salary_growth,
        investment_return=scenario_return,
        current_age=int(age),
    )
    scenario_wealth = scenario_projection["wealth"]
    scenario_rows.append(
        {
            "Scenario": scenario_name,
            "Assumed Annual Return (%)": scenario_return * 100,
            "Projected Retirement Wealth": scenario_wealth,
            "Target Wealth": required_wealth,
            "Shortfall / Surplus": required_wealth - scenario_wealth,
            "Today's Purchasing Power": scenario_wealth / ((1 + inflation) ** years),
        }
    )

scenario_df = pd.DataFrame(scenario_rows)
fig = px.bar(
    scenario_df,
    x="Scenario",
    y="Projected Retirement Wealth",
    color="Scenario",
    text="Projected Retirement Wealth",
    hover_data=[
        "Assumed Annual Return (%)",
        "Target Wealth",
        "Shortfall / Surplus",
        "Today's Purchasing Power",
    ],
    title="Projected Retirement Wealth Under Independent Return Scenarios",
)
fig.update_traces(
    texttemplate="₹%{text:,.0f}",
    textposition="outside",
    cliponaxis=False,
)
fig.update_layout(
    showlegend=False,
    xaxis_title="Investment Return Scenario",
    yaxis_title="Projected Wealth (₹)",
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    scenario_df.style.format(
        {
            "Assumed Annual Return (%)": "{:.1f}%",
            "Projected Retirement Wealth": "₹{:,.0f}",
            "Target Wealth": "₹{:,.0f}",
            "Shortfall / Surplus": "₹{:,.0f}",
            "Today's Purchasing Power": "₹{:,.0f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# YEAR-BY-YEAR PROJECTION
# =========================================================
st.divider()
with st.expander("📈 View Year-by-Year Projection"):
    projection_df = pd.DataFrame(current_projection["records"])
    if not projection_df.empty:
        st.dataframe(
            projection_df.style.format(
                {
                    "Projected Annual Salary": "₹{:,.0f}",
                    "Annual EPF/NPS Contribution": "₹{:,.0f}",
                    "Opening Balance": "₹{:,.0f}",
                    "Investment Growth": "₹{:,.0f}",
                    "Closing Balance": "₹{:,.0f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        balance_chart = px.line(
            projection_df,
            x="Age",
            y="Closing Balance",
            markers=True,
            title="Projected Retirement Wealth Accumulation",
        )
        balance_chart.update_layout(
            xaxis_title="Age",
            yaxis_title="Projected Wealth (₹)",
        )
        st.plotly_chart(balance_chart, use_container_width=True)


# =========================================================
# MODEL ASSUMPTIONS AND LIMITATIONS
# =========================================================
st.divider()
with st.expander("📋 Assumptions and Model Limitations"):
    st.markdown(
        f"""
        **Selected inputs and assumptions**

        - Current age: {age}
        - Retirement age: {retirement_age}
        - Projection period: {years} years
        - Selected scenario: {scenario} ({selected_return:.1%} assumed annual return)
        - Annual salary growth: {salary_growth_pct:.1f}%
        - Annual inflation: {inflation_pct:.1f}%
        - Discount rate: {discount_rate_pct:.1f}%
        - EPF contribution: {epf_pct}% of projected salary
        - NPS contribution: {nps_pct}% of projected salary
        - Retirement target heuristic: {RETIREMENT_TARGET_MULTIPLE} times projected final annual salary

        **Important limitations**

        1. A single assumed return is applied to the combined EPF/NPS contribution pool. Actual products have different returns, risks, fees and rules.
        2. Salary growth and investment returns are assumed constant every year; real outcomes vary.
        3. Contributions are assumed to be invested at the end of each year.
        4. The target of 20 times projected final annual salary is a heuristic, not a personalised retirement-expense valuation.
        5. The readiness score is a custom illustrative score, not a standard actuarial or regulatory measure.
        6. Monthly take-home excludes income tax and other payroll deductions.
        7. Inflation-adjusted values and discounted present values answer different questions and are displayed separately.
        8. WeCare results depend on the assumptions shown in that section; they are not verified official scheme benefits.
        9. Taxes, withdrawals, limits, fees, volatility and scheme-specific contribution rules are not modelled separately.
        """
    )

st.caption(
    "Smart Retirement Decision Engine | Educational project | "
    "Illustrative estimates only — not financial advice."
)
