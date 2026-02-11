"""
Unified Line Item Classes (Tier 2)
====================================
All LineItem classes for SBU-G, SBU-T (and future SBU-D).

Each class inherits from LineItemBase and only implements:
  - run_heuristic(inputs)      for single-heuristic items
  - run_all_heuristics(inputs) for multi-heuristic items

The 4 boilerplate methods (get_approved_amount, get_overall_flag,
check_review_status, get_summary) are inherited from LineItemBase.

Classes:
  SHARED (used by multiple SBUs):
    - LineItem_ROE              (ROE-01)
    - LineItem_Depreciation     (DEP-GEN-01)
    - LineItem_IFC              (IFC-LTL-01, IFC-WC-01, IFC-GPF-01, IFC-OTH-02)
    - LineItem_MasterTrust      (MT-BOND-01, MT-REPAY-01, MT-ADD-01)
    - LineItem_OtherExpenses    (OTHER-EXP-01)
    - LineItem_ExceptionalItems (EXC-01)
    - LineItem_NTI              (NTI-01)
    - LineItem_IntangibleAssets (INTANG-01)

  SBU-G ONLY:
    - LineItem_OM_Expenses      (OM-INFL-01, OM-NORM-01, OM-APPORT-01, EMP-PAYREV-01)
    - LineItem_FuelCosts        (FUEL-01)

  SBU-T ONLY:
    - LineItem_TransOM          (OM-TRANS-NORM-01)
    - LineItem_TransComp        (TRANS-COMP-01)
    - LineItem_TransIncentive   (TRANS-INCENT-01)
"""

from typing import Dict, List, Optional
from sbu_base import LineItemBase

# --- Shared heuristic imports (used by both SBU-G and SBU-T) ---
from heuristics.roe_heuristics import heuristic_ROE_01
from heuristics.depreciation_heuristics import heuristic_DEP_GEN_01
from heuristics.ifc_heuristics import (
    heuristic_IFC_LTL_01,
    heuristic_IFC_WC_01,
    heuristic_IFC_GPF_01,
    heuristic_IFC_OTH_02
)
from heuristics.master_trust_heuristics import (
    heuristic_MT_BOND_01,
    heuristic_MT_REPAY_01,
    heuristic_MT_ADD_01
)
from heuristics.other_items_heuristics import (
    heuristic_OTHER_EXP_01,
    heuristic_EXC_01
)
from heuristics.nti_heuristics import heuristic_NTI_01
from heuristics.intangible_heuristics import heuristic_INTANG_01

# --- SBU-G only imports ---
from heuristics.om_heuristics import (
    heuristic_OM_INFL_01,
    heuristic_OM_NORM_01,
    heuristic_OM_APPORT_01,
    heuristic_EMP_PAYREV_01
)
from heuristics.fuel_heuristics import heuristic_FUEL_01

# --- SBU-T only imports ---
from heuristics.transmission_heuristics import (
    heuristic_OM_TRANS_NORM_01,
    heuristic_TRANS_COMP_01,
    heuristic_TRANS_INCENT_01
)

# --- SBU-D only imports ---
from heuristics.distribution_heuristics import (
    heuristic_PP_COST_01,
    heuristic_OM_DIST_NORM_01,
    heuristic_IFC_SD_01,
    heuristic_IFC_CC_01,
    heuristic_IFC_OTH_D_01,
    heuristic_DIST_LOSS_01,
    heuristic_TD_SHARE_01,
)


# =============================================================================
# SHARED LINE ITEMS (used by SBU-G and SBU-T)
# =============================================================================

