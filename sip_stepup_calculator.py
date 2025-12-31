# sip_stepup_calculator.py
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SIP + Step-up + Lump-sum Calculator", page_icon="💹", layout="centered")

st.title("💹 SIP Calculator with Lump-sum & Yearly Step-up")
st.caption("Monthly SIP grows by a fixed % each year. Choose timing assumptions for precise estimates.")

# ---------------- Inputs ----------------
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        lump_sum = st.number_input("Lump-sum Investment (₹)", min_value=0, value=100000, step=5000, format="%d")
        monthly_sip = st.number_input("Base Monthly SIP (₹)", min_value=0, value=10000, step=500, format="%d")
        years = st.slider("Tenure (years)", min_value=1, max_value=40, value=15)
        annual_return_pct = st.number_input("Expected Annual Return (%)", min_value=0.0, value=12.0, step=0.1, format="%.2f")
    with col2:
        stepup_pct = st.number_input(
            "SIP Step-up per Year (%)",
            min_value=0.0,
            value=10.0,
            step=0.5,
            format="%.2f"
        )
        invest_at_beginning = st.toggle("SIP at beginning of each month (Annuity Due)", value=False)
        lump_sum_timing = st.selectbox(
            "Lump-sum Timing",
            ["Invest today (t=0)", "Invest after 1 month"],
            index=0,
            help="When to apply the lump-sum contribution."
        )
        show_monthly = st.toggle("Show monthly table & chart", value=True)

st.divider()

# ---------------- Core Calculations ----------------
months = years * 12
r = (annual_return_pct / 100.0) / 12.0   # monthly rate
g = stepup_pct / 100.0                   # annual step-up rate

def month_sip_amount(m: int) -> float:
    """
    SIP amount for month m (1-indexed), stepping up annually.
    Step-up applies at months 1, 13, 25, ...
    """
    yr_idx = (m - 1) // 12
    return monthly_sip * ((1 + g) ** yr_idx)

balance = 0.0
rows = []
total_sip_contrib = 0.0
total_lumpsum_contrib = 0.0

for m in range(1, months + 1):
    sip_amt = month_sip_amount(m)

    # SIP at start?
    if invest_at_beginning:
        balance += sip_amt
        total_sip_contrib += sip_amt

    # Lump-sum timing
    if m == 1 and lump_sum > 0 and lump_sum_timing == "Invest today (t=0)":
        balance += lump_sum
        total_lumpsum_contrib += lump_sum
    if m == 2 and lump_sum > 0 and lump_sum_timing == "Invest after 1 month":
        balance += lump_sum
        total_lumpsum_contrib += lump_sum

    # Monthly growth
    if r > 0:
        balance *= (1 + r)

    # SIP at end?
    if not invest_at_beginning:
        balance += sip_amt
        total_sip_contrib += sip_amt

    rows.append(
        {
            "Month": m,
            "SIP this month (₹)": round(sip_amt, 2),
            "Cumulative SIP (₹)": round(total_sip_contrib, 2),
            "Cumulative Lump-sum (₹)": round(total_lumpsum_contrib, 2),
            "Total Principal (₹)": round(total_sip_contrib + total_lumpsum_contrib, 2),
            "Estimated Value (₹)": round(balance, 2),
        }
    )

df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["Month","SIP this month (₹)","Cumulative SIP (₹)","Cumulative Lump-sum (₹)","Total Principal (₹)","Estimated Value (₹)"]
)

principal = float(df["Total Principal (₹)"].iloc[-1]) if not df.empty else float(lump_sum)
future_value = float(df["Estimated Value (₹)"].iloc[-1]) if not df.empty else principal
returns = max(future_value - principal, 0.0)

# ---------------- KPIs ----------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Lump-sum Invested", f"₹ {total_lumpsum_contrib:,.0f}")
k2.metric("Total SIP Invested", f"₹ {total_sip_contrib:,.0f}")
k3.metric("Estimated Value", f"₹ {future_value:,.0f}")
k4.metric("Wealth Gain (Returns)", f"₹ {returns:,.0f}")

# ---------------- Pie: Principal vs Returns ----------------
st.subheader("Principal vs Returns")
pie_data = [
    {"Component": "Principal", "Amount": principal},
    {"Component": "Returns", "Amount": returns},
]
fig_pie = px.pie(pie_data, names="Component", values="Amount", hole=0.45)
fig_pie.update_traces(textposition="inside", textinfo="label+percent")
fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
st.plotly_chart(fig_pie, use_container_width=True)

# ---------------- Line: Growth over time ----------------
if show_monthly and not df.empty:
    st.subheader("Monthly Growth")
    st.dataframe(df, hide_index=True, use_container_width=True)

    line_fig = px.line(
        df,
        x="Month",
        y=["Total Principal (₹)", "Estimated Value (₹)"],
        labels={"value": "Amount (₹)", "variable": "Series"},
    )
    line_fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(line_fig, use_container_width=True)

    # Download CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Monthly Schedule (CSV)", csv, "sip_schedule.csv", "text/csv")

# ---------------- Footer ----------------
st.caption(
    "Assumptions: SIP steps up once every 12 months by the specified percentage. "
    "Returns assume constant monthly compounding at the chosen annual rate. Actual market returns will vary."
)
