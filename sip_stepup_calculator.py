import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------- CONFIGURATION ----------------
st.set_page_config(
    page_title="Highcrest SIP Calculator",
    page_icon="H",
    layout="wide"
)

# ---------------- THEME & STYLING ----------------
# Refined "Luxury Bronze" Palette
# Primary Gold:   #BB9D63 (Metallic Gold - Brighter)
# Secondary Gold: #C5A059
# Background:     Gradient #483C32 (Taupe) -> #1E1812
# Cards:          Glassy Dark Brown
# Text:           White & Warm Beige

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;700&display=swap');

    /* Global App Background - "Curtain" Gradient */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #4D4134 0%, #1F1913 100%);
        color: #F0EAD6; /* Eggshell/Parchment */
        font-family: 'Montserrat', sans-serif;
    }

    /* Custom Header */
    .brand-header {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        color: #BB9D63;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 5px;
        text-align: center;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }
    .brand-sub {
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        color: #E0DACC;
        text-align: center;
        margin-bottom: 30px;
        font-size: 0.9rem;
        letter-spacing: 1px;
    }

    /* Input Styling */
    .stInput > label, .stSlider > label, .stSelectbox > label, .stNumberInput > label {
        color: #ffffff !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.75rem;
    }
    
    /* Input Fields Background - Making them blend */
    input.st-ai, div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        color: white !important;
    }
    
    /* Input Containers - "Glass" Effect */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div {
        background-color: rgba(40, 30, 20, 0.6) !important; /* Semi-transparent brown */
        border: 1px solid rgba(212, 175, 55, 0.2) !important;
        backdrop-filter: blur(10px);
        border-radius: 4px;
    }

    /* Metric Cards - Minimalist Luxury */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(212, 175, 55, 0.15) !important;
        padding: 15px;
        border-radius: 4px;
    }
    
    /* Metric Typography */
    div[data-testid="stMetric"] label[data-testid="stMetricLabel"] {
        color: #A89F91 !important; /* Warm Gray */
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 1px;
    }
        color: #FDFBF7 !important; /* Off-White */
        font-family: 'Montserrat', sans-serif;
        font-weight: 500;
        font-size: 1.2rem !important; /* Smaller font to fit values */
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.2); /* Slight Gold Glow */
    }

    /* Active Elements (Sliders/Checks) */
    div[role="slider"] {
        background-color: #BB9D63 !important;
    }
    /* Slider Filled Track */
    div[data-baseweb="slider"] > div > div > div:first-child {
        background-color: #BB9D63 !important;
    }
    /* Slider Value Label (The number above the slider) */
    div[data-baseweb="slider"] div {
        color: #BB9D63 !important;
    }
    
    /* Divider */
    hr {
        border-color: #BB9D63 !important;
        opacity: 0.2;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5 {
        color: #F0EAD6 !important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 500;
    }
    
    /* Hide Streamlit components */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div style="text-align: center; margin-bottom: 2.5rem;">', unsafe_allow_html=True)
st.markdown('<h2 class="brand-header">Highcrest</h2>', unsafe_allow_html=True)
st.markdown('<p class="brand-sub">GENERATIONAL WEALTH PLANNER</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- LAYOUT ----------------
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.markdown("##### PARAMETERS")
    with st.container(border=True):
        lump_sum = st.number_input("Lump-sum Investment (₹)", min_value=0, value=100000, step=5000, format="%d")
        monthly_sip = st.number_input("Base Monthly SIP (₹)", min_value=0, value=10000, step=500, format="%d")
        years = st.slider("Tenure (years)", min_value=1, max_value=40, value=15)
        annual_return_pct = st.number_input("Expected Annual Return (%)", min_value=0.0, value=12.0, step=0.1, format="%.2f")
        
        st.markdown("---")
        
        stepup_pct = st.number_input("SIP Step-up per Year (%)", min_value=0.0, value=10.0, step=0.5, format="%.2f")
        lump_sum_timing = st.selectbox("Lump-sum Timing", ["Invest today (t=0)", "Invest after 1 month"], index=0)
        invest_at_beginning = st.toggle("SIP at beginning of each month (Annuity Due)", value=False)
        show_monthly = st.toggle("Show monthly table & chart", value=True)

# ---------------- CALCULATION LOGIC ----------------
months = years * 12
r = (annual_return_pct / 100.0) / 12.0
g = stepup_pct / 100.0

def format_indian_currency(n):
    n = float(n)
    if n >= 10000000:
        return f"₹ {n/10000000:.2f} Cr"
    elif n >= 100000:
        return f"₹ {n/100000:.2f} L"
    else:
        return f"₹ {n:,.0f}"

def month_sip_amount(m: int) -> float:
    yr_idx = (m - 1) // 12
    return monthly_sip * ((1 + g) ** yr_idx)

balance = 0.0
rows = []
total_sip_contrib = 0.0
total_lumpsum_contrib = 0.0

for m in range(1, months + 1):
    sip_amt = month_sip_amount(m)
    if invest_at_beginning:
        balance += sip_amt
        total_sip_contrib += sip_amt
    if m == 1 and lump_sum > 0 and lump_sum_timing == "Invest today (t=0)":
        balance += lump_sum
        total_lumpsum_contrib += lump_sum
    if m == 2 and lump_sum > 0 and lump_sum_timing == "Invest after 1 month":
        balance += lump_sum
        total_lumpsum_contrib += lump_sum
    if r > 0:
        balance *= (1 + r)
    if not invest_at_beginning:
        balance += sip_amt
        total_sip_contrib += sip_amt
    rows.append({
        "Month": m,
        "SIP": sip_amt,
        "Invested": total_sip_contrib + total_lumpsum_contrib,
        "Value": balance
    })

df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Month","SIP","Invested","Value"])
principal = float(df["Invested"].iloc[-1]) if not df.empty else float(lump_sum)
future_value = float(df["Value"].iloc[-1]) if not df.empty else principal
returns = max(future_value - principal, 0.0)

# ---------------- OUTPUT DISPLAY ----------------
with col_output:
    st.markdown("##### PROJECTION SUMMARY")
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Lump-sum Invested", format_indian_currency(total_lumpsum_contrib))
    k2.metric("Total SIP Invested", format_indian_currency(total_sip_contrib))
    k3.metric("Estimated Value", format_indian_currency(future_value))
    k4.metric("Wealth Gain (Returns)", format_indian_currency(returns))

    st.markdown("") # Spacer

    # Charts Layout
    c1, c2 = st.columns([1, 1.8])
    
    with c1:
        st.caption("Principal vs Returns".upper())
        pie_data = [{"Type": "Principal", "Value": principal}, {"Type": "Returns", "Value": returns}]
        fig_pie = px.pie(
            pie_data, names="Type", values="Value", hole=0.7,
            color="Type",
            color_discrete_map={"Principal": "#6B5B45", "Returns": "#BB9D63"} # muted brown vs bright gold
        )
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(
            margin=dict(t=20, b=50, l=40, r=40),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F0EAD6", family="Montserrat", size=10),
            showlegend=True,
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        if show_monthly and not df.empty:
            st.caption("Monthly Growth".upper())
            line_fig = px.area(
                df, x="Month", y=["Invested", "Value"],
                labels={"value": "Amount (₹)", "variable": "Metric"},
                color_discrete_sequence=["#5D4D3B", "#BB9D63"] # Dark Bronze vs Gold
            )
            line_fig.update_layout(
                margin=dict(t=10, b=0, l=0, r=0),
                height=300,
                legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A89F91", family="Montserrat", size=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(212, 175, 55, 0.1)"),
                hovermode="x unified"
            )
            st.plotly_chart(line_fig, use_container_width=True)

    with st.expander("Show monthly table & chart"):
        st.dataframe(df, hide_index=True, use_container_width=True)