class LineItem_ROE(LineItemBase):
    """
    Return on Equity Line Item
    Heuristic: ROE-01 (single, primary)
    Used by: SBU-G (equity â‚¹831.27 Cr), SBU-T (equity â‚¹857.05 Cr)
    """

    def __init__(self):
        super().__init__("Return on Equity", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_ROE_01(
            inputs['equity_capital'],
            inputs['roe_rate'],
            inputs['claimed_roe'],
            inputs.get('equity_infusion_during_year', 0.0),
            inputs.get('equity_infusion_details', None)
        )
        self.heuristic_result = result
        return result


class LineItem_Depreciation(LineItemBase):
    """
    Depreciation Line Item
    Heuristic: DEP-GEN-01 (single, primary)
    Used by: SBU-G and SBU-T
    """

    def __init__(self):
        super().__init__("Depreciation", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_DEP_GEN_01(
            inputs['gfa_opening_total'],
            inputs['gfa_13_to_30_years'],
            inputs['land_13_to_30_years'],
            inputs['grants_13_to_30_years'],
            inputs['gfa_below_13_years'],
            inputs['land_below_13_years'],
            inputs['grants_below_13_years'],
            inputs['asset_additions'],
            inputs.get('asset_withdrawals', 0.0),
            inputs['claimed_depreciation']
        )
        self.heuristic_result = result
        return result


class LineItem_IFC(LineItemBase):
    """
    Interest & Finance Charges Line Item
    Heuristics: IFC-LTL-01, IFC-WC-01, IFC-GPF-01, IFC-OTH-02 (multi, all primary)
    Used by: SBU-G and SBU-T (with different WC/OTH parameters via sbu_config)
    Total IFC = sum of all 4 components
    """

    def __init__(self):
        super().__init__("Interest & Finance Charges", pattern="multi")

    def run_all_heuristics(self, inputs: Dict) -> List[Dict]:
        results = []

        # IFC-LTL-01: Interest on Long-Term Loans
        result_ltl = heuristic_IFC_LTL_01(
            inputs['opening_normative_loan'],
            inputs['gfa_additions'],
            inputs['depreciation'],
            inputs['opening_interest_rate'],
            inputs['claimed_interest'],
            inputs.get('disputed_claims', 0.0),
            inputs.get('highest_loan_rate', None)
        )
        results.append(result_ltl)

        # IFC-WC-01: Interest on Working Capital
        result_wc = heuristic_IFC_WC_01(
            inputs['approved_om_expenses'],
            inputs['opening_gfa_excl_land'],
            inputs['sbi_eblr_rate'],
            inputs['claimed_wc_interest']
        )
        results.append(result_wc)

        # IFC-GPF-01: Interest on GPF
        result_gpf = heuristic_IFC_GPF_01(
            inputs['opening_gpf_balance_company'],
            inputs['closing_gpf_balance_company'],
            inputs['gpf_interest_rate'],
            inputs['sbu_allocation_ratio'],
            inputs['claimed_gpf_interest_sbu']
        )
        results.append(result_gpf)

        # IFC-OTH-02: Other Charges (GBI + Bank Charges)
        result_oth = heuristic_IFC_OTH_02(
            inputs['claimed_gbi'],
            inputs['claimed_bank_charges']
        )
        results.append(result_oth)

        self.heuristic_results = results
        return results


class LineItem_MasterTrust(LineItemBase):
    """
    Master Trust Obligations Line Item
    Heuristics: MT-BOND-01, MT-REPAY-01, MT-ADD-01 (multi, all primary)
    Used by: SBU-G and SBU-T
    Total = sum of all 3 components
    """

    def __init__(self):
        super().__init__("Master Trust Obligations", pattern="multi")

    def run_all_heuristics(self, inputs: Dict) -> List[Dict]:
        results = []

        # MT-BOND-01: Interest on Master Trust Bonds
        result_bond = heuristic_MT_BOND_01(
            inputs['total_bond_interest'],
            inputs['sbu_allocation_ratio'],
            inputs['claimed_bond_interest_sbu']
        )
        results.append(result_bond)

        # MT-REPAY-01: Repayment of Master Trust Bond Principal
        result_repay = heuristic_MT_REPAY_01(
            inputs['annual_principal_repayment'],
            inputs['sbu_allocation_ratio'],
            inputs['claimed_principal_repayment_sbu']
        )
        results.append(result_repay)

        # MT-ADD-01: Additional Contribution to Master Trust
        result_add = heuristic_MT_ADD_01(
            inputs['actuarial_liability_current_year'],
            inputs['provisional_cap'],
            inputs['sbu_allocation_ratio'],
            inputs['claimed_additional_contribution_sbu'],
            inputs['actuarial_report_submitted'],
            inputs['govt_approval_obtained']
        )
        results.append(result_add)

        self.heuristic_results = results
        return results


class LineItem_OtherExpenses(LineItemBase):
    """
    Other Expenses Line Item
    Heuristic: OTHER-EXP-01 (single, primary)
    Used by: SBU-G and SBU-T
    """

    def __init__(self):
        super().__init__("Other Expenses", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_OTHER_EXP_01(
            inputs.get('claimed_discount_to_consumers', 0.0),
            inputs.get('claimed_flood_losses', 0.0),
            inputs.get('claimed_misc_writeoffs', 0.0),
            inputs.get('flood_supporting_docs', False),
            inputs.get('writeoff_appeal_orders', False)
        )
        self.heuristic_result = result
        return result


class LineItem_ExceptionalItems(LineItemBase):
    """
    Exceptional Items Line Item
    Heuristic: EXC-01 (single, primary)
    Used by: SBU-G and SBU-T
    """

    def __init__(self):
        super().__init__("Exceptional Items", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_EXC_01(
            inputs.get('claimed_calamity_rm', 0.0),
            inputs.get('claimed_govt_loss_takeover', 0.0),
            inputs.get('separate_account_code', False),
            inputs.get('calamity_supporting_docs', False)
        )
        self.heuristic_result = result
        return result


class LineItem_NTI(LineItemBase):
    """
    Non-Tariff Income Line Item
    Heuristic: NTI-01 (single, primary)
    Used by: SBU-G and SBU-T
    Note: NTI is DEDUCTED from ARR (is_expense=False in config)
    """

    def __init__(self):
        super().__init__("Non-Tariff Income", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_NTI_01(
            inputs['myt_baseline_nti'],
            inputs['base_income_from_accounts'],
            inputs.get('exclusion_grant_clawback', 0.0),
            inputs.get('exclusion_led_bulbs', 0.0),
            inputs.get('exclusion_nilaavu_scheme', 0.0),
            inputs.get('exclusion_provision_reversals', 0.0),
            inputs.get('exclusion_kwa_unrealized', 0.0),
            inputs.get('addition_kwa_arrears_released', 0.0),
            inputs.get('other_exclusions', 0.0),
            inputs.get('other_additions', 0.0),
            inputs.get('claimed_nti', 0.0)
        )
        self.heuristic_result = result
        return result


class LineItem_IntangibleAssets(LineItemBase):
    """
    Intangible Assets (Software Amortization) Line Item
    Heuristic: INTANG-01 (single, primary)
    Used by: SBU-G and SBU-T
    Note: Typically DISALLOWED to avoid double counting with O&M
    """

    def __init__(self):
        super().__init__("Intangible Assets", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_INTANG_01(
            inputs.get('software_employee_costs_capitalized', 0.0),
            inputs.get('software_amortization_claimed', 0.0),
            inputs.get('software_supporting_docs_provided', False),
            inputs.get('software_employees_additional_to_norms', False),
            inputs.get('purchased_software_licenses', 0.0),
            inputs.get('patents_ip', 0.0),
            inputs.get('other_intangibles', 0.0),
            inputs.get('other_intangibles_amortization', 0.0),
            inputs.get('other_supporting_docs_provided', False),
            inputs.get('total_claimed_amortization', 0.0),
            inputs.get('previous_year_amortization', 0.0)
        )
        self.heuristic_result = result
        return result


# =============================================================================
# SBU-G ONLY LINE ITEMS
# =============================================================================

class LineItem_OM_Expenses(LineItemBase):
    """
    O&M Expenses Line Item (SBU-G: Station-wise norms)
    Heuristics: OM-INFL-01, OM-NORM-01, OM-APPORT-01, EMP-PAYREV-01 (multi)
    Primary: OM-NORM-01 (determines approved amount)
    SBU-G ONLY â€” SBU-T uses LineItem_TransOM instead
    """

    def __init__(self):
        super().__init__("O&M Expenses", pattern="multi")

    def run_all_heuristics(self, inputs: Dict) -> List[Dict]:
        results = []

        # Layer 1: OM-INFL-01 (independent)
        result_infl = heuristic_OM_INFL_01(
            inputs['cpi_old'],
            inputs['cpi_new'],
            inputs['wpi_old'],
            inputs['wpi_new']
        )
        results.append(result_infl)
        inflation_2024_25 = result_infl['output_value']

        # Layer 2: OM-NORM-01 (depends on OM-INFL-01) â€” PRIMARY
        result_norm = heuristic_OM_NORM_01(
            inputs['base_year_om'],
            inputs['inflation_2022_23'],
            inputs['inflation_2023_24'],
            inflation_2024_25,
            inputs['claimed_existing'],
            inputs.get('new_stations_allowable', 0.0)
        )
        results.append(result_norm)
        total_om_approved = result_norm['recommended_amount']

        # Layer 3: OM-APPORT-01 (depends on OM-NORM-01)
        result_apport = heuristic_OM_APPORT_01(
            total_om_approved,
            inputs['actual_employee'],
            inputs['actual_ag'],
            inputs['actual_rm']
        )
        results.append(result_apport)

        # Layer 4: EMP-PAYREV-01 (depends on OM-APPORT-01)
        normative_employee = total_om_approved * 0.7703
        result_payrev = heuristic_EMP_PAYREV_01(
            normative_employee,
            inputs['actual_employee'],
            inputs.get('pay_revision', False),
            inputs.get('pay_revision_details', None)
        )
        results.append(result_payrev)

        self.heuristic_results = results
        return results


class LineItem_FuelCosts(LineItemBase):
    """
    Fuel Costs Line Item
    Heuristic: FUEL-01 (single, primary)
    SBU-G ONLY â€” SBU-T has no fuel costs
    """

    def __init__(self):
        super().__init__("Fuel Costs", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_FUEL_01(
            inputs.get('heavy_fuel_oil', 0.0),
            inputs.get('hsd_oil', 0.0),
            inputs.get('lube_oil', 0.0),
            inputs.get('lubricants_consumables', 0.0),
            inputs.get('total_claimed_fuel_cost', 0.0),
            inputs.get('previous_year_fuel_cost', 0.0)
        )
        self.heuristic_result = result
        return result


# =============================================================================
# SBU-T ONLY LINE ITEMS
# =============================================================================

class LineItem_TransOM(LineItemBase):
    """
    O&M Expenses Line Item (SBU-T: Bays/MVA/CktKm formula)
    Heuristic: OM-TRANS-NORM-01 (single, primary)
    SBU-T ONLY â€” SBU-G uses LineItem_OM_Expenses instead
    """

    def __init__(self):
        super().__init__("O&M Expenses (Transmission)", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_OM_TRANS_NORM_01(
            norm_per_bay=inputs.get('norm_per_bay', 7.884),
            norm_per_mva=inputs.get('norm_per_mva', 0.872),
            norm_per_cktkm=inputs.get('norm_per_cktkm', 1.592),
            opening_bays=int(inputs.get('opening_bays', 2905)),
            opening_mva=float(inputs.get('opening_mva', 25344.5)),
            opening_cktkm=float(inputs.get('opening_cktkm', 10633.90)),
            added_bays=int(inputs.get('added_bays', 24)),
            added_mva=float(inputs.get('added_mva', 785.0)),
            added_cktkm=float(inputs.get('added_cktkm', 166.23)),
            myt_approved_om=float(inputs.get('myt_approved_om', 644.81)),
            actual_om_accounts=float(inputs.get('actual_om_accounts', 588.95)),
            claimed_om=float(inputs.get('claimed_om', 625.20)),
            escalation_2022_23=float(inputs.get('escalation_2022_23', 0.0706)),
            escalation_2023_24=float(inputs.get('escalation_2023_24', 0.0341)),
        )
        self.heuristic_result = result
        return result


class LineItem_TransComp(LineItemBase):
    """
    Transmission Line Compensation Line Item
    Heuristic: TRANS-COMP-01 (single, primary)
    SBU-T ONLY â€” Edamon-Kochi or Pugalur-Thrissur
    Note: Two instances created, one per line
    """

    def __init__(self, line_name: str = ""):
        display_name = f"Line Compensation ({line_name})" if line_name else "Line Compensation"
        super().__init__(display_name, pattern="single")
        self.line_name = line_name

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_TRANS_COMP_01(
            line_name=inputs.get('line_name', self.line_name),
            compensation_entries=inputs.get('compensation_entries', []),
            avg_interest_rate=inputs.get('avg_interest_rate', 0.0861),
            claimed_compensation=inputs.get('claimed_compensation', 0.0),
            myt_approved=inputs.get('myt_approved', 0.0),
            assessment_year=inputs.get('assessment_year', '2023-24'),
        )
        self.heuristic_result = result
        return result


class LineItem_TransIncentive(LineItemBase):
    """
    Transmission Availability Incentive Line Item
    Heuristic: TRANS-INCENT-01 (single, primary)
    SBU-T ONLY
    Note: May be deferred if unbridged revenue gap is too large
    """

    def __init__(self):
        super().__init__("Transmission Availability Incentive", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_TRANS_INCENT_01(
            target_availability=float(inputs.get('target_availability', 98.50)),
            actual_availability=float(inputs.get('actual_availability', 0.0)),
            sldc_certified=inputs.get('sldc_certified', True),
            arr_excluding_incentive=float(inputs.get('arr_excluding_incentive', 0.0)),
            claimed_incentive=float(inputs.get('claimed_incentive', 0.0)),
            unbridged_revenue_gap=float(inputs.get('unbridged_revenue_gap', 0.0)),
            revenue_gap_threshold=float(inputs.get('revenue_gap_threshold', 5000.0)),
        )
        self.heuristic_result = result
        return result


# =============================================================================
# SBU-D ONLY LINE ITEMS
# =============================================================================

class LineItem_PowerPurchase(LineItemBase):
    """
    Power Purchase Cost Line Item
    Heuristic: PP-COST-01 (single, primary)
    SBU-D ONLY — Largest cost component (~60% of ARR)

    Validates 13 source categories + ISTS charges:
      CGS, RE IPPs, SECI Wind, Solar outside, Prosumer/Captive,
      RGCCPP fixed, Maithon/DVC, DBFOO approved, DBFOO unapproved,
      Medium-term, Short-term, Exchanges, DSM, Banking/SWAP,
      ISTS charges, surplus sale expenditure

    Key flags:
      - Banking: cash-only basis (reject provisions)
      - Exchanges TAM: flag if rate > avg PP cost without prior approval
      - ISTS: approve as CERC-governed but flag increase
    """

    def __init__(self):
        super().__init__("Power Purchase Cost", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_PP_COST_01(
            # Source-wise costs (₹ Cr) - all 13 categories
            cgs_cost=float(inputs.get('cgs_cost', 4731.09)),
            re_ipps_cost=float(inputs.get('re_ipps_cost', 230.51)),
            seci_wind_cost=float(inputs.get('seci_wind_cost', 61.75)),
            solar_outside_cost=float(inputs.get('solar_outside_cost', 47.33)),
            prosumer_captive_cost=float(inputs.get('prosumer_captive_cost', 25.00)),
            rgccpp_fixed_cost=float(inputs.get('rgccpp_fixed_cost', 70.65)),
            maithon_dvc_cost=float(inputs.get('maithon_dvc_cost', 1495.45)),
            dbfoo_approved_cost=float(inputs.get('dbfoo_approved_cost', 872.15)),
            dbfoo_unapproved_cost=float(inputs.get('dbfoo_unapproved_cost', 373.50)),
            medium_term_cost=float(inputs.get('medium_term_cost', 364.19)),
            short_term_cost=float(inputs.get('short_term_cost', 718.44)),
            exchange_cost=float(inputs.get('exchange_cost', 2123.16)),
            dsm_cost=float(inputs.get('dsm_cost', 206.67)),
            banking_cash_cost=float(inputs.get('banking_cash_cost', 5.09)),
            banking_provision=float(inputs.get('banking_provision', 209.13)),
            ists_charges=float(inputs.get('ists_charges', 1448.27)),
            surplus_sale_cost=float(inputs.get('surplus_sale_cost', 0.25)),
            # SBU-G and SBU-T transfer costs (upstream)
            sbu_g_transfer=float(inputs.get('sbu_g_transfer', 598.70)),
            sbu_t_transfer=float(inputs.get('sbu_t_transfer', 1505.80)),
            # Exchange breakdown for TAM flagging
            exchange_tam_cost=float(inputs.get('exchange_tam_cost', 857.09)),
            exchange_tam_rate=float(inputs.get('exchange_tam_rate', 8.30)),
            avg_pp_rate_approved=float(inputs.get('avg_pp_rate_approved', 4.70)),
            # Energy quantum
            total_pp_mu=float(inputs.get('total_pp_mu', 25711.29)),
            ists_loss_pct=float(inputs.get('ists_loss_pct', 3.47)),
        )
        self.heuristic_result = result
        return result


class LineItem_DistOM(LineItemBase):
    """
    O&M Expenses Line Item (SBU-D: 5-parameter formula + 4% GFA R&M)
    Heuristic: OM-DIST-NORM-01 (single, primary)
    SBU-D ONLY

    Employee + A&G: 5 parameters (Regulation 80, Annexure-7.2c):
      - No. of consumers (20%)
      - No. of distribution transformers (25%)
      - Length of HT lines in km (20%)
      - Length of LT lines in km (20%)
      - Energy sales in MU (15%)
    Norms escalated by actual CPI:WPI (70:30) from base year 2021-22.

    R&M: 4% of opening GFA (excl land, excl derecognized calamity assets)
    """

    def __init__(self):
        super().__init__("O&M Expenses (Distribution)", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_OM_DIST_NORM_01(
            num_consumers=int(inputs.get('num_consumers', 13648851)),
            num_dtrs=int(inputs.get('num_dtrs', 87911)),
            ht_line_km=float(inputs.get('ht_line_km', 70269.0)),
            lt_line_km=float(inputs.get('lt_line_km', 302626.0)),
            energy_sales_mu=float(inputs.get('energy_sales_mu', 25255.0)),
            norm_per_1000_consumers=float(inputs.get('norm_per_1000_consumers', 4.539)),
            norm_per_dtr=float(inputs.get('norm_per_dtr', 0.896)),
            norm_per_ht_km=float(inputs.get('norm_per_ht_km', 0.887)),
            norm_per_lt_km=float(inputs.get('norm_per_lt_km', 0.194)),
            norm_per_mu=float(inputs.get('norm_per_mu', 0.200)),
            gfa_sbu_d_opening=float(inputs.get('gfa_sbu_d_opening', 15961.16)),
            gfa_derecognized=float(inputs.get('gfa_derecognized', 805.39)),
            gfa_land=float(inputs.get('gfa_land', 22.52)),
            rm_rate=float(inputs.get('rm_rate', 0.04)),
            claimed_employee_ag=float(inputs.get('claimed_employee_ag', 3152.28)),
            claimed_rm=float(inputs.get('claimed_rm', 631.28)),
            claimed_total_om=float(inputs.get('claimed_total_om', 3783.56)),
            myt_approved_om=float(inputs.get('myt_approved_om', 3605.39)),
        )
        self.heuristic_result = result
        return result


class LineItem_IFC_D(LineItemBase):
    """
    Interest & Finance Charges Line Item — SBU-D version
    SBU-D ONLY — Has 7 sub-components (more than G/T):
      1. IFC-LTL-01: Interest on normative loans (shared, Ch 6)
      2. IFC-SD-01: Interest on security deposits (D-specific)
      3. IFC-GPF-01: Interest on GPF (shared, Ch 6)
      4. IFC-OTH-D-01: Other interest — PP arrears + bank charges (D-specific)
      5. MT-BOND-01: Master Trust bond interest (shared, Ch 6)
      6. IFC-CC-01: Carrying cost on revenue gap (D-specific)
      7. IFC-WC-01: Interest on working capital (negative in FY23-24)
    """

    def __init__(self):
        super().__init__("Interest & Finance Charges (Distribution)", pattern="multi")

    def run_all_heuristics(self, inputs: Dict) -> List[Dict]:
        results = []

        # 1. IFC-LTL-01: Interest on Long-Term Loans (shared)
        result_ltl = heuristic_IFC_LTL_01(
            inputs.get('opening_normative_loan', 0),
            inputs.get('gfa_additions', 0),
            inputs.get('depreciation', 0),
            inputs.get('opening_interest_rate', 0),
            inputs.get('claimed_interest', 483.76),
            inputs.get('disputed_claims', 0.0),
            inputs.get('highest_loan_rate', None)
        )
        results.append(result_ltl)

        # 2. IFC-SD-01: Interest on Security Deposits (D-specific)
        result_sd = heuristic_IFC_SD_01(
            actual_disbursement=float(inputs.get('sd_actual_disbursement', 146.88)),
            provision_in_accounts=float(inputs.get('sd_provision', 265.92)),
            sd_opening=float(inputs.get('sd_opening', 3235.94)),
            sd_closing=float(inputs.get('sd_closing', 3941.69)),
            interest_rate_prev=float(inputs.get('sd_rate_prev', 4.25)),
            interest_rate_current=float(inputs.get('sd_rate_current', 6.75)),
        )
        results.append(result_sd)

        # 3. IFC-GPF-01: Interest on GPF (shared)
        result_gpf = heuristic_IFC_GPF_01(
            inputs.get('opening_gpf_balance_company', 0),
            inputs.get('closing_gpf_balance_company', 0),
            inputs.get('gpf_interest_rate', 0),
            inputs.get('sbu_allocation_ratio', 1.0),
            inputs.get('claimed_gpf_interest_sbu', 164.88)
        )
        results.append(result_gpf)

        # 4. IFC-OTH-D-01: Other Interest (D-specific)
        result_oth = heuristic_IFC_OTH_D_01(
            interest_on_pp_arrears=float(inputs.get('interest_on_pp_arrears', 43.26)),
            bank_charges=float(inputs.get('bank_charges', 0.81)),
            kwa_fair_valuation=float(inputs.get('kwa_fair_valuation', 706.89)),
            claimed_other_interest=float(inputs.get('claimed_other_interest', 44.07)),
        )
        results.append(result_oth)

        # 5. MT-BOND-01: Master Trust bond interest (shared)
        result_bond = heuristic_MT_BOND_01(
            inputs.get('total_bond_interest', 477.03),
            inputs.get('sbu_allocation_ratio_mt', 1.0),
            inputs.get('claimed_bond_interest_sbu', 477.03)
        )
        results.append(result_bond)

        # 6. IFC-CC-01: Carrying Cost on Revenue Gap (D-specific)
        result_cc = heuristic_IFC_CC_01(
            unbridged_gap_opening=float(inputs.get('unbridged_gap_opening', 6408.37)),
            avg_gpf_balance=float(inputs.get('avg_gpf_balance', 2926.29)),
            excess_sd_over_wc=float(inputs.get('excess_sd_over_wc', 451.04)),
            avg_interest_rate=float(inputs.get('avg_interest_rate_loans', 8.52)),
            claimed_carrying_cost=float(inputs.get('claimed_carrying_cost', 321.24)),
        )
        results.append(result_cc)

        # 7. IFC-WC-01: Interest on Working Capital (shared — but negative for D)
        result_wc = heuristic_IFC_WC_01(
            inputs.get('approved_om_expenses', 3728.01),
            inputs.get('opening_gfa_excl_land', 15133.25),
            inputs.get('sbi_eblr_rate', 9.15),
            inputs.get('claimed_wc_interest', 0.0)
        )
        results.append(result_wc)

        self.heuristic_results = results
        return results


class LineItem_SBUTransfer(LineItemBase):
    """
    Upstream SBU Transfer Line Item (SBU-G → D or SBU-T → D)
    No heuristic — value is taken directly from upstream SBU's approved output.
    SBU-D ONLY
    """

    def __init__(self, source_sbu: str = "G"):
        name = f"Transfer from SBU-{source_sbu}"
        super().__init__(name, pattern="none")
        self.source_sbu = source_sbu

    def run_heuristic(self, inputs: Dict) -> Dict:
        """No heuristic — just pass through the approved amount."""
        approved = float(inputs.get('approved_amount', 0.0))
        claimed = float(inputs.get('claimed_amount', 0.0))

        self.heuristic_result = {
            'heuristic_id': f'SBU-{self.source_sbu}-TRANSFER',
            'flag': 'GREEN',
            'claimed_value': claimed,
            'recommended_amount': approved,
            'calculation_steps': [
                f"Transfer from SBU-{self.source_sbu}: ₹{approved:.2f} Cr",
                f"(Approved in SBU-{self.source_sbu} chapter — not re-evaluated in SBU-D)",
            ],
            'recommendation': f"Accept SBU-{self.source_sbu} approved amount of ₹{approved:.2f} Cr.",
        }
        return self.heuristic_result


class LineItem_TDLossSharing(LineItemBase):
    """
    T&D Loss Gain Sharing Line Item
    Heuristic: TD-SHARE-01 (single, primary)
    SBU-D ONLY

    Regulation 14(1) + 73(3):
      - If actual loss < target: savings shared 2:1 (licensee:consumer)
      - If actual loss > target: penalty (disallow PP cost for excess)
      - FY 2023-24: Loss INCREASED (9.76% vs 8.90% target) → no sharing
      - Commission waived penalty due to extraordinary demand surge
    """

    def __init__(self):
        super().__init__("T&D Loss Gain Sharing", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_TD_SHARE_01(
            td_loss_target_pct=float(inputs.get('td_loss_target_pct', 8.90)),
            td_loss_actual_pct=float(inputs.get('td_loss_actual_pct', 9.76)),
            prev_year_actual_pct=float(inputs.get('prev_year_actual_pct', 9.30)),
            annual_reduction_target=float(inputs.get('annual_reduction_target', 0.40)),
            avg_pp_cost_per_unit=float(inputs.get('avg_pp_cost_per_unit', 5.08)),
            total_energy_input_mu=float(inputs.get('total_energy_input_mu', 31124.10)),
            claimed_gain_sharing=float(inputs.get('claimed_gain_sharing', 131.59)),
            penalty_waived=inputs.get('penalty_waived', True),
        )
        self.heuristic_result = result
        return result


class LineItem_DistLoss(LineItemBase):
    """
    Distribution Loss Assessment Line Item
    Heuristic: DIST-LOSS-01 (single, informational)
    SBU-D ONLY — Does not directly affect ARR but informs TD-SHARE-01

    Reports actual distribution loss vs target.
    """

    def __init__(self):
        super().__init__("Distribution Loss", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_DIST_LOSS_01(
            energy_input_distribution_mu=float(inputs.get('energy_input_distribution_mu', 30587.11)),
            energy_output_mu=float(inputs.get('energy_output_mu', 28360.25)),
            dist_loss_target_pct=float(inputs.get('dist_loss_target_pct', 7.78)),
            claimed_dist_loss_pct=float(inputs.get('claimed_dist_loss_pct', 7.28)),
        )
        self.heuristic_result = result
        return result


class LineItem_PayRevision(LineItemBase):
    """
    Pay Revision Arrears Line Item
    Heuristic: EMP-PAYREV-01 (single, primary)
    SBU-D: ₹7.93 Cr claimed → Provisionally disallowed (no State Govt approval)
    """

    def __init__(self):
        super().__init__("Pay Revision Arrears", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_EMP_PAYREV_01(
            inputs.get('normative_employee_cost', 0.0),
            inputs.get('actual_employee_cost', 0.0),
            inputs.get('pay_revision', False),
            inputs.get('pay_revision_details', None)
        )
        self.heuristic_result = result
        return result


class LineItem_MTAdditional(LineItemBase):
    """
    Additional Contribution to Master Trust (standalone for SBU-D)
    Heuristic: MT-ADD-01 (single)
    In SBU-G/T this is part of LineItem_MasterTrust (multi).
    In SBU-D it's a separate ARR line item.
    """

    def __init__(self):
        super().__init__("Additional Contribution to Master Trust", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_MT_ADD_01(
            inputs.get('actuarial_liability_current_year', 0.0),
            inputs.get('provisional_cap', 0.0),
            inputs.get('sbu_allocation_ratio', 1.0),
            inputs.get('claimed_additional_contribution_sbu', 333.42),
            inputs.get('actuarial_report_submitted', True),
            inputs.get('govt_approval_obtained', True)
        )
        self.heuristic_result = result
        return result


class LineItem_MTBondRepayment(LineItemBase):
    """
    Repayment of Master Trust Bonds (standalone for SBU-D)
    Heuristic: MT-REPAY-01 (single)
    In SBU-G/T this is part of LineItem_MasterTrust (multi).
    In SBU-D it's a separate ARR line item.
    """

    def __init__(self):
        super().__init__("Repayment of Master Trust Bonds", pattern="single")

    def run_heuristic(self, inputs: Dict) -> Dict:
        result = heuristic_MT_REPAY_01(
            inputs.get('annual_principal_repayment', 339.40),
            inputs.get('sbu_allocation_ratio', 1.0),
            inputs.get('claimed_principal_repayment_sbu', 339.42)
        )
        self.heuristic_result = result
        return result


# =============================================================================
# REGISTRY: All LineItem classes by key
# =============================================================================

# Shared classes (can be instantiated for any SBU)
SHARED_LINE_ITEMS = {
    'roe': LineItem_ROE,
    'depreciation': LineItem_Depreciation,
    'ifc': LineItem_IFC,
    'master_trust': LineItem_MasterTrust,
    'other_expenses': LineItem_OtherExpenses,
    'exceptional_items': LineItem_ExceptionalItems,
    'nti': LineItem_NTI,
    'intangible_assets': LineItem_IntangibleAssets,
}

# SBU-G only
SBU_G_LINE_ITEMS = {
    'om_expenses': LineItem_OM_Expenses,
    'fuel_costs': LineItem_FuelCosts,
}

# SBU-T only
SBU_T_LINE_ITEMS = {
    'om_expenses': LineItem_TransOM,
    'edamon_kochi_comp': LineItem_TransComp,
    'pugalur_thrissur_comp': LineItem_TransComp,
    'trans_incentive': LineItem_TransIncentive,
}

# SBU-D only
SBU_D_LINE_ITEMS = {
    'sbu_g_transfer': lambda: LineItem_SBUTransfer(source_sbu='G'),
    'sbu_t_transfer': lambda: LineItem_SBUTransfer(source_sbu='T'),
    'power_purchase': LineItem_PowerPurchase,
    'om_expenses': LineItem_DistOM,
    'ifc': LineItem_IFC_D,                # D has its own IFC class (7 sub-components)
    'mt_additional': LineItem_MTAdditional,
    'bond_repayment': LineItem_MTBondRepayment,
    'td_loss_sharing': LineItem_TDLossSharing,
    'pay_revision': LineItem_PayRevision,
}


def create_line_items_for_sbu(sbu_code: str) -> Dict[str, LineItemBase]:
    """
    Factory function: create all LineItem instances for a given SBU.
    Uses sbu_config to determine which line items are needed.
    """
    from sbu_config import get_sbu_config

    config = get_sbu_config(sbu_code)
    items = {}

    # Select the SBU-specific registry
    sbu_specific = {
        'G': SBU_G_LINE_ITEMS,
        'T': SBU_T_LINE_ITEMS,
        'D': SBU_D_LINE_ITEMS,
    }.get(sbu_code, {})

    for item_config in config['line_items']:
        key = item_config['key']
        pattern = item_config.get('pattern', 'single')

        # Skip 'none' pattern items that don't have specific classes
        # (they're handled by SBU-specific items like SBUTransfer)

        # Check SBU-specific items first, then shared
        if key in sbu_specific:
            cls_or_factory = sbu_specific[key]
            # Support lambda factories (for items needing constructor args)
            if callable(cls_or_factory) and not isinstance(cls_or_factory, type):
                items[key] = cls_or_factory()  # Call lambda
            else:
                # Special handling for TransComp (needs line_name)
                if sbu_code == 'T' and cls_or_factory == LineItem_TransComp:
                    if key == 'edamon_kochi_comp':
                        items[key] = cls_or_factory(line_name="Edamon-Kochi 400kV")
                    elif key == 'pugalur_thrissur_comp':
                        items[key] = cls_or_factory(line_name="Pugalur-Thrissur 320kV HVDC")
                    else:
                        items[key] = cls_or_factory()
                else:
                    items[key] = cls_or_factory()
        elif key in SHARED_LINE_ITEMS:
            items[key] = SHARED_LINE_ITEMS[key]()
        elif pattern == 'none':
            # Items with no heuristic and no class (e.g., informational)
            pass
        else:
            print(f"Warning: No LineItem class found for key='{key}' in SBU-{sbu_code}")

    return items