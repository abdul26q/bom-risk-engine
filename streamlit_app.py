import streamlit as st
import pandas as pd
import numpy as np
import io

# ==========================================
# 1. PAGE CONFIGURATION & STYLES
# ==========================================
st.set_page_config(
    page_title="BOM Risk & Obsolescence Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI polish
st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    .badge-active { color: #2e7d32; font-weight: bold; }
    .badge-nrnd { color: #f57f17; font-weight: bold; }
    .badge-eol { color: #c62828; font-weight: bold; }
    .badge-obsolete { color: #b71c1c; font-weight: bold; background-color: #ffebee; padding: 2px 6px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. MOCK DATABASE GENERATION
# ==========================================
@st.cache_data
def load_mock_component_catalog():
    """Generates a default catalog of 15 electronic components across categories."""
    catalog_data = {
        "MPN": [
            "IRF540N", "LM358P", "AMS1117-3.3", "STM32F103C8T6", "RC0805JR-0710KL",
            "2N7002", "NE555P", "LM7805CT", "ATmega328P-PU", "RC0603FR-07100KL",
            "FQP30N06L", "TL072CP", "LD1117V33", "ESP8266-EX", "MC33063AP"
        ],
        "Category": [
            "MOSFET", "Op-Amp", "LDO Regulator", "Microcontroller", "Resistor",
            "MOSFET", "Timer IC", "LDO Regulator", "Microcontroller", "Resistor",
            "MOSFET", "Op-Amp", "LDO Regulator", "Microcontroller", "DC-DC Converter"
        ],
        "Lifecycle_Status": [
            "Active", "Active", "NRND", "NRND", "Active",
            "Active", "EOL", "Active", "Obsolete", "Active",
            "EOL", "Active", "Active", "NRND", "Obsolete"
        ],
        "Package": [
            "TO-220", "DIP-8", "SOT-223", "LQFP-48", "0805",
            "SOT-23", "DIP-8", "TO-220", "DIP-28", "0603",
            "TO-220", "DIP-8", "TO-220", "QFN-32", "DIP-8"
        ],
        "Max_Voltage_V": [100.0, 32.0, 15.0, 3.6, 150.0, 60.0, 18.0, 35.0, 5.5, 75.0, 60.0, 36.0, 15.0, 3.6, 40.0],
        "Max_Current_A": [33.0, 0.05, 1.0, 0.15, 0.125, 0.115, 0.2, 1.5, 0.04, 0.1, 32.0, 0.01, 0.8, 0.17, 1.5],
        "Lead_Time_Weeks": [12, 8, 26, 52, 4, 6, 30, 10, 0, 4, 36, 8, 14, 24, 0],
        "Substitute_MPN": [
            "STP36NF06L", "OPA2991P", "NCP1117ST33T3G", "STM32G030C8T6", "AC0805JR-0710KL",
            "BSS138", "TLC555IP", "MC7805CTG", "ATmega328PB-PU", "AC0603FR-07100KL",
            "STP40NF06L", "TL082CP", "IFX1117MEV33", "ESP32-C3", "NCV33063AVDR2G"
        ],
        "Substitute_Package": [
            "TO-220", "DIP-8", "SOT-223", "LQFP-48", "0805",
            "SOT-23", "DIP-8", "TO-220", "DIP-28", "0603",
            "TO-220", "DIP-8", "TO-220", "QFN-32", "SOIC-8"
        ],
        "Substitute_Match_Score": [98, 92, 95, 88, 100, 96, 90, 99, 85, 100, 94, 97, 95, 78, 82],
        "Price_USD": [1.25, 0.45, 0.30, 3.50, 0.01, 0.15, 0.50, 0.80, 2.10, 0.01, 1.10, 0.60, 0.55, 1.80, 0.40]
    }
    return pd.DataFrame(catalog_data)


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def generate_sample_bom():
    """Generates a sample uploaded BOM CSV for demo purposes."""
    sample_bom = pd.DataFrame({
        "Reference_Designator": ["Q1", "U1", "VR1", "U2", "R1", "U3", "U4", "R2"],
        "MPN": [
            "IRF540N", "LM358P", "AMS1117-3.3", "STM32F103C8T6", 
            "RC0805JR-0710KL", "ATmega328P-PU", "MC33063AP", "RC0603FR-07100KL"
        ],
        "Quantity": [2, 1, 1, 1, 10, 1, 2, 5]
    })
    return sample_bom

def style_lifecycle(val):
    """Applies color styling based on the Lifecycle status."""
    if val == "Active":
        return "color: #2e7d32; font-weight: bold;"
    elif val == "NRND":
        return "color: #f57f17; font-weight: bold;"
    elif val in ["EOL", "Obsolete"]:
        return "color: #c62828; font-weight: bold; background-color: #ffebee;"
    return ""


# ==========================================
# 4. SIDEBAR & DATA LOADING
# ==========================================
st.sidebar.title("🛠️ BOM Control Panel")
st.sidebar.markdown("Upload a custom BOM or test with sample data.")

# Load component catalog (acts as our central reference database)
catalog_df = load_mock_component_catalog()

# Sidebar input controls
uploaded_file = st.sidebar.file_uploader("Upload BOM CSV", type=["csv"])
use_demo_bom = st.sidebar.button("📦 Load Sample Demo BOM", use_container_width=True)

# Session state initialization for demo BOM toggle
if "use_demo" not in st.session_state:
    st.session_state.use_demo = False

if use_demo_bom:
    st.session_state.use_demo = True

# Process uploaded BOM or default sample
if uploaded_file is not None:
    raw_bom = pd.read_csv(uploaded_file)
    st.session_state.use_demo = False
elif st.session_state.use_demo:
    raw_bom = generate_sample_bom()
else:
    raw_bom = generate_sample_bom()

# Merge incoming BOM with Catalog database on MPN
processed_bom = pd.merge(raw_bom, catalog_df, on="MPN", how="left")

# Fallback for MPNs not present in the catalog
processed_bom["Lifecycle_Status"] = processed_bom["Lifecycle_Status"].fillna("Unknown")


# ==========================================
# 5. DASHBOARD HEADER & METRICS
# ==========================================
st.title("⚡ BOM Risk & Component Obsolescence Engine")
st.markdown("Analyze supply chain health, flag end-of-life components, and identify drop-in substitutes.")

# Compute key metrics
total_line_items = len(processed_bom)
active_count = (processed_bom["Lifecycle_Status"] == "Active").sum()
high_risk_count = processed_bom["Lifecycle_Status"].isin(["EOL", "Obsolete"]).sum()

# Health Score calculation: 100 - (High Risk / Total Items * 100)
health_score = int(max(0, 100 - ((high_risk_count / total_line_items) * 100))) if total_line_items > 0 else 100

# Display Metrics Cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Line Items", total_line_items)
c2.metric("Active Components", active_count, delta=f"{int(active_count/total_line_items*100)}%")
c3.metric("High Risk / Obsolete", high_risk_count, delta=f"-{high_risk_count}", delta_color="inverse")
c4.metric("BOM Health Score", f"{health_score}%")

st.markdown("---")


# ==========================================
# 6. MAIN INTERACTIVE TABLE
# ==========================================
st.subheader("📋 BOM Analysis Table")

# Display styled table
styled_df = processed_bom.style.map(style_lifecycle, subset=["Lifecycle_Status"])
st.dataframe(
    styled_df,
    column_config={
        "Price_USD": st.column_config.NumberColumn("Unit Price ($)", format="$%.2f"),
        "Substitute_Match_Score": st.column_config.ProgressColumn(
            "Substitute Match",
            format="%d%%",
            min_value=0,
            max_value=100
        )
    },
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 7. SUBSTITUTE COMPARISON DRAWER
# ==========================================
st.markdown("---")
st.subheader("🔍 High-Risk Component Inspector & Pin-Compatible Replacement")

# Filter for items that need attention (EOL, Obsolete, NRND)
flagged_items = processed_bom[processed_bom["Lifecycle_Status"].isin(["EOL", "Obsolete", "NRND"])]

if not flagged_items.empty():
    selected_mpn = st.selectbox(
        "Select a Flagged Component to Inspect:",
        options=flagged_items["MPN"].tolist(),
        format_func=lambda x: f"{x} ({flagged_items[flagged_items['MPN'] == x]['Lifecycle_Status'].values[0]})"
    )

    # Get details for the selected component
    orig = processed_bom[processed_bom["MPN"] == selected_mpn].iloc[0]

    # Display side-by-side spec comparison
    col_left, col_right = st.columns(2)

    with col_left:
        st.error(f"🔴 Original: **{orig['MPN']}**")
        st.write(f"**Status:** {orig['Lifecycle_Status']}")
        st.write(f"**Package:** {orig['Package']}")
        st.write(f"**Max Voltage:** {orig['Max_Voltage_V']} V")
        st.write(f"**Max Current:** {orig['Max_Current_A']} A")
        st.write(f"**Lead Time:** {orig['Lead_Time_Weeks']} Weeks")
        st.write(f"**Unit Price:** ${orig['Price_USD']:.2f}")

    with col_right:
        st.success(f"🟢 Recommended Substitute: **{orig['Substitute_MPN']}**")
        match_score = int(orig['Substitute_Match_Score'])
        st.progress(match_score / 100, text=f"**Pin-to-Pin Match Score: {match_score}%**")
        st.write(f"**Package:** {orig['Substitute_Package']}")
        st.write(f"**Max Voltage:** {orig['Max_Voltage_V']} V *(Matches Spec)*")
        st.write(f"**Max Current:** {orig['Max_Current_A']} A *(Matches Spec)*")
        st.write(f"**Estimated Lead Time:** {max(2, orig['Lead_Time_Weeks'] - 8)} Weeks")
        st.write(f"**Unit Price:** ${(orig['Price_USD'] * 0.95):.2f}")

else:
    st.info("🎉 All components in the current BOM are active! No action required.")


# ==========================================
# 8. EXPORT FUNCTIONALITY
# ==========================================
st.markdown("---")
st.subheader("📥 Export Enriched BOM Data")

# Convert final DataFrame to CSV stream
csv_buffer = io.StringIO()
processed_bom.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="Download Risk Report & Substitutes (CSV)",
    data=csv_data,
    file_name="BOM_Risk_Report_And_Substitutes.csv",
    mime="text/csv",
    use_container_width=True
)
