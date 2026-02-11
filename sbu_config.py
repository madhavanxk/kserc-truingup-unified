"""
SBU Configuration Dictionary
==============================
Central configuration for all Strategic Business Units.

Each SBU entry defines:
  - line_items: Which line items belong to this SBU
  - parameters: SBU-specific default values
  - heuristic_map: Which heuristics apply and their metadata

Adding a new SBU (e.g., SBU-D) requires ONLY adding a new block here
plus the SBU-specific heuristic files. No changes to base classes needed.

Current SBUs:
  - G: Generation
  - T: Transmission
  - D: Distribution (placeholder for future)
"""

from typing import Dict, List, Any


# =============================================================================
# SBU-G: GENERATION
# =============================================================================

SBU_G_CONFIG = {
    'sbu_code': 'G',
    'sbu_name': 'Generation (SBU-G)',
    'sbu_full_name': 'Strategic Business Unit - Generation',

    # Equity base for ROE calculation
    'equity_base_cr': 831.27,
    'roe_rate': 0.14,

    # Line items in display order
    # Each entry: (key, display_name, heuristic_pattern, heuristic_ids)
    #   heuristic_pattern: 'single' = 1 heuristic, 'multi' = multiple heuristics
    'line_items': [
        {
            'key': 'fuel_costs',
            'name': 'Fuel Costs',
            'icon': 'âš¡',
            'pattern': 'single',
            'heuristic_ids': ['FUEL-01'],
            'is_expense': True,  # Added to Gross ARR
        },
        {
            'key': 'om_expenses',
            'name': 'O&M Expenses',
            'icon': 'ðŸ“„',
            'pattern': 'multi',
            'heuristic_ids': ['OM-INFL-01', 'OM-NORM-01', 'OM-APPORT-01', 'EMP-PAYREV-01'],
            'is_expense': True,
        },
        {
            'key': 'roe',
            'name': 'Return on Equity',
            'icon': 'ðŸ’°',
            'pattern': 'single',
            'heuristic_ids': ['ROE-01'],
            'is_expense': True,
        },
        {
            'key': 'depreciation',
            'name': 'Depreciation',
            'icon': 'ðŸ“‰',
            'pattern': 'single',
            'heuristic_ids': ['DEP-GEN-01'],
            'is_expense': True,
        },
        {
            'key': 'ifc',
            'name': 'Interest & Finance Charges',
            'icon': 'ðŸ¦',
            'pattern': 'multi',
            'heuristic_ids': ['IFC-LTL-01', 'IFC-WC-01', 'IFC-GPF-01', 'IFC-OTH-02'],
            'is_expense': True,
        },
        {
            'key': 'master_trust',
            'name': 'Master Trust Obligations',
            'icon': 'ðŸ›ï¸',
            'pattern': 'multi',
            'heuristic_ids': ['MT-BOND-01', 'MT-REPAY-01', 'MT-ADD-01'],
            'is_expense': True,
        },
        {
            'key': 'other_expenses',
            'name': 'Other Expenses',
            'icon': 'ðŸ“‹',
            'pattern': 'single',
            'heuristic_ids': ['OTHER-EXP-01'],
            'is_expense': True,
        },
        {
            'key': 'exceptional_items',
            'name': 'Exceptional Items',
            'icon': 'âš ï¸',
            'pattern': 'single',
            'heuristic_ids': ['EXC-01'],
            'is_expense': True,
        },
        {
            'key': 'intangible_assets',
            'name': 'Intangible Assets',
            'icon': 'ðŸ’¾',
            'pattern': 'single',
            'heuristic_ids': ['INTANG-01'],
            'is_expense': True,
        },
        {
            'key': 'nti',
            'name': 'Non-Tariff Income',
            'icon': 'ðŸ’µ',
            'pattern': 'single',
            'heuristic_ids': ['NTI-01'],
            'is_expense': False,  # Deducted from Gross ARR
        },
    ],

    # IFC-WC-01 specifics for SBU-G
    'ifc_wc': {
        'exclude_receivables': True,   # SBU-G excludes receivables
        'exclude_mt_from_om': True,    # SBU-G excludes MT from O&M for WC calc
    },

    # IFC-OTH specifics for SBU-G
    'ifc_oth': {
        'has_gbi': True,               # SBU-G has GBI (always disallowed)
    },

    # O&M method
    'om_method': 'station_wise_norms',  # Annexure-7: station-wise norms

    # FY 2023-24 validation data (from KSERC order)
    'fy_2023_24': {
        'gross_arr_approved': 529.47,   # Approximate
        'nti_approved': 40.21,
        'net_arr_approved': 489.26,     # Approximate
    },
}


