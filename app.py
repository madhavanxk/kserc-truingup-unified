"""
KSERC Truing-Up Decision Support System
==========================================
Unified Streamlit Application for SBU-G, SBU-T (and future SBU-D)

Features:
  - SBU selector in sidebar (G/T/D)
  - Dynamic page list based on selected SBU
  - Shared staff review UI pattern across all pages
  - Dashboard with traffic light summary
  - Aggregation view with drill-down
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Import unified modules
from sbu_base import SBU_Generation, SBU_Transmission, create_sbu
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
    Reused across ALL pages — eliminates massive duplication.

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
            new_flag = st.selectbox("New Flag:", ["GREEN", "YELLOW", "RED"], key=f"flag_{prefix}_{idx}")
            staff_name = st.text_input("Reviewed By:", key=f"staff_flag_{prefix}_{idx}")
        with col2:
            justification = st.text_area("Justification (Required):", key=f"just_flag_{prefix}_{idx}", height=100)
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
                "New Approved Amount [Cr]:",
                value=float(result.get('recommended_amount') or 0),
                key=f"amt_{prefix}_{idx}"
            )
            staff_name = st.text_input("Reviewed By:", key=f"staff_amt_{prefix}_{idx}")
        with col2:
            justification = st.text_area("Justification (Required):", key=f"just_amt_{prefix}_{idx}", height=100)
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
    Template for pages with multiple heuristics (O&M, IFC, MasterTrust).
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

# Add T&D Loss page for SBU-T
if get_sbu_key() == 'T':
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
    st.title(f"{sbu.sbu_name} — Truing-Up Dashboard")

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

    # T&D Loss card for SBU-T
    if get_sbu_key() == 'T':
        st.markdown("---")
        st.markdown("### 📊 T&D Loss Analysis")
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
                st.write(f"- {item['line_item']}: {item['heuristic_name']} [{get_flag_emoji(item['flag'])}]")
    else:
        st.success("✅ All reviews complete — Aggregation ready")
        total_arr = sbu.calculate_total_arr()

        st.markdown("### 💰 Approved Amounts")
        for i in range(0, len(line_item_configs), 3):
            cols = st.columns(3)
            for col_idx, item_cfg in enumerate(line_item_configs[i:i+3]):
                with cols[col_idx]:
                    li = sbu.get_line_item(item_cfg['key'])
                    approved = li.get_approved_amount() if li else None
                    label = f"{item_cfg['icon']} {item_cfg['name']}"
                    if item_cfg.get('is_expense') is False:
                        label += " (deducted)"
                    st.metric(label, f"₹{approved:.2f} Cr" if approved else "N/A")

        st.markdown("---")
        st.metric("**🎯 Net ARR**", f"₹{total_arr:.2f} Cr")

        # Drill-down
        st.markdown("---")
        st.markdown("### 🔍 Detailed Breakdown")
        drill_down = sbu.get_drill_down_data()
        for line_detail in drill_down['line_items_detail']:
            amt = line_detail['approved_amount']
            label = (f"{get_flag_emoji(line_detail['overall_flag'])} {line_detail['name']}: "
                     f"₹{amt:.2f} Cr" if amt else
                     f"{get_flag_emoji(line_detail['overall_flag'])} {line_detail['name']}: N/A")
            with st.expander(label, expanded=False):
                rs = line_detail['review_status']
                st.write(f"**Status:** {rs['accepted']} Accepted, {rs['overridden']} Overridden, {rs['pending']} Pending")
                for heur in line_detail['heuristics']:
                    primary_tag = "**[PRIMARY]**" if heur['is_primary'] else ""
                    st.write(f"- {get_flag_emoji(heur['flag'])} {heur['id']}: {heur['name']} {primary_tag}")


# =============================================================================
# PAGE: O&M EXPENSES (SBU-G: multi-heuristic, SBU-T: single-heuristic)
# =============================================================================

elif page == "O&M Expenses":
    sbu_code = get_sbu_key()

    if sbu_code == 'G':
        def om_g_form(sbu):
            with st.form("om_form"):
                st.markdown("### Section 1: Inflation Indices")
                col1, col2 = st.columns(2)
                with col1:
                    cpi_old = st.number_input("CPI (Previous Year)", value=397.20)
                    cpi_new = st.number_input("CPI (Current Year)", value=405.20)
                with col2:
                    wpi_old = st.number_input("WPI (Previous Year)", value=151.40)
                    wpi_new = st.number_input("WPI (Current Year)", value=153.10)

                st.markdown("### Section 2: Existing Stations")
                col1, col2 = st.columns(2)
                with col1:
                    base_year_om = st.number_input("Base Year O&M (2021-22)", value=156.16, disabled=True)
                    inflation_2022_23 = st.number_input("Inflation 2022-23 (%)", value=7.06, disabled=True)
                with col2:
                    inflation_2023_24 = st.number_input("Inflation 2023-24 (%)", value=3.41, disabled=True)
                    claimed_existing = st.number_input("O&M Claimed (Existing) [Cr]", value=185.0)

                st.markdown("### Section 3: New Stations")
                new_stations_allowable = st.number_input("New Stations Allowable O&M [Cr]", value=5.11)

                st.markdown("### Section 4: Actual Expenditure")
                col1, col2, col3 = st.columns(3)
                with col1:
                    actual_employee = st.number_input("Employee Cost [Cr]", value=220.12)
                with col2:
                    actual_ag = st.number_input("A&G [Cr]", value=48.32)
                with col3:
                    actual_rm = st.number_input("R&M [Cr]", value=22.89)

                st.markdown("### Section 5: Pay Revision")
                pay_revision = st.checkbox("Pay Revision Implemented?")

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

        render_multi_heuristic_page('om_expenses', 'O&M Expenses', '📄', 'om_form', 'om', om_g_form)

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
                                     '📄', 'om_trans_form', 'om_t', om_t_form)


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
# PAGE: INTEREST & FINANCE CHARGES (shared)
# =============================================================================

elif page == "Interest & Finance Charges":
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
                opening_gfa_excl_land = st.number_input("GFA excl. land [Cr]", value=5453.56)
            with col2:
                sbi_eblr_rate = st.number_input("SBI EBLR Rate (%)", value=9.15)
                claimed_wc_interest = st.number_input("WC Interest Claimed [Cr]", value=9.21)

            st.markdown("### Interest on GPF (IFC-GPF-01)")
            col1, col2 = st.columns(2)
            with col1:
                opening_gpf = st.number_input("Opening GPF [Cr]", value=3000.09)
                closing_gpf = st.number_input("Closing GPF [Cr]", value=2852.48)
            with col2:
                gpf_rate = st.number_input("GPF Rate (%)", value=7.10, disabled=True)
                sbu_ratio = st.number_input("SBU Allocation (%)", value=5.40)
                claimed_gpf = st.number_input("GPF Interest Claimed [Cr]", value=9.94)

            st.markdown("### Other Charges (IFC-OTH-02)")
            col1, col2 = st.columns(2)
            with col1:
                claimed_gbi = st.number_input("GBI [Cr]", value=0.19)
            with col2:
                claimed_bank = st.number_input("Bank Charges [Cr]", value=0.28)

            submitted = st.form_submit_button("🔍 Calculate IFC", use_container_width=True)
            if submitted:
                return {
                    'opening_normative_loan': opening_normative_loan,
                    'gfa_additions': gfa_additions, 'depreciation': depreciation,
                    'opening_interest_rate': opening_interest_rate,
                    'claimed_interest': claimed_interest,
                    'approved_om_expenses': approved_om_expenses,
                    'opening_gfa_excl_land': opening_gfa_excl_land,
                    'sbi_eblr_rate': sbi_eblr_rate,
                    'claimed_wc_interest': claimed_wc_interest,
                    'opening_gpf_balance_company': opening_gpf,
                    'closing_gpf_balance_company': closing_gpf,
                    'gpf_interest_rate': gpf_rate,
                    'sbu_allocation_ratio': sbu_ratio,
                    'claimed_gpf_interest_sbu': claimed_gpf,
                    'claimed_gbi': claimed_gbi,
                    'claimed_bank_charges': claimed_bank,
                }
        return None

    render_multi_heuristic_page('ifc', 'Interest & Finance Charges', '🏦', 'ifc_form', 'ifc', ifc_form)


# =============================================================================
# PAGE: MASTER TRUST (shared)
# =============================================================================

elif page == "Master Trust Obligations":
    def mt_form(sbu):
        with st.form("mt_form"):
            st.info("💡 20-year bond @ 10% issued 01.04.2017 for ₹8144 Cr")

            st.markdown("### Bond Interest (MT-BOND-01)")
            col1, col2 = st.columns(2)
            with col1:
                total_bond_interest = st.number_input("Total Bond Interest [Cr]", value=570.08)
                sbu_ratio_bond = st.number_input("SBU Allocation (%)", value=5.59, key="sbu_bond")
            with col2:
                claimed_bond = st.number_input("Bond Interest Claimed [Cr]", value=31.88)

            st.markdown("### Principal Repayment (MT-REPAY-01)")
            col1, col2 = st.columns(2)
            with col1:
                annual_repayment = st.number_input("Annual Repayment (Fixed) [Cr]", value=407.20, disabled=True)
                sbu_ratio_repay = st.number_input("SBU Allocation (%)", value=5.40, key="sbu_repay")
            with col2:
                claimed_repay = st.number_input("Repayment Claimed [Cr]", value=21.99)

            st.markdown("### Additional Contribution (MT-ADD-01)")
            col1, col2 = st.columns(2)
            with col1:
                actuarial = st.number_input("Actuarial Liability [Cr]", value=1468.96)
                provisional_cap = st.number_input("KSERC Provisional Cap [Cr]", value=400.0)
            with col2:
                sbu_ratio_add = st.number_input("SBU Allocation (%)", value=5.40, key="sbu_add")
                claimed_add = st.number_input("Additional Claimed [Cr]", value=21.60)

            col1, col2 = st.columns(2)
            with col1:
                actuarial_submitted = st.checkbox("Actuarial report submitted?")
            with col2:
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

    render_multi_heuristic_page('master_trust', 'Master Trust Obligations', '🏛️', 'mt_form', 'mt', mt_form)


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

elif page in ["Intangible Assets", "Intangible Assets (Software)"]:
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
            st.info("💡 NTI is DEDUCTED from ARR — higher NTI reduces tariff burden")
            col1, col2 = st.columns(2)
            with col1:
                myt_baseline = st.number_input("MYT Baseline NTI [Cr]", value=10.81)
                base_income = st.number_input("Base Income (Accounts) [Cr]", value=33.21)
            with col2:
                claimed_nti = st.number_input("NTI Claimed [Cr]", value=40.21)

            st.markdown("### Exclusions")
            col1, col2, col3 = st.columns(3)
            with col1:
                ex_grant = st.number_input("Grant Claw-back [Cr]", value=0.0)
                ex_led = st.number_input("LED Bulb Costs [Cr]", value=0.0)
            with col2:
                ex_nilaavu = st.number_input("Nilaavu Scheme [Cr]", value=0.0)
                ex_provision = st.number_input("Provision Reversals [Cr]", value=0.0)
            with col3:
                ex_kwa = st.number_input("KWA Unrealized [Cr]", value=0.0)
                other_ex = st.number_input("Other Exclusions [Cr]", value=0.0)

            st.markdown("### Additions")
            col1, col2 = st.columns(2)
            with col1:
                add_kwa = st.number_input("KWA Arrears Released [Cr]", value=0.0)
            with col2:
                other_add = st.number_input("Other Additions [Cr]", value=0.0)

            submitted = st.form_submit_button("🔍 Calculate NTI", use_container_width=True)
            if submitted:
                return {
                    'myt_baseline_nti': myt_baseline, 'base_income_from_accounts': base_income,
                    'exclusion_grant_clawback': ex_grant, 'exclusion_led_bulbs': ex_led,
                    'exclusion_nilaavu_scheme': ex_nilaavu,
                    'exclusion_provision_reversals': ex_provision,
                    'exclusion_kwa_unrealized': ex_kwa,
                    'addition_kwa_arrears_released': add_kwa,
                    'other_exclusions': other_ex, 'other_additions': other_add,
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
            st.warning("⚠️ FY 2023-24: KSERC DEFERRED incentive due to ₹6408 Cr revenue gap")
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
# PAGE: T&D LOSS ANALYSIS (SBU-T only)
# =============================================================================

elif page == "T&D Loss Analysis":
    st.title("📊 T&D Loss Analysis")
    sbu = get_sbu()

    if not hasattr(sbu, 'run_td_loss_heuristics'):
        st.warning("T&D Loss Analysis is only available for SBU-T")
    else:
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
                avg_ppc = st.number_input("Avg Power Purchase Cost (₹/unit)", value=4.50)
                claimed_reward = st.number_input("Reward Claimed [Cr]", value=131.59)

            submitted = st.form_submit_button("🔍 Run T&D Loss Analysis", use_container_width=True)

        if submitted:
            td_results = sbu.run_td_loss_heuristics(
                trans_loss_params={
                    'total_energy_input': energy_input,
                    'transmission_loss_mu': trans_loss,
                    'myt_approved_trans_loss_pct': target_trans,
                    'peak_demand_mw': peak_demand,
                },
                td_reward_params={
                    'approved_td_loss_pct': target_td,
                    'actual_td_loss_pct': actual_td,
                    'total_energy_input_mu': energy_input,
                    'avg_power_purchase_cost_per_unit': avg_ppc,
                    'claimed_reward': claimed_reward,
                }
            )
            st.success("✅ T&D Loss analysis completed!")

        # Display results
        if hasattr(sbu, 'td_loss_results') and sbu.td_loss_results:
            st.markdown("---")
            st.markdown("## 🔍 Results")
            for idx, result in enumerate(sbu.td_loss_results):
                render_heuristic_result(result, idx, 'td')