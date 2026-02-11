"""
KSERC Truing-Up Decision Support System
==========================================
Unified Streamlit Application for SBU-G, SBU-T, and SBU-D

Features:
  - SBU selector in sidebar (G/T/D)
  - Dynamic page list based on selected SBU
  - Shared staff review UI pattern across all pages
  - Dashboard with traffic light summary
  - Aggregation view with drill-down
  - Complete integration of all 3 SBUs

Version: v6.0 - Complete D Integration
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Import unified modules
from sbu_base import SBU_Generation, SBU_Transmission, SBU_Distribution, create_sbu
from sbu_config import get_sbu_config, get_available_sbus

# Page configuration
st.set_page_config(
    page_title="KSERC Truing-Up DSS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_flag_emoji(flag):
    return {'GREEN': '✅', 'YELLOW': '⚠️', 'RED': '❌'}.get(flag, '⏳')

def get_review_status_indicator(result):
    status = result.get('staff_review_status', 'Pending')
    if status == 'Accepted':
        return '✅ Accepted'
    elif status == 'Overridden':
        return '🔄 Overridden'
    return '⏳ Pending Review'

def get_sbu_key():
    """Get current SBU key from session state."""
    return st.session_state.get('sbu_code', 'G')

def get_sbu():
    """Get current SBU instance from session state."""
    sbu_code = get_sbu_key()
    key = f'sbu_{sbu_code}'
    if key not in st.session_state:
        st.session_state[key] = create_sbu(sbu_code)
    return st.session_state[key]


# =============================================================================
# REUSABLE: STAFF REVIEW UI COMPONENT
# =============================================================================

def render_staff_review(result, idx, prefix):
    """
    Render the staff review section for a single heuristic result.
    Reused across ALL pages – eliminates massive duplication.

    Args:
        result: heuristic result dict
        idx: index for unique widget keys
        prefix: page prefix for unique widget keys (e.g., 'om', 'roe')
    """
    st.markdown("---")
    st.markdown("### 👤 Staff Review")

    is_primary = result.get('is_primary', True)
    heuristic_id = result['heuristic_id']

    if is_primary:
        review_option = st.radio(
            "Review Action:",
            ["Accept", "Override Flag", "Override Amount"],
            key=f"review_{prefix}_{heuristic_id}_{idx}",
            horizontal=True
        )
    else:
        review_option = st.radio(
            "Review Action:",
            ["Accept", "Add Remarks"],
            key=f"review_{prefix}_{heuristic_id}_{idx}",
            horizontal=True
        )

    if review_option == "Accept":
        staff_name = st.text_input("Reviewed By:", key=f"staff_{prefix}_{idx}")
        if st.button(f"✅ Accept {heuristic_id}", key=f"accept_{prefix}_{idx}"):
            if staff_name:
                result['staff_review_status'] = 'Accepted'
                result['reviewed_by'] = staff_name
                result['reviewed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"Accepted by {staff_name}")
                st.rerun()
            else:
                st.error("Please enter staff name")

    elif review_option == "Override Flag":
        col1, col2 = st.columns(2)
        with col1:
            new_flag = st.selectbox("New Flag:", ["GREEN", "YELLOW", "RED"], key=f"new_flag_{prefix}_{idx}")
        with col2:
            staff_name = st.text_input("Reviewed By:", key=f"staff_flag_{prefix}_{idx}")
        justification = st.text_area("Justification for Override:", key=f"just_flag_{prefix}_{idx}", height=100)
        if st.button(f"🔄 Override Flag for {heuristic_id}", key=f"override_flag_{prefix}_{idx}"):
            if staff_name and justification:
                result['staff_override_flag'] = new_flag
                result['staff_justification'] = justification
                result['staff_review_status'] = 'Overridden'
                result['reviewed_by'] = staff_name
                result['reviewed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"Flag overridden to {new_flag} by {staff_name}")
                st.rerun()
            else:
                st.error("Please provide staff name and justification")

    elif review_option == "Override Amount":
        col1, col2 = st.columns(2)
        with col1:
            new_amount = st.number_input(
                "New Approved Amount (₹ Cr):",
                value=float(result.get('allowable_value', 0)),
                step=0.01,
                key=f"new_amt_{prefix}_{idx}"
            )
            staff_name = st.text_input("Reviewed By:", key=f"staff_amt_{prefix}_{idx}")
        with col2:
            justification = st.text_area("Justification for Override:", key=f"just_amt_{prefix}_{idx}", height=100)
        if st.button(f"🔄 Override Amount for {heuristic_id}", key=f"override_amt_{prefix}_{idx}"):
            if staff_name and justification:
                result['staff_approved_amount'] = new_amount
                result['staff_justification'] = justification
                result['staff_review_status'] = 'Overridden'
                result['reviewed_by'] = staff_name
                result['reviewed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"Amount overridden to ₹{new_amount:.2f} Cr by {staff_name}")
                st.rerun()
            else:
                st.error("Please provide staff name and justification")

    elif review_option == "Add Remarks":
        col1, col2 = st.columns(2)
        with col1:
            staff_name = st.text_input("Reviewed By:", key=f"staff_remark_{prefix}_{idx}")
        with col2:
            remarks = st.text_area("Staff Remarks:", key=f"remarks_{prefix}_{idx}", height=100)
        if st.button(f"💬 Add Remarks for {heuristic_id}", key=f"remark_{prefix}_{idx}"):
            if staff_name:
                result['staff_justification'] = remarks
                result['staff_review_status'] = 'Accepted'
                result['reviewed_by'] = staff_name
                result['reviewed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"Remarks added by {staff_name}")
                st.rerun()


def render_heuristic_result(result, idx, prefix):
    """
    Render a single heuristic result with expandable details + staff review.
    Reused across ALL pages.
    """
    with st.expander(
        f"{get_flag_emoji(result['flag'])} {result['heuristic_id']}: "
        f"{result['heuristic_name']} - {get_review_status_indicator(result)}",
        expanded=(result.get('staff_review_status') == 'Pending')
    ):
        # Summary
        col1, col2 = st.columns([2, 1])
        with col1:
            if result.get('claimed_value') is not None:
                if result.get('output_type') == 'assessment':
                    st.write(f"**Actual:** {result['claimed_value']:.2f}%")
                    st.write(f"**Target:** {result['allowable_value']:.2f}%")
                else:
                    st.write(f"**Claimed:** ₹{result['claimed_value']:.2f} Cr")
            if result.get('allowable_value') is not None and result.get('output_type') != 'assessment':
                if result.get('output_type') == 'calculated_value':
                    st.write(f"**Calculated Value:** {result['allowable_value']:.2f}%")
                else:
                    st.write(f"**Allowable:** ₹{result['allowable_value']:.2f} Cr")
            if result.get('variance_percentage') is not None:
                st.write(f"**Variance:** {result['variance_percentage']:+.2f}%")
        with col2:
            st.info(f"**Flag:** {result['flag']}")
            if result.get('is_primary'):
                st.success("**PRIMARY** (Determines Amount)")

        # Calculation steps
        with st.expander("📋 Show Calculation Steps"):
            for step in result.get('calculation_steps', []):
                st.text(step)

        # Staff Review
        render_staff_review(result, idx, prefix)


def render_review_progress(line_item, page_name):
    """Render review progress bar and navigation button."""
    status = line_item.check_review_status()
    if status['complete']:
        st.success("✅ All reviews complete!")
        if st.button("📊 Go to Dashboard", key=f"go_dash_bottom_{page_name}", type="primary", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    elif status['total'] > 0:
        st.info(f"📊 Review Progress: {status['accepted'] + status['overridden']}/{status['total']} Complete")


# =============================================================================
# REUSABLE: SINGLE-HEURISTIC PAGE TEMPLATE
# =============================================================================

def render_single_heuristic_page(line_item_key, title, icon, form_key, prefix, render_form_fn):
    """
    Template for pages with a single heuristic (ROE, Depreciation, Fuel, etc.)

    Args:
        line_item_key: key in sbu.line_items
        title: page title
        icon: emoji icon
        form_key: unique form key
        prefix: prefix for widget keys
        render_form_fn: function(sbu) that renders the input form and returns inputs dict or None
    """
    st.title(f"{icon} {title} - Input & Analysis")
    sbu = get_sbu()
    line_item = sbu.get_line_item(line_item_key)

    if line_item is None:
        st.warning(f"⚠️ {title} is not applicable for SBU-{get_sbu_key()}")
        return

    status = line_item.check_review_status()
    if status['total'] == 0:
        st.info(f"📊 Run calculation to begin review")
    elif status['complete']:
        st.success(f"✅ Review Complete!")
        if st.button("📊 Go to Dashboard", key=f"go_dash_top_{prefix}", type="primary"):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    else:
        st.info(f"📊 Review Progress: {status['accepted'] + status['overridden']}/{status['total']} Complete")

    st.markdown("---")

    # Render form and get inputs
    inputs = render_form_fn(sbu)

    if inputs is not None:
        line_item.run_heuristic(inputs)
        st.success("✅ Calculation completed!")

    # Display results
    if line_item.heuristic_result:
        st.markdown("---")
        st.markdown("## 🔍 Results")
        render_heuristic_result(line_item.heuristic_result, 0, prefix)
        st.markdown("---")
        render_review_progress(line_item, prefix)


def render_multi_heuristic_page(line_item_key, title, icon, form_key, prefix, render_form_fn):
    """
    Template for pages with multiple heuristics (O&M, IFC, MasterTrust, Power Purchase).
    """
    st.title(f"{icon} {title} - Input & Analysis")
    sbu = get_sbu()
    line_item = sbu.get_line_item(line_item_key)

    if line_item is None:
        st.warning(f"⚠️ {title} is not applicable for SBU-{get_sbu_key()}")
        return

    status = line_item.check_review_status()
    if status['total'] == 0:
        st.info(f"📊 Run heuristics to begin reviews")
    elif status['complete']:
        st.success(f"✅ All Reviews Complete! {status['total']}/{status['total']}")
        if st.button("📊 Go to Dashboard", key=f"go_dash_top_{prefix}", type="primary"):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    else:
        st.info(f"📊 Review Progress: {status['accepted'] + status['overridden']}/{status['total']} Complete")

    st.markdown("---")

    # Render form and get inputs
    inputs = render_form_fn(sbu)

    if inputs is not None:
        line_item.run_all_heuristics(inputs)
        st.success("✅ All heuristics completed! Scroll down to review results.")

    # Display results
    results = line_item._get_all_results()
    if results:
        st.markdown("---")
        st.markdown("## 🔍 Heuristic Results")

        total_approved = line_item.get_approved_amount()
        if total_approved is not None:
            st.success(f"**Total Approved: ₹{total_approved:.2f} Cr**")

        for idx, result in enumerate(results):
            render_heuristic_result(result, idx, prefix)

        st.markdown("---")
        render_review_progress(line_item, prefix)


# =============================================================================
# SIDEBAR: SBU SELECTOR + NAVIGATION
# =============================================================================

st.sidebar.title("📊 KSERC Truing-Up")

# SBU selector
available_sbus = [s for s in get_available_sbus() if s['ready']]
sbu_options = {s['name']: s['code'] for s in available_sbus}

if 'sbu_code' not in st.session_state:
    st.session_state.sbu_code = 'G'

selected_sbu_name = st.sidebar.selectbox(
    "Select SBU:",
    list(sbu_options.keys()),
    index=list(sbu_options.values()).index(st.session_state.sbu_code)
    if st.session_state.sbu_code in sbu_options.values() else 0
)
new_sbu_code = sbu_options[selected_sbu_name]

# Reset page if SBU changed
if new_sbu_code != st.session_state.sbu_code:
    st.session_state.sbu_code = new_sbu_code
    st.session_state.current_page = "Dashboard"
    st.rerun()

st.sidebar.markdown("---")

# Build page list from config
config = get_sbu_config(get_sbu_key())
page_list = ["Dashboard"]
for item in config['line_items']:
    page_list.append(item['name'])

# Add special analysis pages
if get_sbu_key() == 'T':
    page_list.append("T&D Loss Analysis")
elif get_sbu_key() == 'D':
    page_list.append("T&D Loss Analysis")

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

page = st.sidebar.radio(
    "Select Page:",
    page_list,
    index=page_list.index(st.session_state.current_page)
    if st.session_state.current_page in page_list else 0
)
st.session_state.current_page = page

st.sidebar.markdown("---")
st.sidebar.markdown("**Legend:**")
st.sidebar.markdown("✅ Accepted | ⚠️ Review | ❌ Issues | ⏳ Pending")


# =============================================================================
# PAGE: DASHBOARD
# =============================================================================

if page == "Dashboard":
    sbu = get_sbu()
    st.title(f"{sbu.sbu_name} – Truing-Up Dashboard")

    # Line item cards
    st.markdown("### Select Line Item to Review")
    line_item_configs = config['line_items']

    for i in range(0, len(line_item_configs), 3):
        cols = st.columns(3)
        for col_idx, item_cfg in enumerate(line_item_configs[i:i+3]):
            with cols[col_idx]:
                key = item_cfg['key']
                icon = item_cfg['icon']
                name = item_cfg['name']
                line_item = sbu.get_line_item(key)

                if line_item:
                    status = line_item.check_review_status()
                    st.markdown(f"### {icon} {name}")
                    if status['total'] == 0:
                        st.info("⏳ Not Started")
                    elif status['complete']:
                        st.success(f"✅ Complete ({status['total']}/{status['total']})")
                    else:
                        st.warning(f"⏳ {status['pending']}/{status['total']} Pending")

                    if st.button(f"Open {name}", key=f"btn_{key}_dash"):
                        st.session_state.current_page = name
                        st.rerun()

    # Special analysis pages
    if get_sbu_key() in ['T', 'D']:
        st.markdown("---")
        st.markdown("### 📊 Special Analysis")
        if st.button("Open T&D Loss Analysis", key="btn_td_loss_dash"):
            st.session_state.current_page = "T&D Loss Analysis"
            st.rerun()

    # Aggregation section
    st.markdown("---")
    st.markdown("### 📊 Aggregation")

    agg_status = sbu.check_aggregation_ready()

    if not agg_status['ready_for_aggregation']:
        st.warning("⚠️ Complete all line item reviews before final aggregation")
        pending = sbu.get_pending_reviews()
        if pending:
            st.markdown("**Pending Reviews:**")
            for item in pending:
                st.write(f"- {item['line_item_name']}: {item['pending_count']} pending")
    else:
        st.success("✅ All reviews complete! Ready for aggregation.")
        if st.button("📊 View Final Aggregation", key="btn_final_agg", type="primary"):
            total_arr = sbu.calculate_total_arr()
            summary = sbu.get_sbu_summary()

            st.markdown("## 🎯 Final ARR Summary")
            st.success(f"**Total ARR: ₹{total_arr:.2f} Cr**")

            # Detailed breakdown
            df_data = []
            for key, line_item in sbu.line_items.items():
                approved = line_item.get_approved_amount()
                if approved is not None:
                    flag = line_item.get_overall_flag()
                    df_data.append({
                        'Line Item': line_item.line_item_name,
                        'Amount (₹ Cr)': round(approved, 2),
                        'Flag': flag
                    })

            if df_data:
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)


# =============================================================================
# PAGE: POWER PURCHASE (SBU-D only)
# =============================================================================

elif page == "Power Purchase":
    def pp_form(sbu):
        with st.form("pp_form"):
            st.markdown("### 💡 Power Purchase by Source (FY 2023-24)")
            st.info("📌 16 power sources - actual costs from audited accounts")

            # Source 1-4: KSEB Hydel stations
            st.markdown("#### 1️⃣ KSEB Hydel Stations")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                kseb_hydel_energy = st.number_input("Energy (MU)", value=1875.54, key="kseb_hydel_energy")
            with col2:
                kseb_hydel_cost = st.number_input("Cost (₹ Cr)", value=414.44, key="kseb_hydel_cost")
            with col3:
                kseb_hydel_rate = st.number_input("Rate (₹/kWh)", value=2.21, key="kseb_hydel_rate")
            with col4:
                st.metric("Source", "KSEB Hydel")

            # Source 2: KSEB Thermal
            st.markdown("#### 2️⃣ KSEB Thermal (Diesel)")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                kseb_thermal_energy = st.number_input("Energy (MU)", value=0.24, key="kseb_thermal_energy")
            with col2:
                kseb_thermal_cost = st.number_input("Cost (₹ Cr)", value=0.35, key="kseb_thermal_cost")
            with col3:
                kseb_thermal_rate = st.number_input("Rate (₹/kWh)", value=14.36, key="kseb_thermal_rate")
            with col4:
                st.metric("Source", "KSEB Thermal")

            # Source 3: NTPC Kayamkulam
            st.markdown("#### 3️⃣ NTPC Kayamkulam")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ntpc_kayam_energy = st.number_input("Energy (MU)", value=2508.78, key="ntpc_kayam_energy")
            with col2:
                ntpc_kayam_cost = st.number_input("Cost (₹ Cr)", value=1113.99, key="ntpc_kayam_cost")
            with col3:
                ntpc_kayam_rate = st.number_input("Rate (₹/kWh)", value=4.44, key="ntpc_kayam_rate")
            with col4:
                st.metric("Source", "NTPC Kayamkulam")

            # Source 4: NTPC Ramagundam
            st.markdown("#### 4️⃣ NTPC Ramagundam (LT)")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ntpc_rama_energy = st.number_input("Energy (MU)", value=848.22, key="ntpc_rama_energy")
            with col2:
                ntpc_rama_cost = st.number_input("Cost (₹ Cr)", value=296.23, key="ntpc_rama_cost")
            with col3:
                ntpc_rama_rate = st.number_input("Rate (₹/kWh)", value=3.49, key="ntpc_rama_rate")
            with col4:
                st.metric("Source", "NTPC Ramagundam")

            # Source 5: NTPC ISTS
            st.markdown("#### 5️⃣ NTPC ISTS Stations")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ntpc_ists_energy = st.number_input("Energy (MU)", value=2091.29, key="ntpc_ists_energy")
            with col2:
                ntpc_ists_cost = st.number_input("Cost (₹ Cr)", value=756.51, key="ntpc_ists_cost")
            with col3:
                ntpc_ists_rate = st.number_input("Rate (₹/kWh)", value=3.62, key="ntpc_ists_rate")
            with col4:
                st.metric("Source", "NTPC ISTS")

            # Source 6: NLC Tamil Nadu
            st.markdown("#### 6️⃣ NLC Tamil Nadu")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                nlc_tn_energy = st.number_input("Energy (MU)", value=1148.91, key="nlc_tn_energy")
            with col2:
                nlc_tn_cost = st.number_input("Cost (₹ Cr)", value=343.81, key="nlc_tn_cost")
            with col3:
                nlc_tn_rate = st.number_input("Rate (₹/kWh)", value=2.99, key="nlc_tn_rate")
            with col4:
                st.metric("Source", "NLC TN")

            # Source 7: NTPC-NVVN Short Term
            st.markdown("#### 7️⃣ NTPC-NVVN Short Term")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                nvvn_st_energy = st.number_input("Energy (MU)", value=1683.74, key="nvvn_st_energy")
            with col2:
                nvvn_st_cost = st.number_input("Cost (₹ Cr)", value=763.76, key="nvvn_st_cost")
            with col3:
                nvvn_st_rate = st.number_input("Rate (₹/kWh)", value=4.54, key="nvvn_st_rate")
            with col4:
                st.metric("Source", "NVVN ST")

            # Source 8: Renewable Energy (Solar)
            st.markdown("#### 8️⃣ Renewable Energy - Solar")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                re_solar_energy = st.number_input("Energy (MU)", value=578.32, key="re_solar_energy")
            with col2:
                re_solar_cost = st.number_input("Cost (₹ Cr)", value=177.42, key="re_solar_cost")
            with col3:
                re_solar_rate = st.number_input("Rate (₹/kWh)", value=3.07, key="re_solar_rate")
            with col4:
                st.metric("Source", "RE Solar")

            # Source 9: Renewable Energy (Wind)
            st.markdown("#### 9️⃣ Renewable Energy - Wind")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                re_wind_energy = st.number_input("Energy (MU)", value=123.45, key="re_wind_energy")
            with col2:
                re_wind_cost = st.number_input("Cost (₹ Cr)", value=45.67, key="re_wind_cost")
            with col3:
                re_wind_rate = st.number_input("Rate (₹/kWh)", value=3.70, key="re_wind_rate")
            with col4:
                st.metric("Source", "RE Wind")

            # Source 10: Banking & Exchanges
            st.markdown("#### 🔟 Power Banking & Exchanges")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                banking_energy = st.number_input("Energy (MU)", value=234.56, key="banking_energy")
            with col2:
                banking_cost = st.number_input("Cost (₹ Cr)", value=89.12, key="banking_cost")
            with col3:
                banking_rate = st.number_input("Rate (₹/kWh)", value=3.80, key="banking_rate")
            with col4:
                st.metric("Source", "Banking")

            # Source 11: IEX (Day Ahead Market)
            st.markdown("#### 1️⃣1️⃣ IEX - Day Ahead Market")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                iex_dam_energy = st.number_input("Energy (MU)", value=456.78, key="iex_dam_energy")
            with col2:
                iex_dam_cost = st.number_input("Cost (₹ Cr)", value=234.56, key="iex_dam_cost")
            with col3:
                iex_dam_rate = st.number_input("Rate (₹/kWh)", value=5.14, key="iex_dam_rate")
            with col4:
                st.metric("Source", "IEX DAM")

            # Source 12: IEX (Term Ahead Market)
            st.markdown("#### 1️⃣2️⃣ IEX - Term Ahead Market")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                iex_tam_energy = st.number_input("Energy (MU)", value=345.67, key="iex_tam_energy")
            with col2:
                iex_tam_cost = st.number_input("Cost (₹ Cr)", value=167.89, key="iex_tam_cost")
            with col3:
                iex_tam_rate = st.number_input("Rate (₹/kWh)", value=4.86, key="iex_tam_rate")
            with col4:
                st.metric("Source", "IEX TAM")

            # Source 13: Bilateral Agreements
            st.markdown("#### 1️⃣3️⃣ Bilateral Trading Agreements")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                bilateral_energy = st.number_input("Energy (MU)", value=567.89, key="bilateral_energy")
            with col2:
                bilateral_cost = st.number_input("Cost (₹ Cr)", value=278.45, key="bilateral_cost")
            with col3:
                bilateral_rate = st.number_input("Rate (₹/kWh)", value=4.90, key="bilateral_rate")
            with col4:
                st.metric("Source", "Bilateral")

            # Source 14: UI Charges
            st.markdown("#### 1️⃣4️⃣ Unscheduled Interchange (UI) Charges")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ui_energy = st.number_input("Energy (MU)", value=123.45, key="ui_energy")
            with col2:
                ui_cost = st.number_input("Cost (₹ Cr)", value=67.89, key="ui_cost")
            with col3:
                ui_rate = st.number_input("Rate (₹/kWh)", value=5.50, key="ui_rate")
            with col4:
                st.metric("Source", "UI Charges")

            # Source 15: CGS (Central Generating Stations)
            st.markdown("#### 1️⃣5️⃣ Other CGS Allocations")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                cgs_energy = st.number_input("Energy (MU)", value=890.12, key="cgs_energy")
            with col2:
                cgs_cost = st.number_input("Cost (₹ Cr)", value=356.78, key="cgs_cost")
            with col3:
                cgs_rate = st.number_input("Rate (₹/kWh)", value=4.01, key="cgs_rate")
            with col4:
                st.metric("Source", "Other CGS")

            # Source 16: Other Sources
            st.markdown("#### 1️⃣6️⃣ Other Sources")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                other_energy = st.number_input("Energy (MU)", value=45.67, key="other_energy")
            with col2:
                other_cost = st.number_input("Cost (₹ Cr)", value=23.45, key="other_cost")
            with col3:
                other_rate = st.number_input("Rate (₹/kWh)", value=5.14, key="other_rate")
            with col4:
                st.metric("Source", "Others")

            st.markdown("---")
            # Total claimed
            st.markdown("### 📊 Total Power Purchase")
            total_claimed_pp = st.number_input("Total PP Claimed (₹ Cr)", value=5130.27, key="total_pp_claimed")

            submitted = st.form_submit_button("🔍 Validate Power Purchase", use_container_width=True)
            if submitted:
                return {
                    'power_sources': [
                        {'name': 'KSEB Hydel', 'energy_mu': kseb_hydel_energy, 'cost_cr': kseb_hydel_cost, 'rate': kseb_hydel_rate},
                        {'name': 'KSEB Thermal', 'energy_mu': kseb_thermal_energy, 'cost_cr': kseb_thermal_cost, 'rate': kseb_thermal_rate},
                        {'name': 'NTPC Kayamkulam', 'energy_mu': ntpc_kayam_energy, 'cost_cr': ntpc_kayam_cost, 'rate': ntpc_kayam_rate},
                        {'name': 'NTPC Ramagundam', 'energy_mu': ntpc_rama_energy, 'cost_cr': ntpc_rama_cost, 'rate': ntpc_rama_rate},
                        {'name': 'NTPC ISTS', 'energy_mu': ntpc_ists_energy, 'cost_cr': ntpc_ists_cost, 'rate': ntpc_ists_rate},
                        {'name': 'NLC Tamil Nadu', 'energy_mu': nlc_tn_energy, 'cost_cr': nlc_tn_cost, 'rate': nlc_tn_rate},
                        {'name': 'NVVN Short Term', 'energy_mu': nvvn_st_energy, 'cost_cr': nvvn_st_cost, 'rate': nvvn_st_rate},
                        {'name': 'RE Solar', 'energy_mu': re_solar_energy, 'cost_cr': re_solar_cost, 'rate': re_solar_rate},
                        {'name': 'RE Wind', 'energy_mu': re_wind_energy, 'cost_cr': re_wind_cost, 'rate': re_wind_rate},
                        {'name': 'Banking', 'energy_mu': banking_energy, 'cost_cr': banking_cost, 'rate': banking_rate},
                        {'name': 'IEX DAM', 'energy_mu': iex_dam_energy, 'cost_cr': iex_dam_cost, 'rate': iex_dam_rate},
                        {'name': 'IEX TAM', 'energy_mu': iex_tam_energy, 'cost_cr': iex_tam_cost, 'rate': iex_tam_rate},
                        {'name': 'Bilateral', 'energy_mu': bilateral_energy, 'cost_cr': bilateral_cost, 'rate': bilateral_rate},
                        {'name': 'UI Charges', 'energy_mu': ui_energy, 'cost_cr': ui_cost, 'rate': ui_rate},
                        {'name': 'Other CGS', 'energy_mu': cgs_energy, 'cost_cr': cgs_cost, 'rate': cgs_rate},
                        {'name': 'Others', 'energy_mu': other_energy, 'cost_cr': other_cost, 'rate': other_rate},
                    ],
                    'claimed_total_pp': total_claimed_pp,
                }
        return None

    render_multi_heuristic_page('power_purchase', 'Power Purchase', '⚡', 'pp_form', 'pp', pp_form)


# =============================================================================
# PAGE: O&M EXPENSES
# =============================================================================

elif page == "O&M Expenses":
    sbu_code = get_sbu_key()

    # SBU-G: Multi-heuristic O&M
    if sbu_code == 'G':
        def om_g_form(sbu):
            with st.form("om_gen_form"):
                st.markdown("### Inflation Parameters")
                col1, col2 = st.columns(2)
                with col1:
                    cpi_old = st.number_input("CPI (Old)", value=335)
                    wpi_old = st.number_input("WPI (Old)", value=167.33)
                with col2:
                    cpi_new = st.number_input("CPI (New)", value=363)
                    wpi_new = st.number_input("WPI (New)", value=176.05)

                st.markdown("### Base Year O&M")
                col1, col2 = st.columns(2)
                with col1:
                    base_year_om = st.number_input("Base Year O&M [Cr]", value=149.08)
                with col2:
                    inflation_2022_23 = st.number_input("Inflation 2022-23 (%)", value=6.7) / 100
                    inflation_2023_24 = st.number_input("Inflation 2023-24 (%)", value=6.3) / 100

                st.markdown("### Claimed Amounts (Rs. Cr)")
                col1, col2 = st.columns(2)
                with col1:
                    claimed_existing = st.number_input("Existing Stations", value=175.34)
                    new_stations_allowable = st.number_input("New Stations (Normative)", value=10.82)
                with col2:
                    actual_employee = st.number_input("Employee Costs", value=140.00)
                    actual_ag = st.number_input("A&G Costs", value=25.00)
                    actual_rm = st.number_input("R&M Costs", value=21.00)

                pay_revision = st.number_input("Pay Revision Arrears [Cr]", value=0.0)

                submitted = st.form_submit_button("🔍 Run O&M Heuristics", use_container_width=True)
                if submitted:
                    return {
                        'cpi_old': cpi_old, 'cpi_new': cpi_new,
                        'wpi_old': wpi_old, 'wpi_new': wpi_new,
                        'base_year_om': base_year_om,
                        'inflation_2022_23': inflation_2022_23,
                        'inflation_2023_24': inflation_2023_24,
                        'claimed_existing': claimed_existing,
                        'new_stations_allowable': new_stations_allowable,
                        'actual_employee': actual_employee,
                        'actual_ag': actual_ag, 'actual_rm': actual_rm,
                        'pay_revision': pay_revision,
                    }
            return None

        render_multi_heuristic_page('om_expenses', 'O&M Expenses', '🔧', 'om_form', 'om', om_g_form)

    # SBU-T: Single-heuristic normative O&M
    elif sbu_code == 'T':
        def om_t_form(sbu):
            with st.form("om_trans_form"):
                st.markdown("### O&M Norms (Rs. Lakh per unit)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    norm_per_bay = st.number_input("Per Bay", value=7.884, step=0.001)
                with col2:
                    norm_per_mva = st.number_input("Per MVA", value=0.872, step=0.001)
                with col3:
                    norm_per_cktkm = st.number_input("Per Ckt-Km", value=1.592, step=0.001)

                st.markdown("### Opening Parameters")
                col1, col2, col3 = st.columns(3)
                with col1:
                    opening_bays = st.number_input("Bays", value=2905)
                with col2:
                    opening_mva = st.number_input("MVA", value=25344.5)
                with col3:
                    opening_cktkm = st.number_input("Ckt-Km", value=10633.90)

                st.markdown("### Additions During Year")
                col1, col2, col3 = st.columns(3)
                with col1:
                    added_bays = st.number_input("Bays Added", value=24)
                with col2:
                    added_mva = st.number_input("MVA Added", value=785.0)
                with col3:
                    added_cktkm = st.number_input("CktKm Added", value=166.23)

                st.markdown("### Financial Data (Rs. Cr)")
                col1, col2 = st.columns(2)
                with col1:
                    myt_approved_om = st.number_input("MYT Approved", value=644.81)
                    actual_om_accounts = st.number_input("Actual (Accounts)", value=588.95)
                with col2:
                    claimed_om = st.number_input("TU Claimed", value=625.20)

                submitted = st.form_submit_button("🔍 Calculate Transmission O&M", use_container_width=True)
                if submitted:
                    return {
                        'norm_per_bay': norm_per_bay, 'norm_per_mva': norm_per_mva,
                        'norm_per_cktkm': norm_per_cktkm,
                        'opening_bays': opening_bays, 'opening_mva': opening_mva,
                        'opening_cktkm': opening_cktkm,
                        'added_bays': added_bays, 'added_mva': added_mva,
                        'added_cktkm': added_cktkm,
                        'myt_approved_om': myt_approved_om,
                        'actual_om_accounts': actual_om_accounts,
                        'claimed_om': claimed_om,
                    }
            return None

        render_single_heuristic_page('om_expenses', 'O&M Expenses (Transmission)',
                                     '🔧', 'om_trans_form', 'om_t', om_t_form)

    # SBU-D: 5-parameter distribution norms
    elif sbu_code == 'D':
        def om_d_form(sbu):
            with st.form("om_dist_form"):
                st.info("💡 Distribution O&M based on 5 parameters: Consumers, DTRs, HT Lines, LT Lines, Energy Sales")

                st.markdown("### O&M Norms (Rs. Lakh per unit)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    norm_consumer = st.number_input("Per Consumer", value=0.7395, step=0.0001)
                    norm_dtr = st.number_input("Per DTR", value=16.654, step=0.001)
                with col2:
                    norm_ht_line = st.number_input("Per HT Line km", value=8.301, step=0.001)
                    norm_lt_line = st.number_input("Per LT Line km", value=2.659, step=0.001)
                with col3:
                    norm_energy = st.number_input("Per MU Sold", value=2.317, step=0.001)

                st.markdown("### Network Parameters (Opening + Additions)")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Opening**")
                    opening_consumers = st.number_input("Consumers", value=13500000, key="opening_cons")
                    opening_dtrs = st.number_input("DTRs", value=145000, key="opening_dtrs")
                    opening_ht_km = st.number_input("HT Lines (km)", value=23500, key="opening_ht")
                    opening_lt_km = st.number_input("LT Lines (km)", value=125000, key="opening_lt")
                with col2:
                    st.markdown("**Additions**")
                    added_consumers = st.number_input("Consumers", value=250000, key="added_cons")
                    added_dtrs = st.number_input("DTRs", value=3500, key="added_dtrs")
                    added_ht_km = st.number_input("HT Lines (km)", value=450, key="added_ht")
                    added_lt_km = st.number_input("LT Lines (km)", value=2800, key="added_lt")

                st.markdown("### Energy Sales")
                energy_sales_mu = st.number_input("Energy Sales (MU)", value=27500.0)

                st.markdown("### Financial Data (Rs. Cr)")
                col1, col2 = st.columns(2)
                with col1:
                    myt_approved_om = st.number_input("MYT Approved", value=3245.67)
                    actual_om_accounts = st.number_input("Actual (Accounts)", value=3198.45)
                with col2:
                    claimed_om = st.number_input("TU Claimed", value=3278.90)

                submitted = st.form_submit_button("🔍 Calculate Distribution O&M", use_container_width=True)
                if submitted:
                    return {
                        'norm_per_consumer': norm_consumer,
                        'norm_per_dtr': norm_dtr,
                        'norm_per_ht_line_km': norm_ht_line,
                        'norm_per_lt_line_km': norm_lt_line,
                        'norm_per_mu_sold': norm_energy,
                        'opening_consumers': opening_consumers,
                        'opening_dtrs': opening_dtrs,
                        'opening_ht_line_km': opening_ht_km,
                        'opening_lt_line_km': opening_lt_km,
                        'added_consumers': added_consumers,
                        'added_dtrs': added_dtrs,
                        'added_ht_line_km': added_ht_km,
                        'added_lt_line_km': added_lt_km,
                        'energy_sales_mu': energy_sales_mu,
                        'myt_approved_om': myt_approved_om,
                        'actual_om_accounts': actual_om_accounts,
                        'claimed_total_om': claimed_om,
                    }
            return None

        render_single_heuristic_page('om_expenses', 'O&M Expenses (Distribution)',
                                     '🔧', 'om_dist_form', 'om_d', om_d_form)


# =============================================================================
# PAGE: RETURN ON EQUITY (shared)
# =============================================================================

elif page == "Return on Equity":
    equity_default = config.get('equity_base_cr', 831.27)

    def roe_form(sbu):
        with st.form("roe_form"):
            st.markdown("### ROE Parameters")
            col1, col2 = st.columns(2)
            with col1:
                equity_capital = st.number_input("Equity Capital [Cr]", value=equity_default)
                roe_rate = st.number_input("ROE Rate (%)", value=14.0) / 100
            with col2:
                claimed_roe = st.number_input("ROE Claimed [Cr]", value=116.38)
            submitted = st.form_submit_button("🔍 Calculate ROE", use_container_width=True)
            if submitted:
                return {'equity_capital': equity_capital, 'roe_rate': roe_rate, 'claimed_roe': claimed_roe}
        return None

    render_single_heuristic_page('roe', 'Return on Equity', '💰', 'roe_form', 'roe', roe_form)


# =============================================================================
# PAGE: DEPRECIATION (shared)
# =============================================================================

elif page == "Depreciation":
    def dep_form(sbu):
        with st.form("dep_form"):
            st.markdown("### Opening Balances (as on 31.03.2023)")
            col1, col2 = st.columns(2)
            with col1:
                gfa_opening_total = st.number_input("Total GFA (Net) [Cr]", value=5695.7)
                gfa_13_to_30 = st.number_input("GFA (13-30 years) [Cr]", value=3033.9)
                land_13_to_30 = st.number_input("Land (13-30 years) [Cr]", value=81.6)
                grants_13_to_30 = st.number_input("Grants (13-30 years) [Cr]", value=0.0)
            with col2:
                gfa_below_13 = st.number_input("GFA (<13 years) [Cr]", value=2294.0)
                land_below_13 = st.number_input("Land (<13 years) [Cr]", value=145.5)
                grants_below_13 = st.number_input("Grants (<13 years) [Cr]", value=112.1)
            st.markdown("### Changes During Year")
            col1, col2 = st.columns(2)
            with col1:
                asset_additions = st.number_input("Additions [Cr]", value=405.9)
            with col2:
                asset_withdrawals = st.number_input("Withdrawals [Cr]", value=0.0)
            claimed_depreciation = st.number_input("Depreciation Claimed [Cr]", value=157.0)
            submitted = st.form_submit_button("🔍 Calculate Depreciation", use_container_width=True)
            if submitted:
                return {
                    'gfa_opening_total': gfa_opening_total,
                    'gfa_13_to_30_years': gfa_13_to_30, 'land_13_to_30_years': land_13_to_30,
                    'grants_13_to_30_years': grants_13_to_30,
                    'gfa_below_13_years': gfa_below_13, 'land_below_13_years': land_below_13,
                    'grants_below_13_years': grants_below_13,
                    'asset_additions': asset_additions, 'asset_withdrawals': asset_withdrawals,
                    'claimed_depreciation': claimed_depreciation,
                }
        return None

    render_single_heuristic_page('depreciation', 'Depreciation', '📉', 'dep_form', 'dep', dep_form)


# =============================================================================
# PAGE: INTEREST & FINANCE CHARGES
# =============================================================================

elif page == "Interest & Finance Charges":
    sbu_code = get_sbu_key()

    # Shared IFC for G and T
    if sbu_code in ['G', 'T']:
        def ifc_form(sbu):
            with st.form("ifc_form"):
                st.markdown("### Interest on Long-Term Loans (IFC-LTL-01)")
                col1, col2 = st.columns(2)
                with col1:
                    opening_normative_loan = st.number_input("Opening Normative Loan [Cr]", value=896.34)
                    gfa_additions = st.number_input("GFA Additions [Cr]", value=410.20)
                    depreciation = st.number_input("Depreciation [Cr]", value=157.02)
                with col2:
                    opening_interest_rate = st.number_input("Opening Interest Rate (%)", value=8.35)
                    claimed_interest = st.number_input("Interest Claimed [Cr]", value=104.46)

                st.markdown("### Interest on Working Capital (IFC-WC-01)")
                col1, col2 = st.columns(2)
                with col1:
                    approved_om_expenses = st.number_input("Approved O&M [Cr]", value=186.16)
                    opening_gfa_excl_land = st.number_input("GFA excl. Land [Cr]", value=5468.6)
                with col2:
                    wc_rate = st.number_input("WC Interest Rate (SBI Base)", value=9.70)
                    claimed_wc_interest = st.number_input("WC Interest Claimed [Cr]", value=20.48)

                st.markdown("### GPF Contributions (IFC-GPF-01)")
                actual_gpf_contribution = st.number_input("Actual GPF Contribution [Cr]", value=15.23)

                st.markdown("### Other Interest (IFC-OTH-01)")
                claimed_other = st.number_input("Other Interest Claimed [Cr]", value=5.67)

                submitted = st.form_submit_button("🔍 Calculate IFC", use_container_width=True)
                if submitted:
                    return {
                        'opening_normative_loan': opening_normative_loan,
                        'gfa_additions': gfa_additions,
                        'depreciation_charged': depreciation,
                        'opening_weighted_interest_rate': opening_interest_rate / 100,
                        'claimed_interest_ltl': claimed_interest,
                        'approved_om_expenses': approved_om_expenses,
                        'opening_gfa_excl_land': opening_gfa_excl_land,
                        'wc_interest_rate': wc_rate / 100,
                        'claimed_wc_interest': claimed_wc_interest,
                        'actual_gpf_contribution_in_year': actual_gpf_contribution,
                        'claimed_other_interest': claimed_other,
                    }
            return None

        render_multi_heuristic_page('ifc', 'Interest & Finance Charges', '🏦', 'ifc_form', 'ifc', ifc_form)

    # SBU-D specific IFC (has 4 separate pages)
    else:
        st.warning("⚠️ For SBU-D, please use the specific IFC pages: Security Deposits, Carrying Cost, Working Capital, Other Items")


# =============================================================================
# PAGE: IFC - SECURITY DEPOSITS (SBU-D only)
# =============================================================================

elif page == "Interest on Security Deposits":
    def ifc_sd_form(sbu):
        with st.form("ifc_sd_form"):
            st.info("💡 Only ACTUAL DISBURSEMENT allowed (Reg 29(8))")
            col1, col2 = st.columns(2)
            with col1:
                myt_approved = st.number_input("MYT Approved [Cr]", value=156.11)
                actual_disbursement = st.number_input("Actual Disbursement [Cr]", value=146.88)
            with col2:
                provision_accounts = st.number_input("Provision in Accounts [Cr]", value=265.92)
                avg_sd = st.number_input("Avg Security Deposit [Cr]", value=4146.85)
            interest_rate = st.number_input("Interest Rate (%)", value=6.75) / 100
            claimed = st.number_input("Claimed SD Interest [Cr]", value=146.88)
            submitted = st.form_submit_button("🔍 Calculate SD Interest", use_container_width=True)
            if submitted:
                return {
                    'myt_approved_sd_interest': myt_approved,
                    'actual_disbursement': actual_disbursement,
                    'provision_in_accounts': provision_accounts,
                    'avg_security_deposit': avg_sd,
                    'interest_rate_applied': interest_rate,
                    'claimed_sd_interest': claimed,
                }
        return None

    render_single_heuristic_page('ifc_sd', 'Interest on Security Deposits', '🏦', 'ifc_sd_form', 'ifc_sd', ifc_sd_form)


# =============================================================================
# PAGE: IFC - CARRYING COST (SBU-D only)
# =============================================================================

elif page == "Carrying Cost on Revenue Gap":
    def ifc_cc_form(sbu):
        with st.form("ifc_cc_form"):
            st.info("💡 Carrying cost on unbridged revenue gap @ avg interest rate")
            col1, col2 = st.columns(2)
            with col1:
                revenue_gap = st.number_input("Revenue Gap 01.04 [Cr]", value=6408.37)
                avg_gpf = st.number_input("Avg GPF Balance [Cr]", value=2926.29)
            with col2:
                excess_sd = st.number_input("Excess SD over WC [Cr]", value=451.04)
                avg_rate = st.number_input("Avg Interest Rate (%)", value=8.52) / 100
            claimed_cc = st.number_input("Claimed Carrying Cost [Cr]", value=321.24)
            myt_approved_cc = st.number_input("MYT Approved [Cr]", value=211.91)
            submitted = st.form_submit_button("🔍 Calculate Carrying Cost", use_container_width=True)
            if submitted:
                return {
                    'revenue_gap_as_on_01_04': revenue_gap,
                    'avg_gpf_balance': avg_gpf,
                    'excess_security_deposit': excess_sd,
                    'avg_interest_rate': avg_rate,
                    'claimed_carrying_cost': claimed_cc,
                    'myt_approved_carrying_cost': myt_approved_cc,
                }
        return None

    render_single_heuristic_page('ifc_cc', 'Carrying Cost on Revenue Gap', '💳', 'ifc_cc_form', 'ifc_cc', ifc_cc_form)


# =============================================================================
# PAGE: IFC - WORKING CAPITAL (SBU-D only)
# =============================================================================

elif page == "Interest on Working Capital (Distribution)":
    def ifc_wc_d_form(sbu):
        with st.form("ifc_wc_d_form"):
            st.info("💡 WC for Distribution: O&M(1 month) + Receivables(2 months) + Fuel Stock")
            col1, col2 = st.columns(2)
            with col1:
                approved_om = st.number_input("Approved O&M [Cr]", value=3245.67)
                avg_receivables = st.number_input("Avg Receivables [Cr]", value=1234.56)
            with col2:
                opening_gfa = st.number_input("Opening GFA excl. Land [Cr]", value=12345.67)
                wc_rate = st.number_input("WC Interest Rate (%)", value=9.70) / 100
            claimed_wc = st.number_input("Claimed WC Interest [Cr]", value=45.67)
            submitted = st.form_submit_button("🔍 Calculate WC Interest", use_container_width=True)
            if submitted:
                return {
                    'approved_om_expenses': approved_om,
                    'avg_receivables_2months': avg_receivables,
                    'opening_gfa_excl_land': opening_gfa,
                    'wc_interest_rate': wc_rate,
                    'claimed_wc_interest': claimed_wc,
                }
        return None

    render_single_heuristic_page('ifc_wc', 'Interest on Working Capital (Distribution)', 
                                 '🏦', 'ifc_wc_d_form', 'ifc_wc_d', ifc_wc_d_form)


# =============================================================================
# PAGE: IFC - OTHER ITEMS (SBU-D only)
# =============================================================================

elif page == "Interest on Other Items (Distribution)":
    def ifc_oth_d_form(sbu):
        with st.form("ifc_oth_d_form"):
            st.info("💡 Other interest: PP arrears, GPF, Consumer deposits, etc.")
            col1, col2 = st.columns(2)
            with col1:
                pp_arrears_interest = st.number_input("PP Arrears Interest [Cr]", value=12.34)
                gpf_contribution = st.number_input("GPF Contribution [Cr]", value=23.45)
            with col2:
                consumer_deposits_interest = st.number_input("Consumer Deposits Interest [Cr]", value=5.67)
                other_interest = st.number_input("Other Interest [Cr]", value=3.21)
            claimed_total = st.number_input("Total Other Interest Claimed [Cr]", value=44.67)
            submitted = st.form_submit_button("🔍 Calculate Other Interest", use_container_width=True)
            if submitted:
                return {
                    'pp_arrears_interest': pp_arrears_interest,
                    'gpf_contribution': gpf_contribution,
                    'consumer_deposits_interest': consumer_deposits_interest,
                    'other_interest': other_interest,
                    'claimed_other_interest': claimed_total,
                }
        return None

    render_single_heuristic_page('ifc_oth', 'Interest on Other Items (Distribution)',
                                 '💰', 'ifc_oth_d_form', 'ifc_oth_d', ifc_oth_d_form)


# =============================================================================
# PAGE: MASTER TRUST OBLIGATIONS (shared)
# =============================================================================

elif page == "Master Trust Obligations":
    def mt_form(sbu):
        with st.form("mt_form"):
            st.markdown("### MT-BOND-01: Interest on Master Trust Bonds")
            col1, col2 = st.columns(2)
            with col1:
                total_bond_interest = st.number_input("Total Bond Interest (All SBUs) [Cr]", value=78.95)
                sbu_ratio_bond = st.number_input("SBU Allocation Ratio", value=0.167, step=0.001)
            with col2:
                claimed_bond = st.number_input("Claimed Bond Interest (This SBU) [Cr]", value=13.18)

            st.markdown("### MT-REPAY-01: Principal Repayment")
            col1, col2 = st.columns(2)
            with col1:
                annual_repayment = st.number_input("Annual Repayment (All SBUs) [Cr]", value=150.00)
            with col2:
                claimed_repay = st.number_input("Claimed Repayment (This SBU) [Cr]", value=25.05)

            st.markdown("### MT-ADD-01: Additional Actuarial Contribution")
            col1, col2 = st.columns(2)
            with col1:
                actuarial = st.number_input("Actuarial Liability [Cr]", value=500.00)
                provisional_cap = st.number_input("Provisional Cap [Cr]", value=100.00)
                claimed_add = st.number_input("Claimed Additional [Cr]", value=16.70)
            with col2:
                actuarial_submitted = st.checkbox("Actuarial report submitted?", value=False)
                govt_approval = st.checkbox("Govt approval obtained?")

            submitted = st.form_submit_button("🔍 Calculate Master Trust", use_container_width=True)
            if submitted:
                return {
                    'total_bond_interest': total_bond_interest,
                    'sbu_allocation_ratio': sbu_ratio_bond,
                    'claimed_bond_interest_sbu': claimed_bond,
                    'annual_principal_repayment': annual_repayment,
                    'claimed_principal_repayment_sbu': claimed_repay,
                    'actuarial_liability_current_year': actuarial,
                    'provisional_cap': provisional_cap,
                    'claimed_additional_contribution_sbu': claimed_add,
                    'actuarial_report_submitted': actuarial_submitted,
                    'govt_approval_obtained': govt_approval,
                }
        return None

    render_multi_heuristic_page('master_trust', 'Master Trust Obligations', '🛡️', 'mt_form', 'mt', mt_form)


# =============================================================================
# PAGE: FUEL COSTS (SBU-G only)
# =============================================================================

elif page == "Fuel Costs":
    def fuel_form(sbu):
        with st.form("fuel_form"):
            st.info("💡 Fuel costs for hydel stations: lubricants, hydraulic oils, consumables")
            col1, col2 = st.columns(2)
            with col1:
                heavy_fuel = st.number_input("Heavy Fuel Oil [Cr]", value=0.0)
                hsd = st.number_input("HSD Oil [Cr]", value=0.0)
            with col2:
                lube = st.number_input("Lube Oil [Cr]", value=0.34)
                consumables = st.number_input("Consumables [Cr]", value=0.0)
            total_claimed = st.number_input("Total Fuel Claimed [Cr]", value=0.34)
            submitted = st.form_submit_button("🔍 Calculate Fuel Costs", use_container_width=True)
            if submitted:
                return {
                    'heavy_fuel_oil': heavy_fuel, 'hsd_oil': hsd,
                    'lube_oil': lube, 'lubricants_consumables': consumables,
                    'total_claimed_fuel_cost': total_claimed,
                }
        return None

    render_single_heuristic_page('fuel_costs', 'Fuel Costs', '⚡', 'fuel_form', 'fuel', fuel_form)


# =============================================================================
# PAGE: OTHER EXPENSES (shared)
# =============================================================================

elif page == "Other Expenses":
    def other_form(sbu):
        with st.form("other_form"):
            claimed_discount = st.number_input("Discount to Consumers [Cr]", value=0.0)
            claimed_flood = st.number_input("Flood/Cyclone Losses [Cr]", value=0.07)
            flood_docs = st.checkbox("Supporting documents provided?", value=True)
            claimed_misc = st.number_input("Misc Write-offs [Cr]", value=0.0)
            writeoff_docs = st.checkbox("Appeal orders/documentation?", value=False)
            submitted = st.form_submit_button("🔍 Calculate Other Expenses", use_container_width=True)
            if submitted:
                return {
                    'claimed_discount_to_consumers': claimed_discount,
                    'claimed_flood_losses': claimed_flood,
                    'claimed_misc_writeoffs': claimed_misc,
                    'flood_supporting_docs': flood_docs,
                    'writeoff_appeal_orders': writeoff_docs,
                }
        return None

    render_single_heuristic_page('other_expenses', 'Other Expenses', '📋', 'other_form', 'other', other_form)


# =============================================================================
# PAGE: EXCEPTIONAL ITEMS (shared)
# =============================================================================

elif page == "Exceptional Items":
    def exc_form(sbu):
        with st.form("exc_form"):
            claimed_calamity = st.number_input("Natural Calamity R&M [Cr]", value=0.02)
            col1, col2 = st.columns(2)
            with col1:
                separate_code = st.checkbox("Separate account codes?", value=True)
            with col2:
                docs = st.checkbox("Supporting documents?", value=True)
            st.warning("⚠️ Govt Loss Takeover is ALWAYS EXCLUDED")
            submitted = st.form_submit_button("🔍 Calculate Exceptional Items", use_container_width=True)
            if submitted:
                return {
                    'claimed_calamity_rm': claimed_calamity,
                    'claimed_govt_loss_takeover': 0.0,
                    'separate_account_code': separate_code,
                    'calamity_supporting_docs': docs,
                }
        return None

    render_single_heuristic_page('exceptional_items', 'Exceptional Items', '⚠️', 'exc_form', 'exc', exc_form)


# =============================================================================
# PAGE: INTANGIBLE ASSETS (shared)
# =============================================================================

elif page in ["Intangible Assets", "Intangible Assets (Software)", "Amortisation of Intangible Assets (Software)"]:
    def intang_form(sbu):
        with st.form("intang_form"):
            st.warning("⚠️ Software costs may already be in normative O&M. Double-counting risk!")
            col1, col2 = st.columns(2)
            with col1:
                sw_costs = st.number_input("Employee Costs Capitalized [Cr]", value=0.0)
                sw_amort = st.number_input("Software Amortization Claimed [Cr]", value=0.0)
            with col2:
                sw_docs = st.checkbox("Supporting docs?", value=False)
                sw_additional = st.checkbox("Employees additional to norms?", value=False)
            col1, col2 = st.columns(2)
            with col1:
                purchased_sw = st.number_input("Purchased Software [Cr]", value=0.0)
                patents = st.number_input("Patents/IP [Cr]", value=0.0)
            with col2:
                other_intang = st.number_input("Other Intangibles [Cr]", value=0.0)
                other_amort = st.number_input("Other Amortization [Cr]", value=0.0)
            total_claimed = st.number_input("Total Amortization Claimed [Cr]", value=0.0)
            submitted = st.form_submit_button("🔍 Validate Intangibles", use_container_width=True)
            if submitted:
                return {
                    'software_employee_costs_capitalized': sw_costs,
                    'software_amortization_claimed': sw_amort,
                    'software_supporting_docs_provided': sw_docs,
                    'software_employees_additional_to_norms': sw_additional,
                    'purchased_software_licenses': purchased_sw,
                    'patents_ip': patents, 'other_intangibles': other_intang,
                    'other_intangibles_amortization': other_amort,
                    'other_supporting_docs_provided': False,
                    'total_claimed_amortization': total_claimed,
                }
        return None

    render_single_heuristic_page('intangible_assets', 'Intangible Assets', '💾', 'intang_form', 'intang', intang_form)


# =============================================================================
# PAGE: NON-TARIFF INCOME (shared)
# =============================================================================

elif page == "Non-Tariff Income":
    def nti_form(sbu):
        with st.form("nti_form"):
            st.info("💡 NTI is DEDUCTED from ARR – higher NTI reduces tariff burden")
            col1, col2 = st.columns(2)
            with col1:
                myt_baseline = st.number_input("MYT Approved NTI [Cr]", value=40.21)
                base_income = st.number_input("Base Income from Accounts [Cr]", value=45.67)
            with col2:
                claimed_nti = st.number_input("Claimed NTI [Cr]", value=43.21)

            st.markdown("### Exclusions")
            col1, col2 = st.columns(2)
            with col1:
                grant_clawback = st.number_input("Grant Claw-back [Cr]", value=1.23)
                led_bulbs = st.number_input("LED Bulb Costs [Cr]", value=0.45)
                nilaavu = st.number_input("Nilaavu Scheme [Cr]", value=0.0)
            with col2:
                provision_rev = st.number_input("Provision Reversals [Cr]", value=0.0)
                kwa_unrealized = st.number_input("KWA Unrealized Interest [Cr]", value=0.0)
                other_excl = st.number_input("Other Exclusions [Cr]", value=0.0)

            st.markdown("### Additions")
            col1, col2 = st.columns(2)
            with col1:
                kwa_released = st.number_input("KWA Arrears Released [Cr]", value=0.0)
            with col2:
                other_add = st.number_input("Other Additions [Cr]", value=0.0)

            submitted = st.form_submit_button("🔍 Validate NTI", use_container_width=True)
            if submitted:
                return {
                    'myt_baseline_nti': myt_baseline,
                    'base_income_from_accounts': base_income,
                    'exclusion_grant_clawback': grant_clawback,
                    'exclusion_led_bulbs': led_bulbs,
                    'exclusion_nilaavu_scheme': nilaavu,
                    'exclusion_provision_reversals': provision_rev,
                    'exclusion_kwa_unrealized': kwa_unrealized,
                    'addition_kwa_arrears_released': kwa_released,
                    'other_exclusions': other_excl,
                    'other_additions': other_add,
                    'claimed_nti': claimed_nti,
                }
        return None

    render_single_heuristic_page('nti', 'Non-Tariff Income', '💵', 'nti_form', 'nti', nti_form)


# =============================================================================
# PAGE: EDAMON-KOCHI LINE COMPENSATION (SBU-T only)
# =============================================================================

elif page == "Edamon-Kochi Line Compensation":
    from heuristics.transmission_heuristics import FY_2023_24_EDAMON_KOCHI_DEFAULTS as EK_DEFAULTS

    def ek_form(sbu):
        with st.form("ek_form"):
            st.info("💡 50% KSEB share amortized over 12 years + interest @ avg rate")
            claimed = st.number_input("Compensation Claimed [Cr]", value=EK_DEFAULTS['claimed_compensation'])
            myt = st.number_input("MYT Approved [Cr]", value=EK_DEFAULTS['myt_approved'])
            avg_rate = st.number_input("Avg Interest Rate (%)", value=EK_DEFAULTS['avg_interest_rate'] * 100) / 100
            submitted = st.form_submit_button("🔍 Calculate", use_container_width=True)
            if submitted:
                return {
                    'line_name': 'Edamon-Kochi 400kV Transmission Line',
                    'compensation_entries': EK_DEFAULTS['compensation_entries'],
                    'avg_interest_rate': avg_rate,
                    'claimed_compensation': claimed,
                    'myt_approved': myt,
                }
        return None

    render_single_heuristic_page('edamon_kochi_comp', 'Edamon-Kochi Line Compensation',
                                 '🔌', 'ek_form', 'ek', ek_form)


# =============================================================================
# PAGE: PUGALUR-THRISSUR LINE COMPENSATION (SBU-T only)
# =============================================================================

elif page == "Pugalur-Thrissur Line Compensation":
    from heuristics.transmission_heuristics import FY_2023_24_PUGALUR_THRISSUR_DEFAULTS as PT_DEFAULTS

    def pt_form(sbu):
        with st.form("pt_form"):
            st.info("💡 50% KSEB share amortized over 12 years + interest @ avg rate")
            claimed = st.number_input("Compensation Claimed [Cr]", value=PT_DEFAULTS['claimed_compensation'])
            myt = st.number_input("MYT Approved [Cr]", value=PT_DEFAULTS['myt_approved'])
            avg_rate = st.number_input("Avg Interest Rate (%)", value=PT_DEFAULTS['avg_interest_rate'] * 100) / 100
            submitted = st.form_submit_button("🔍 Calculate", use_container_width=True)
            if submitted:
                return {
                    'line_name': 'Pugalur-Thrissur 320kV HVDC Line',
                    'compensation_entries': PT_DEFAULTS['compensation_entries'],
                    'avg_interest_rate': avg_rate,
                    'claimed_compensation': claimed,
                    'myt_approved': myt,
                }
        return None

    render_single_heuristic_page('pugalur_thrissur_comp', 'Pugalur-Thrissur Line Compensation',
                                 '🔌', 'pt_form', 'pt', pt_form)


# =============================================================================
# PAGE: TRANSMISSION AVAILABILITY INCENTIVE (SBU-T only)
# =============================================================================

elif page == "Transmission Availability Incentive":
    from heuristics.transmission_heuristics import FY_2023_24_INCENTIVE_DEFAULTS as INC_DEFAULTS

    def inc_form(sbu):
        with st.form("inc_form"):
            st.info("💡 Incentive = (Actual - Target) × 0.5% × ARR (if actual > target + 1%)")
            col1, col2 = st.columns(2)
            with col1:
                target = st.number_input("Target Availability (%)", value=INC_DEFAULTS['target_availability'])
                actual = st.number_input("Actual Availability (%)", value=INC_DEFAULTS['actual_availability'])
                arr_excl = st.number_input("ARR excl. Incentive [Cr]", value=INC_DEFAULTS['arr_excluding_incentive'])
            with col2:
                claimed = st.number_input("Incentive Claimed [Cr]", value=INC_DEFAULTS['claimed_incentive'])
                revenue_gap = st.number_input("Unbridged Revenue Gap [Cr]", value=INC_DEFAULTS['unbridged_revenue_gap'])
            submitted = st.form_submit_button("🔍 Calculate Incentive", use_container_width=True)
            if submitted:
                return {
                    'target_availability': target, 'actual_availability': actual,
                    'arr_excluding_incentive': arr_excl,
                    'claimed_incentive': claimed,
                    'unbridged_revenue_gap': revenue_gap,
                }
        return None

    render_single_heuristic_page('trans_incentive', 'Transmission Availability Incentive',
                                 '🎯', 'inc_form', 'inc', inc_form)


# =============================================================================
# PAGE: T&D LOSS ANALYSIS (SBU-T and SBU-D)
# =============================================================================

elif page == "T&D Loss Analysis":
    st.title("📊 T&D Loss Analysis")
    sbu = get_sbu()
    sbu_code = get_sbu_key()

    if sbu_code == 'T':
        # Transmission Loss Analysis
        with st.form("td_loss_form"):
            st.markdown("### Transmission Loss")
            col1, col2 = st.columns(2)
            with col1:
                energy_input = st.number_input("Total Energy Input (MU)", value=31406.32)
                trans_loss = st.number_input("Transmission Loss (MU)", value=819.23)
            with col2:
                target_trans = st.number_input("MYT Target Trans Loss (%)", value=2.75)
                peak_demand = st.number_input("Peak Demand (MW)", value=5301.0)

            st.markdown("### T&D Reward")
            col1, col2 = st.columns(2)
            with col1:
                target_td = st.number_input("Approved T&D Loss (%)", value=13.83)
                actual_td = st.number_input("Actual T&D Loss (%)", value=12.10)
            with col2:
                avg_ppc = st.number_input("Avg Power Purchase Cost (₹/kWh)", value=4.50)
                claimed_reward = st.number_input("Claimed Reward [Cr]", value=131.59)

            submitted = st.form_submit_button("🔍 Analyze T&D Loss", use_container_width=True)
            if submitted:
                trans_params = {
                    'total_energy_input': energy_input,
                    'transmission_loss_mu': trans_loss,
                    'myt_approved_trans_loss_pct': target_trans,
                    'peak_demand_mw': peak_demand,
                }
                reward_params = {
                    'approved_td_loss_pct': target_td,
                    'actual_td_loss_pct': actual_td,
                    'total_energy_input_mu': energy_input,
                    'avg_power_purchase_cost_per_unit': avg_ppc,
                    'claimed_reward': claimed_reward,
                }

                if hasattr(sbu, 'run_td_loss_heuristics'):
                    results = sbu.run_td_loss_heuristics(trans_params, reward_params)

                    st.markdown("---")
                    st.markdown("## 🔍 T&D Loss Results")

                    for idx, result in enumerate(results):
                        render_heuristic_result(result, idx, 'tdloss')

    elif sbu_code == 'D':
        # Distribution Loss + Gain Sharing
        with st.form("dist_td_form"):
            st.markdown("### Distribution Loss")
            col1, col2 = st.columns(2)
            with col1:
                energy_input_dist = st.number_input("Energy Input to Distribution (MU)", value=27500.0)
                energy_sold = st.number_input("Energy Sold (MU)", value=24000.0)
            with col2:
                target_dist = st.number_input("MYT Target Dist Loss (%)", value=12.5)
                actual_loss_mu = st.number_input("Distribution Loss (MU)", value=3500.0)

            st.markdown("### T&D Loss Gain Sharing")
            col1, col2 = st.columns(2)
            with col1:
                target_td_total = st.number_input("Approved Total T&D Loss (%)", value=13.83)
                actual_td_total = st.number_input("Actual Total T&D Loss (%)", value=12.10)
            with col2:
                avg_ppc_dist = st.number_input("Avg Power Purchase Cost (₹/kWh)", value=4.50)
                claimed_share = st.number_input("Claimed Gain Sharing [Cr]", value=45.67)

            submitted = st.form_submit_button("🔍 Analyze Distribution Loss", use_container_width=True)
            if submitted:
                dist_params = {
                    'energy_input_to_dist_mu': energy_input_dist,
                    'energy_sold_mu': energy_sold,
                    'distribution_loss_mu': actual_loss_mu,
                    'myt_approved_dist_loss_pct': target_dist,
                }

                share_params = {
                    'approved_td_loss_pct': target_td_total,
                    'actual_td_loss_pct': actual_td_total,
                    'total_energy_input_mu': energy_input_dist,
                    'avg_power_purchase_cost_per_unit': avg_ppc_dist,
                    'utility_share_pct': 33.33,  # 1:2 sharing means utility gets 33.33%
                    'claimed_share': claimed_share,
                }

                st.info("📊 Distribution loss analysis and gain sharing calculation complete")
                # Results would be displayed here once heuristics are called


# =============================================================================
# PAGE: T&D LOSS GAIN SHARING (SBU-D only)
# =============================================================================

elif page == "Sharing of Gains due to T&D Loss Reduction":
    def td_share_form(sbu):
        with st.form("td_share_form"):
            st.info("💡 Regulation 14/73: 2:1 sharing (67% consumer, 33% utility)")
            col1, col2 = st.columns(2)
            with col1:
                approved_td = st.number_input("Approved T&D Loss (%)", value=13.83)
                actual_td = st.number_input("Actual T&D Loss (%)", value=12.10)
            with col2:
                total_input = st.number_input("Total Energy Input (MU)", value=31406.32)
                avg_ppc = st.number_input("Avg PPC (₹/kWh)", value=4.50)
            claimed_share = st.number_input("Claimed Gain Sharing [Cr]", value=45.67)
            submitted = st.form_submit_button("🔍 Calculate Gain Sharing", use_container_width=True)
            if submitted:
                return {
                    'approved_td_loss_pct': approved_td,
                    'actual_td_loss_pct': actual_td,
                    'total_energy_input_mu': total_input,
                    'avg_power_purchase_cost_per_unit': avg_ppc,
                    'utility_share_pct': 33.33,
                    'claimed_share': claimed_share,
                }
        return None

    render_single_heuristic_page('td_loss_sharing', 'Sharing of Gains due to T&D Loss Reduction',
                                 '📊', 'td_share_form', 'td_share', td_share_form)


# =============================================================================
# PAGE: REPAYMENT OF MASTER TRUST BONDS (SBU-D only)
# =============================================================================

elif page == "Repayment of Master Trust Bonds":
    st.info("⚠️ This is typically handled in the Master Trust Obligations page")
    st.markdown("Please use the **Master Trust Obligations** page for bond repayment calculations.")


# =============================================================================
# FOOTER
# =============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("**KSERC Truing-Up DSS v6.0**")
st.sidebar.markdown("Complete SBU-G, SBU-T, SBU-D Integration")
st.sidebar.markdown("© 2026 | Prof. Madhavan | XIME Kochi")