# =============================================================================
# SBU-T: TRANSMISSION
# =============================================================================

SBU_T_CONFIG = {
    'sbu_code': 'T',
    'sbu_name': 'Transmission (SBU-T)',
    'sbu_full_name': 'Strategic Business Unit - Transmission',

    # Equity base for ROE calculation
    'equity_base_cr': 857.05,
    'roe_rate': 0.14,

    # Line items in display order
    'line_items': [
        {
            'key': 'om_expenses',
            'name': 'O&M Expenses',
            'icon': 'ðŸ“„',
            'pattern': 'single',  # SBU-T O&M is single heuristic (normative formula)
            'heuristic_ids': ['OM-TRANS-NORM-01'],
            'is_expense': True,
        },
        {
            'key': 'roe',
            'name': 'Return on Equity',
            'icon': 'ðŸ’°',
            'pattern': 'single',
            'heuristic_ids': ['ROE-01'],
            'is_expense': True,
        },
        {
            'key': 'depreciation',
            'name': 'Depreciation',
            'icon': 'ðŸ“‰',
            'pattern': 'single',
            'heuristic_ids': ['DEP-GEN-01'],
            'is_expense': True,
        },
        {
            'key': 'ifc',
            'name': 'Interest & Finance Charges',
            'icon': 'ðŸ¦',
            'pattern': 'multi',
            'heuristic_ids': ['IFC-LTL-01', 'IFC-WC-01', 'IFC-GPF-01', 'IFC-OTH-02'],
            'is_expense': True,
        },
        {
            'key': 'master_trust',
            'name': 'Master Trust Obligations',
            'icon': 'ðŸ›ï¸',
            'pattern': 'multi',
            'heuristic_ids': ['MT-BOND-01', 'MT-REPAY-01', 'MT-ADD-01'],
            'is_expense': True,
        },
        {
            'key': 'edamon_kochi_comp',
            'name': 'Edamon-Kochi Line Compensation',
            'icon': 'ðŸ”Œ',
            'pattern': 'single',
            'heuristic_ids': ['TRANS-COMP-01'],
            'is_expense': True,
        },
        {
            'key': 'pugalur_thrissur_comp',
            'name': 'Pugalur-Thrissur Line Compensation',
            'icon': 'ðŸ”Œ',
            'pattern': 'single',
            'heuristic_ids': ['TRANS-COMP-01'],
            'is_expense': True,
        },
        {
            'key': 'intangible_assets',
            'name': 'Intangible Assets (Software)',
            'icon': 'ðŸ’¾',
            'pattern': 'single',
            'heuristic_ids': ['INTANG-01'],
            'is_expense': True,
        },
        {
            'key': 'other_expenses',
            'name': 'Other Expenses',
            'icon': 'ðŸ“‹',
            'pattern': 'single',
            'heuristic_ids': ['OTHER-EXP-01'],
            'is_expense': True,
        },
        {
            'key': 'exceptional_items',
            'name': 'Exceptional Items',
            'icon': 'âš ï¸',
            'pattern': 'single',
            'heuristic_ids': ['EXC-01'],
            'is_expense': True,
        },
        {
            'key': 'trans_incentive',
            'name': 'Transmission Availability Incentive',
            'icon': 'ðŸŽ¯',
            'pattern': 'single',
            'heuristic_ids': ['TRANS-INCENT-01'],
            'is_expense': True,  # Added to ARR (though may be deferred)
        },
        {
            'key': 'nti',
            'name': 'Non-Tariff Income',
            'icon': 'ðŸ’µ',
            'pattern': 'single',
            'heuristic_ids': ['NTI-01'],
            'is_expense': False,
        },
    ],

    # T&D Loss heuristics (separate from ARR line items)
    'td_loss_heuristics': ['TRANS-LOSS-01', 'DIST-LOSS-01', 'TD-LOSS-COMBINED-01', 'TD-REWARD-01'],

    # IFC-WC-01 specifics for SBU-T
    'ifc_wc': {
        'exclude_receivables': False,   # SBU-T includes receivables
        'exclude_mt_from_om': False,    # SBU-T includes MT in O&M for WC calc
    },

    # IFC-OTH specifics for SBU-T
    'ifc_oth': {
        'has_gbi': False,               # SBU-T does not have GBI
    },

    # O&M method
    'om_method': 'bays_mva_cktkm',     # Regulation 58: Bays/MVA/CktKm formula

    # FY 2023-24 validation data (from KSERC order, Table 3.24)
    'fy_2023_24': {
        'gross_arr_approved': 1581.76,
        'nti_approved': 75.96,
        'net_arr_approved': 1505.80,
        'line_item_approved': {
            'ifc': 427.13,
            'roe': 119.99,
            'depreciation': 308.87,
            'om_expenses': 625.12,
            'mt_bond_repayment': 45.81,
            'mt_additional': 44.98,
            'edamon_kochi_comp': 7.95,
            'pugalur_thrissur_comp': 1.17,
            'intangible_assets': 0.00,
            'other_expenses': 0.56,
            'exceptional_items': 0.18,
            'trans_incentive': 0.00,  # Deferred
            'nti': 75.96,
        },
    },
}


