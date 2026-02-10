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


# =============================================================================
# SHARED LINE ITEMS (used by SBU-G and SBU-T)
# =============================================================================

class LineItem_ROE(LineItemBase):
    """
    Return on Equity Line Item
    Heuristic: ROE-01 (single, primary)
    Used by: SBU-G (equity ₹831.27 Cr), SBU-T (equity ₹857.05 Cr)
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
    SBU-G ONLY — SBU-T uses LineItem_TransOM instead
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

        # Layer 2: OM-NORM-01 (depends on OM-INFL-01) — PRIMARY
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
    SBU-G ONLY — SBU-T has no fuel costs
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
    SBU-T ONLY — SBU-G uses LineItem_OM_Expenses instead
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
    SBU-T ONLY — Edamon-Kochi or Pugalur-Thrissur
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


def create_line_items_for_sbu(sbu_code: str) -> Dict[str, LineItemBase]:
    """
    Factory function: create all LineItem instances for a given SBU.
    Uses sbu_config to determine which line items are needed.
    """
    from sbu_config import get_sbu_config

    config = get_sbu_config(sbu_code)
    items = {}

    for item_config in config['line_items']:
        key = item_config['key']

        # Check SBU-specific items first, then shared
        if sbu_code == 'G' and key in SBU_G_LINE_ITEMS:
            items[key] = SBU_G_LINE_ITEMS[key]()
        elif sbu_code == 'T' and key in SBU_T_LINE_ITEMS:
            cls = SBU_T_LINE_ITEMS[key]
            # Special handling for TransComp (needs line_name)
            if cls == LineItem_TransComp:
                if key == 'edamon_kochi_comp':
                    items[key] = cls(line_name="Edamon-Kochi 400kV")
                elif key == 'pugalur_thrissur_comp':
                    items[key] = cls(line_name="Pugalur-Thrissur 320kV HVDC")
                else:
                    items[key] = cls()
            else:
                items[key] = cls()
        elif key in SHARED_LINE_ITEMS:
            items[key] = SHARED_LINE_ITEMS[key]()
        else:
            # Unknown line item - skip with warning
            print(f"Warning: No LineItem class found for key='{key}' in SBU-{sbu_code}")

    return items