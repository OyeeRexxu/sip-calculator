# swp_calculator.py
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SWP Calculator", page_icon="💸", layout="centered")

st.title("💸 SWP Calculator (Percent Withdrawal)")
st.caption("Withdraw a fixed % of corpus per year (applied monthly). Supports delayed withdrawal start and start/end-of-month timing.")

# ---------------- Inputs ----------------
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        initial_corpus = st.number_input(
            "Initial Investment / Basic (₹)", min_value=0, value=1_000_000, step=10_000, format="%d"
        )
        exp_return_pa = st.number_input(
            "Expected Annual Return (%)", min_value=0.0, value=10.0, step=0.1, format="%.2f"
        )
        tenure_years = st.slider("Planned Tenure (years)", min_value=1, max_value=50, value=20)
        withdraw_start_year = st.number_input(
            "Withdrawal starts from Year",
            min_value=1, max_value=50, value=1,
            help="Example: 1 = start immediately; 3 = grow for 2 years, start withdrawals in year 3."
        )
    with col2:
        withdraw_pct_pa = st.number_input(
            "Withdrawal Rate (% per year)", min_value=0.0, value=6.0, step=0.1, format="%.2f"
        )
        withdraw_timing = st.selectbox(
            "Withdrawal Timing",
            ["Start of month", "End of month"],
            help="When the monthly withdrawal is applied relative to growth."
        )
        show_table = st.toggle("Show monthly schedule & chart", value=True)

st.divider()

# ---------------- Validate inputs & compute ----------------
try:
    if withdraw_start_year > tenure_years:
        st.error("⚠️ 'Withdrawal starts from Year' cannot be greater than the total tenure. Reduce the start year or increase tenure.")
        st.stop()

    months = int(tenure_years * 12)
    r_m = float(exp_return_pa) / 100.0 / 12.0                 # monthly return rate
    w_m = float(withdraw_pct_pa) / 100.0 / 12.0               # monthly withdrawal rate
    start_month = (int(withdraw_start_year) - 1) * 12 + 1     # 1, 13, 25, ...

    rows = []
    balance = float(initial_corpus)
    total_withdrawn = 0.0
    months_simulated = 0

    for m in range(1, months + 1):
        opening = balance
        if opening <= 0:
            rows.append({
                "Month": m,
                "Opening Corpus (₹)": 0.0,
                "Withdrawal (₹)": 0.0,
                "Growth (₹)": 0.0,
                "Closing Corpus (₹)": 0.0,
                "Phase": "Depleted"
            })
            months_simulated = m
            break

        withdrawals_active = (m >= start_month)

        if not withdrawals_active:
            # Growth-only phase
            withdrawal = 0.0
            growth = opening * r_m
            balance = opening + growth
            phase = "Growth only"
        else:
            if withdraw_timing == "Start of month":
                # Withdraw first, then grow
                withdrawal = opening * w_m
                after_withdraw = opening - withdrawal
                growth = after_withdraw * r_m
                balance = after_withdraw + growth
            else:
                # Grow first, then withdraw from grown corpus
                growth = opening * r_m
                mid = opening + growth
                withdrawal = mid * w_m
                balance = mid - withdrawal
            total_withdrawn += withdrawal
            phase = "Withdrawal"

        months_simulated = m
        rows.append({
            "Month": m,
            "Opening Corpus (₹)": round(opening, 2),
            "Withdrawal (₹)": round(withdrawal, 2),
            "Growth (₹)": round(growth, 2),
            "Closing Corpus (₹)": round(balance, 2),
            "Phase": phase
        })

        if balance <= 0:
            break

    df = pd.DataFrame(rows)
    ending_corpus = float(df["Closing Corpus (₹)"].iloc[-1]) if not df.empty else 0.0

    # ---------------- KPIs ----------------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Initial Investment (₹)", f"₹ {initial_corpus:,.0f}")
    k2.metric("Total Withdrawn (₹)", f"₹ {total_withdrawn:,.0f}")
    k3.metric("Ending Corpus (₹)", f"₹ {ending_corpus:,.0f}")
    k4.metric("Months Simulated", f"{months_simulated:,}")

    # ---------------- Summary line ----------------
    if ending_corpus <= 0:
        st.warning(
            f"Corpus **exhausted by month {months_simulated}** at a {withdraw_pct_pa:.2f}% annual withdrawal rate "
            f"(withdrawals starting Year {int(withdraw_start_year)})."
        )
    else:
        st.info(
            f"Corpus survives the full horizon: **₹ {total_withdrawn:,.0f}** withdrawn, "
            f"**₹ {ending_corpus:,.0f}** remaining. "
            f"(Withdrawals start Year {int(withdraw_start_year)}, timing: **{withdraw_timing}**.)"
        )

    # ---------------- Table & Chart ----------------
    if show_table and not df.empty:
        st.subheader("Monthly Schedule")
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Month": st.column_config.NumberColumn(format="%d"),
                "Opening Corpus (₹)": st.column_config.NumberColumn(format="₹ %,.2f"),
                "Withdrawal (₹)": st.column_config.NumberColumn(format="₹ %,.2f"),
                "Growth (₹)": st.column_config.NumberColumn(format="₹ %,.2f"),
                "Closing Corpus (₹)": st.column_config.NumberColumn(format="₹ %,.2f"),
                "Phase": st.column_config.TextColumn(),
            },
        )

        st.subheader("Corpus & Withdrawals Over Time")
        melted = df.melt(id_vars=["Month"], value_vars=["Closing Corpus (₹)", "Withdrawal (₹)"],
                         var_name="Series", value_name="Amount")
        fig = px.line(
            melted, x="Month", y="Amount", color="Series",
            labels={"Amount": "Amount (₹)"}
        )
        fig.update_yaxes(tickformat=",.0f")
        fig.update_traces(hovertemplate="Month %{x}: ₹ %{y:,.2f}<extra></extra>")
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Schedule (CSV)", csv, "swp_schedule.csv", "text/csv")

except Exception as e:
    # Surface any hidden errors in the UI so the page never looks "empty"
    st.error(f"Unexpected error: {e}")
    st.exception(e)
