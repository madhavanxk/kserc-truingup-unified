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
            'icon': '⚡',
            'pattern': 'single',
            'heuristic_ids': ['FUEL-01'],
            'is_expense': True,  # Added to Gross ARR
        },
        {
            'key': 'om_expenses',
            'name': 'O&M Expenses',
            'icon': '📄',
            'pattern': 'multi',
            'heuristic_ids': ['OM-INFL-01', 'OM-NORM-01', 'OM-APPORT-01', 'EMP-PAYREV-01'],
            'is_expense': True,
        },
        {
            'key': 'roe',
            'name': 'Return on Equity',
            'icon': '💰',
            'pattern': 'single',
            'heuristic_ids': ['ROE-01'],
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
            'key': 'ifc',
            'name': 'Interest & Finance Charges',
            'icon': '🏦',
            'pattern': 'multi',
            'heuristic_ids': ['IFC-LTL-01', 'IFC-WC-01', 'IFC-GPF-01', 'IFC-OTH-02'],
            'is_expense': True,
        },
        {
            'key': 'master_trust',
            'name': 'Master Trust Obligations',
            'icon': '🏛️',
            'pattern': 'multi',
            'heuristic_ids': ['MT-BOND-01', 'MT-REPAY-01', 'MT-ADD-01'],
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
            'key': 'intangible_assets',
            'name': 'Intangible Assets',
            'icon': '💾',
            'pattern': 'single',
            'heuristic_ids': ['INTANG-01'],
            'is_expense': True,
        },
        {
            'key': 'nti',
            'name': 'Non-Tariff Income',
            'icon': '💵',
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
            'icon': '📄',
            'pattern': 'single',  # SBU-T O&M is single heuristic (normative formula)
            'heuristic_ids': ['OM-TRANS-NORM-01'],
            'is_expense': True,
        },
        {
            'key': 'roe',
            'name': 'Return on Equity',
            'icon': '💰',
            'pattern': 'single',
            'heuristic_ids': ['ROE-01'],
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
            'key': 'ifc',
            'name': 'Interest & Finance Charges',
            'icon': '🏦',
            'pattern': 'multi',
            'heuristic_ids': ['IFC-LTL-01', 'IFC-WC-01', 'IFC-GPF-01', 'IFC-OTH-02'],
            'is_expense': True,
        },
        {
            'key': 'master_trust',
            'name': 'Master Trust Obligations',
            'icon': '🏛️',
            'pattern': 'multi',
            'heuristic_ids': ['MT-BOND-01', 'MT-REPAY-01', 'MT-ADD-01'],
            'is_expense': True,
        },
        {
            'key': 'edamon_kochi_comp',
            'name': 'Edamon-Kochi Line Compensation',
            'icon': '🔌',
            'pattern': 'single',
            'heuristic_ids': ['TRANS-COMP-01'],
            'is_expense': True,
        },
        {
            'key': 'pugalur_thrissur_comp',
            'name': 'Pugalur-Thrissur Line Compensation',
            'icon': '🔌',
            'pattern': 'single',
            'heuristic_ids': ['TRANS-COMP-01'],
            'is_expense': True,
        },
        {
            'key': 'intangible_assets',
            'name': 'Intangible Assets (Software)',
            'icon': '💾',
            'pattern': 'single',
            'heuristic_ids': ['INTANG-01'],
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
            'key': 'trans_incentive',
            'name': 'Transmission Availability Incentive',
            'icon': '🎯',
            'pattern': 'single',
            'heuristic_ids': ['TRANS-INCENT-01'],
            'is_expense': True,  # Added to ARR (though may be deferred)
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

    # Equity base (to be filled)
    'equity_base_cr': 0.0,  # TBD
    'roe_rate': 0.14,

    # Line items (placeholder - to be populated when SBU-D work begins)
    'line_items': [
        # Will include: Power Purchase Cost, O&M, ROE, Depreciation, IFC,
        # Master Trust, Cross-Subsidy, AT&C Losses, Consumer Tariff,
        # DSM, NTI, etc.
    ],

    'om_method': 'distribution_norms',  # TBD

    # IFC-WC specifics for SBU-D (to be confirmed)
    'ifc_wc': {
        'exclude_receivables': False,
        'exclude_mt_from_om': False,
    },

    'ifc_oth': {
        'has_gbi': False,
    },

    'fy_2023_24': {},  # To be populated
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
            'D': 'Distribution norms (TBD)',
        },
        'ifc_wc_receivables': {
            'G': 'Excluded from working capital',
            'T': 'Included in working capital',
            'D': 'TBD',
        },
        'ifc_wc_mt_in_om': {
            'G': 'MT excluded from O&M for WC calculation',
            'T': 'MT included in O&M for WC calculation',
            'D': 'TBD',
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
            'D': ['Power Purchase Cost', 'AT&C Losses', 'Cross-Subsidy', 'DSM (TBD)'],
        },
        'equity_base': {
            'G': 'Rs.831.27 Cr',
            'T': 'Rs.857.05 Cr',
            'D': 'TBD',
        },
    }


if __name__ == "__main__":
    print("=" * 70)
    print("SBU CONFIGURATION REGISTRY")
    print("=" * 70)

    for sbu_info in get_available_sbus():
        status = "✅ Ready" if sbu_info['ready'] else "⏳ Placeholder"
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