# =============================================================================
# SBU-D: DISTRIBUTION (PLACEHOLDER)
# =============================================================================

SBU_D_CONFIG = {
    'sbu_code': 'D',
    'sbu_name': 'Distribution (SBU-D)',
    'sbu_full_name': 'Strategic Business Unit - Distribution',

    # Equity base for ROE calculation (Table 6.38 of KSERC Order)
    'equity_base_cr': 1810.73,
    'roe_rate': 0.14,

    # ------------------------------------------------------------------
    # Line items in ARR display order (Table 5.94)
    # SBU-D is the most complex: 15 line items including upstream transfers,
    # 13-source power purchase, 5-parameter O&M norms, D-specific IFC,
    # and T&D loss gain sharing.
    # ------------------------------------------------------------------
    'line_items': [
        {
            'key': 'sbu_g_transfer',
            'name': 'Cost of Generation (SBU-G)',
            'icon': '⚡',
            'pattern': 'none',
            'heuristic_ids': [],
            'is_expense': True,
            'note': 'Upstream transfer from SBU-G. Not re-evaluated in SBU-D.',
        },
        {
            'key': 'power_purchase',
            'name': 'Cost of Power Purchase (incl RLDC/ISTS)',
            'icon': '🔌',
            'pattern': 'single',
            'heuristic_ids': ['PP-COST-01'],
            'is_expense': True,
            'note': '13 source categories + ISTS charges. ~60% of ARR.',
        },
        {
            'key': 'sbu_t_transfer',
            'name': 'Cost of Intra-State Transmission (SBU-T)',
            'icon': '🔀',
            'pattern': 'none',
            'heuristic_ids': [],
            'is_expense': True,
            'note': 'Upstream transfer from SBU-T. Not re-evaluated in SBU-D.',
        },
        {
            'key': 'ifc',
            'name': 'Interest & Finance Charges',
            'icon': '🏦',
            'pattern': 'multi',
            'heuristic_ids': [
                'IFC-LTL-01',      # Interest on normative loans (Ch 6)
                'IFC-SD-01',       # Interest on security deposits (D-specific)
                'IFC-GPF-01',      # Interest on GPF (Ch 6)
                'IFC-OTH-D-01',   # Other interest (PP arrears, bank charges)
                'MT-BOND-01',      # Master Trust bond interest (Ch 6)
                'IFC-CC-01',       # Carrying cost on revenue gap (D-specific)
                'IFC-WC-01',       # Interest on working capital (negative in FY23-24)
            ],
            'is_expense': True,
        },
        {
            'key': 'mt_additional',
            'name': 'Additional Contribution to Master Trust',
            'icon': '🏛️',
            'pattern': 'single',
            'heuristic_ids': ['MT-ADD-01'],
            'is_expense': True,
        },
        {
            'key': 'depreciation',
            'name': 'Depreciation',
            'icon': '📉',
            'pattern': 'single',
            'heuristic_ids': ['DEP-GEN-01'],
            'is_expense': True,
        },
        {
            'key': 'om_expenses',
            'name': 'Normative O&M Expenses',
            'icon': '🔧',
            'pattern': 'single',
            'heuristic_ids': ['OM-DIST-NORM-01'],
            'is_expense': True,
            'note': '5-param formula (consumers/DTRs/HT/LT/energy) + R&M @ 4% GFA.',
        },
        {
            'key': 'pay_revision',
            'name': 'Pay Revision Arrears',
            'icon': '📋',
            'pattern': 'single',
            'heuristic_ids': ['EMP-PAYREV-01'],
            'is_expense': True,
            'note': 'Provisionally disallowed — no State Govt approval.',
        },
        {
            'key': 'roe',
            'name': 'Return on Equity (14%)',
            'icon': '💰',
            'pattern': 'single',
            'heuristic_ids': ['ROE-01'],
            'is_expense': True,
        },
        {
            'key': 'other_expenses',
            'name': 'Other Expenses',
            'icon': '📋',
            'pattern': 'single',
            'heuristic_ids': ['OTHER-EXP-01'],
            'is_expense': True,
        },
        {
            'key': 'exceptional_items',
            'name': 'Exceptional Items',
            'icon': '⚠️',
            'pattern': 'single',
            'heuristic_ids': ['EXC-01'],
            'is_expense': True,
        },
        {
            'key': 'td_loss_sharing',
            'name': 'Sharing of Gains due to T&D Loss Reduction',
            'icon': '📊',
            'pattern': 'single',
            'heuristic_ids': ['TD-SHARE-01'],
            'is_expense': True,
            'note': 'Reg 14/73: 2:1 sharing. Disallowed FY23-24 (loss increased).',
        },
        {
            'key': 'intangible_assets',
            'name': 'Amortisation of Intangible Assets (Software)',
            'icon': '💾',
            'pattern': 'single',
            'heuristic_ids': ['INTANG-01'],
            'is_expense': True,
        },
        {
            'key': 'bond_repayment',
            'name': 'Repayment of Master Trust Bonds',
            'icon': '🏛️',
            'pattern': 'single',
            'heuristic_ids': ['MT-REPAY-01'],
            'is_expense': True,
        },
        {
            'key': 'nti',
            'name': 'Non-Tariff Income',
            'icon': '💵',
            'pattern': 'single',
            'heuristic_ids': ['NTI-01'],
            'is_expense': False,
        },
    ],

    # T&D Loss / Distribution Loss heuristics
    'td_loss_heuristics': ['DIST-LOSS-01', 'TD-SHARE-01'],

    # O&M method
    'om_method': 'distribution_5param_norms',

    # IFC-WC specifics for SBU-D
    'ifc_wc': {
        'exclude_receivables': False,
        'exclude_mt_from_om': False,
        # WC was negative in FY 2023-24 (SD > WC requirement) → zero interest
    },

    # IFC-OTH specifics for SBU-D
    'ifc_oth': {
        'has_gbi': False,
        'has_pp_interest': True,        # Interest on PP arrears (CERC tariff diff)
    },

    # IFC-SD specifics for SBU-D
    'ifc_sd': {
        'basis': 'actual_disbursement',  # Reg 29(8): Only actual payment to consumers
    },

    # IFC-CC specifics for SBU-D (Carrying Cost)
    'ifc_cc': {
        'deduct_avg_gpf': True,
        'deduct_excess_sd_over_wc': True,
    },

    # Power Purchase configuration
    'pp_config': {
        'source_categories': 13,
        'ists_included': True,
        'banking_basis': 'cash_only',
        'exchange_tam_flag': True,
        'myt_avg_pp_rate': 4.70,
        'ists_loss_pct': 3.47,
    },

    # Distribution parameters for O&M norms (Table 5.75)
    'dist_params_fy2324': {
        'num_consumers': 13648851,
        'num_dtrs': 87911,
        'ht_line_km': 70269,
        'lt_line_km': 302626,
        'energy_sales_mu': 25255,
        'gfa_opening': 15961.16,
        'gfa_derecognized': 805.39,
        'gfa_land': 22.52,
    },

    # Inflation indices for norm escalation (Table 5.72)
    'inflation_indices': {
        'fy_2021_22': {'cpi': 356.06, 'wpi': 139.40},
        'fy_2022_23': {'cpi': 377.62, 'wpi': 152.50, 'weighted_70_30': 7.06},
        'fy_2023_24': {'cpi': 397.20, 'wpi': 151.40, 'weighted_70_30': 3.41},
    },

    # FY 2023-24 validation data (from KSERC Order, Table 5.94)
    'fy_2023_24': {
        'gross_arr_approved': 21413.35,
        'nti_approved': 920.18,
        'net_arr_approved': 20493.17,
        'revenue_from_sale': 19761.95,
        'revenue_gap': 731.22,
        'line_item_approved': {
            'sbu_g_transfer': 598.70,
            'power_purchase': 12773.50,
            'sbu_t_transfer': 1505.80,
            'ifc': 1536.14,
            'mt_additional': 333.42,
            'depreciation': 307.66,
            'om_expenses': 3728.01,
            'pay_revision': 0.00,
            'roe': 253.50,
            'other_expenses': 22.19,
            'exceptional_items': 15.00,
            'td_loss_sharing': 0.00,
            'intangible_assets': 0.00,
            'bond_repayment': 339.42,
            'nti': 920.18,
        },
        'line_item_claimed': {
            'sbu_g_transfer': 626.48,
            'power_purchase': 12982.59,
            'sbu_t_transfer': 1553.14,
            'ifc': 1637.86,
            'mt_additional': 333.42,
            'depreciation': 309.36,
            'om_expenses': 3783.56,
            'pay_revision': 7.93,
            'roe': 253.50,
            'other_expenses': 22.19,
            'exceptional_items': 15.00,
            'td_loss_sharing': 131.59,
            'intangible_assets': 9.64,
            'bond_repayment': 339.42,
            'nti': 920.18,
        },
        'ifc_approved_detail': {
            'interest_on_loans': 445.04,
            'interest_on_sd': 146.88,
            'interest_on_gpf': 164.88,
            'other_interest': 44.07,
            'mt_bond_interest': 477.03,
            'carrying_cost': 258.25,
            'interest_on_wc': 0.00,
        },
        'pp_approved_detail': {
            'cgs': 4731.09,
            'small_ipps_re': 230.51,
            'seci_wind': 61.75,
            'solar_outside': 47.33,
            'prosumer_captive': 25.00,
            'rgccpp_fixed': 70.65,
            'maithon_dvc': 1495.45,
            'dbfoo_approved': 872.15,
            'dbfoo_unapproved': 373.50,
            'medium_term': 364.19,
            'short_term': 718.44,
            'exchanges': 2123.16,
            'dsm': 206.67,
            'banking_swap': 5.09,
            'ists_charges': 1448.27,
            'surplus_sale_cost': 0.25,
        },
        'energy_balance': {
            'internal_gen_mu': 5657.40,
            'pp_at_kerala_periphery_mu': 25711.29,
            'swap_return_mu': 552.68,
            'sale_outside_mu': 71.27,
            'dsm_export_mu': 61.49,
            'net_for_state_mu': 30683.25,
            'energy_sold_mu': 27603.44,
            'avg_pp_cost_external': 5.08,
            'avg_pp_cost_pooled': 4.34,
            'appc_for_prosumer': 3.26,
        },
        'td_loss': {
            'myt_target_pct': 10.82,
            'ksebl_claimed_pct': 9.70,
            'kserc_assessed_pct': 9.76,
            'prev_year_actual_pct': 9.30,
            'annual_reduction_target': 0.40,
            'computed_target_pct': 8.90,
            'distribution_loss_pct': 7.28,
            'transmission_loss_pct': 2.61,
            'penalty_imposed': False,
            'gain_sharing_approved': 0.00,
        },
    },
}


