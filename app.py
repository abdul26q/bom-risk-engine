import streamlit as st
import pandas as pd
import concurrent.futures
import io
from db import init_db, get_cached_component, cache_component
from decoders import sanitize_mpn, decode_passive_component
from search_engine import search_web_fallback

# Initialize Local Database Cache
init_db()

st.set_page_config(page_title="Hybrid BOM Engine", page_icon="⚡", layout="wide")

st.title("⚡ Multi-Layer Hybrid BOM Engine")
st.caption("Combines SQLite Local Cache, Algorithmic Passive Parsers, APIs, and Web Search Fallbacks.")

uploaded_file = st.sidebar.file_uploader("Upload BOM CSV", type=["csv"])

def resolve_component(mpn_raw):
    mpn = str(mpn_raw).strip()
    if not mpn or mpn.lower() in ["nan", "none", "null"]:
        return None

    # Layer 1: Local SQLite DB Cache
    cached = get_cached_component(mpn)
    if cached:
        return cached

    # Layer 2: Passive Component Regex Parser
    decoded = decode_passive_component(mpn)
    if decoded:
        cache_component(decoded)
        return decoded

    # Layer 3: Custom Part Bypasses
    if "CUSTOM" in mpn.upper() or "PCB" in mpn.upper():
        custom = {
            "MPN": mpn, "Manufacturer": "Custom", "Category": "Custom Board",
            "Description": "Non-catalog custom component", "Lifecycle_Status": "Custom Part",
            "Package": "N/A", "Max_Voltage_V": "N/A", "Max_Current_A": "N/A",
            "Price_USD": "N/A", "Source": "System Rule"
        }
        cache_component(custom)
        return custom

    # Layer 4: Search Engine Fallback
    search_res = search_web_fallback(mpn)
    if search_res:
        cache_component(search_res)
        return search_res

    # Unresolved Part
    unresolved = {
        "MPN": mpn, "Manufacturer": "N/A", "Category": "Uncategorized",
        "Description": "Unresolved across search layers", "Lifecycle_Status": "Unknown",
        "Package": "N/A", "Max_Voltage_V": "N/A", "Max_Current_A": "N/A",
        "Price_USD": "N/A", "Source": "Unresolved"
    }
    return unresolved

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)
    
    # Auto-detect MPN Column Header
    mpn_col = None
    for col in raw_df.columns:
        if str(col).strip().upper() in ["MPN", "PART_NUMBER", "PARTNUMBER", "MANUFACTURER_PART_NUMBER"]:
            mpn_col = col
            break
            
    if mpn_col:
        st.write(f"Detected Part Number Column: **{mpn_col}**")
        if st.sidebar.button("🚀 Run Engine Analysis", type="primary"):
            mpn_list = raw_df[mpn_col].dropna().tolist()
            results = []

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Parallel Multi-Threaded Execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                future_to_mpn = {executor.submit(resolve_component, mpn): mpn for mpn in mpn_list}
                completed = 0
                
                for future in concurrent.futures.as_completed(future_to_mpn):
                    res = future.result()
                    if res:
                        results.append(res)
                    completed += 1
                    progress_bar.progress(completed / len(mpn_list))
                    status_text.text(f"Processed {completed}/{len(mpn_list)} items concurrently...")

            progress_bar.empty()
            status_text.empty()

            processed_df = pd.DataFrame(results)
            st.subheader("📋 Enriched Output Table")
            st.dataframe(processed_df, use_container_width=True)

            csv_buffer = io.StringIO()
            processed_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Enriched BOM CSV",
                data=csv_buffer.getvalue(),
                file_name="Enriched_BOM_Output.csv",
                mime="text/csv"
            )
    else:
        st.error("⚠️ Could not find a valid 'MPN' or 'Part Number' column in CSV headers.")