# =============================================================================
# MASTER REGISTRY
# =============================================================================

SBU_CONFIGS = {
    'G': SBU_G_CONFIG,
    'T': SBU_T_CONFIG,
    'D': SBU_D_CONFIG,
}


def get_sbu_config(sbu_code: str) -> Dict:
    """Get configuration for a specific SBU."""
    config = SBU_CONFIGS.get(sbu_code.upper())
    if config is None:
        raise ValueError(f"Unknown SBU code: {sbu_code}. Available: {list(SBU_CONFIGS.keys())}")
    return config


def get_available_sbus() -> List[Dict]:
    """Get list of available SBUs with basic info."""
    return [
        {
            'code': config['sbu_code'],
            'name': config['sbu_name'],
            'line_item_count': len(config['line_items']),
            'ready': len(config['line_items']) > 0,
        }
        for config in SBU_CONFIGS.values()
    ]


def get_line_item_config(sbu_code: str, line_item_key: str) -> Dict:
    """Get configuration for a specific line item within an SBU."""
    config = get_sbu_config(sbu_code)
    for item in config['line_items']:
        if item['key'] == line_item_key:
            return item
    raise ValueError(f"Line item '{line_item_key}' not found in SBU-{sbu_code}")


def get_sbu_differences() -> Dict:
    """
    Document key differences between SBUs for reference.
    Useful for understanding why branching exists.
    """
    return {
        'om_method': {
            'G': 'Station-wise norms (Annexure-7, existing + new stations)',
            'T': 'Bays(40%):MVA(30%):CktKm(30%) formula (Regulation 58)',
            'D': '5-parameter norms (consumers/DTRs/HT/LT/energy) + 4% GFA R&M (Reg 80)',
        },
        'ifc_wc_receivables': {
            'G': 'Excluded from working capital',
            'T': 'Included in working capital',
            'D': 'Included in working capital (2 months revenue, less SD)',
        },
        'ifc_wc_mt_in_om': {
            'G': 'MT excluded from O&M for WC calculation',
            'T': 'MT included in O&M for WC calculation',
            'D': 'MT included in O&M for WC calculation',
        },
        'gbi': {
            'G': 'Has GBI (always disallowed - no scheme in force)',
            'T': 'No GBI',
            'D': 'No GBI',
        },
        'unique_line_items': {
            'G': ['Fuel Costs (FUEL-01)'],
            'T': ['Line Compensation (TRANS-COMP-01)', 'Availability Incentive (TRANS-INCENT-01)',
                   'T&D Losses (TRANS-LOSS-01, DIST-LOSS-01, TD-LOSS-COMBINED-01, TD-REWARD-01)'],
            'D': ['Power Purchase (PP-COST-01, 13 sources)', 'SBU-G/T Transfers (upstream)',
                   'Security Deposit Interest (IFC-SD-01)', 'Carrying Cost (IFC-CC-01)',
                   'T&D Gain Sharing (TD-SHARE-01)', 'Distribution Loss (DIST-LOSS-01)'],
        },
        'equity_base': {
            'G': 'Rs.831.27 Cr',
            'T': 'Rs.857.05 Cr',
            'D': 'Rs.1810.73 Cr',
        },
    }


if __name__ == "__main__":
    print("=" * 70)
    print("SBU CONFIGURATION REGISTRY")
    print("=" * 70)

    for sbu_info in get_available_sbus():
        status = "âœ… Ready" if sbu_info['ready'] else "â³ Placeholder"
        print(f"\n  SBU-{sbu_info['code']}: {sbu_info['name']}")
        print(f"    Line Items: {sbu_info['line_item_count']}")
        print(f"    Status: {status}")

    print("\n" + "-" * 70)
    print("KEY DIFFERENCES:")
    diffs = get_sbu_differences()
    for key, vals in diffs.items():
        print(f"\n  {key}:")
        for sbu, desc in vals.items():
            print(f"    SBU-{sbu}: {desc}")