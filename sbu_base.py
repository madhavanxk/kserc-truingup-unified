"""
Base Classes for KSERC Truing-Up Decision Support System
=========================================================
Two base classes that eliminate boilerplate across all SBUs:

1. LineItemBase: Base for all LineItem classes (Tier 2)
   - Handles single-heuristic and multi-heuristic patterns
   - Provides get_approved_amount, get_overall_flag, check_review_status, get_summary
   - Subclasses only need to implement run_heuristic/run_all_heuristics

2. SBU_Base: Base for all SBU aggregation classes (Tier 3)
   - Handles ARR calculation, aggregation readiness, drill-down, export
   - Subclasses only need to define their line_items dict

Usage:
    class LineItem_ROE(LineItemBase):
        def __init__(self):
            super().__init__("Return on Equity", pattern="single")

        def run_heuristic(self, inputs):
            result = heuristic_ROE_01(**inputs)
            self.heuristic_result = result
            return result

    class SBU_Generation(SBU_Base):
        def __init__(self):
            super().__init__("G")
            self.line_items = {
                'roe': LineItem_ROE(),
                ...
            }
"""

from typing import Dict, List, Optional, Any
from sbu_config import get_sbu_config


# =============================================================================
# TIER 2: LINE ITEM BASE CLASS
# =============================================================================

class LineItemBase:
    """
    Base class for all LineItem classes.

    Handles two patterns:
      - 'single': One heuristic → stored in self.heuristic_result (dict)
      - 'multi': Multiple heuristics → stored in self.heuristic_results (list of dicts)

    Subclasses MUST implement:
      - For 'single' pattern: run_heuristic(inputs) → sets self.heuristic_result
      - For 'multi' pattern: run_all_heuristics(inputs) → sets self.heuristic_results

    All other methods (get_approved_amount, get_overall_flag, check_review_status,
    get_summary) are provided by this base class and should NOT be overridden.
    """

    def __init__(self, line_item_name: str, pattern: str = "single"):
        """
        Args:
            line_item_name: Display name of the line item
            pattern: 'single' for 1 heuristic, 'multi' for multiple
        """
        self.line_item_name = line_item_name
        self.pattern = pattern

        # Storage for heuristic results
        if pattern == "single":
            self.heuristic_result: Optional[Dict] = None
        else:
            self.heuristic_results: List[Dict] = []

        self.final_approved_amount: Optional[float] = None
        self.all_reviews_complete: bool = False

    # -------------------------------------------------------------------------
    # INTERNAL: Get all results as a list (unified access regardless of pattern)
    # -------------------------------------------------------------------------

    def _get_all_results(self) -> List[Dict]:
        """Get all heuristic results as a list, regardless of pattern."""
        if self.pattern == "single":
            return [self.heuristic_result] if self.heuristic_result else []
        else:
            return self.heuristic_results if self.heuristic_results else []

    # -------------------------------------------------------------------------
    # PUBLIC: These 4 methods replace the boilerplate in all 10+ LineItem classes
    # -------------------------------------------------------------------------

    def get_primary_heuristic(self) -> Optional[Dict]:
        """Get the primary heuristic (the one that determines the approved amount)."""
        for result in self._get_all_results():
            if result.get('is_primary'):
                return result
        # If no primary marked, return the first result (for single-heuristic items)
        results = self._get_all_results()
        return results[0] if results else None

    def get_approved_amount(self) -> Optional[float]:
        """
        Get final approved amount for this line item.
        Staff override takes precedence over recommended amount.

        For multi-heuristic items, sums all primary heuristic amounts.
        """
        results = self._get_all_results()
        if not results:
            return None

        if self.pattern == "single":
            primary = self.get_primary_heuristic()
            if not primary:
                return None
            if primary.get('staff_approved_amount') is not None:
                self.final_approved_amount = primary['staff_approved_amount']
            else:
                self.final_approved_amount = primary.get('recommended_amount')
            return self.final_approved_amount

        else:
            # Multi-heuristic: sum all primary heuristic amounts
            total = 0.0
            has_any = False
            for result in results:
                if result.get('is_primary') and result.get('output_type') == 'approved_amount':
                    if result.get('staff_approved_amount') is not None:
                        total += result['staff_approved_amount']
                        has_any = True
                    elif result.get('recommended_amount') is not None:
                        total += result['recommended_amount']
                        has_any = True

            if has_any:
                self.final_approved_amount = total
                return self.final_approved_amount

            # Fallback: if no primary with approved_amount, try first primary
            primary = self.get_primary_heuristic()
            if primary:
                if primary.get('staff_approved_amount') is not None:
                    self.final_approved_amount = primary['staff_approved_amount']
                else:
                    self.final_approved_amount = primary.get('recommended_amount')
                return self.final_approved_amount

            return None

    def get_overall_flag(self) -> str:
        """
        Get overall flag for the line item.
        Uses strictest flag: RED > YELLOW > GREEN.
        Considers staff overrides.
        """
        results = self._get_all_results()
        if not results:
            return 'PENDING'

        flags = []
        for result in results:
            flag = result.get('staff_override_flag') or result.get('flag')
            if flag:
                flags.append(flag)

        if not flags:
            return 'PENDING'

        if 'RED' in flags:
            return 'RED'
        elif 'YELLOW' in flags:
            return 'YELLOW'
        else:
            return 'GREEN'

    def check_review_status(self) -> Dict:
        """
        Check review status of all heuristics.
        Returns counts and completion status.
        """
        results = self._get_all_results()
        if not results:
            return {
                'total': 0,
                'pending': 0,
                'accepted': 0,
                'overridden': 0,
                'complete': False
            }

        pending = sum(1 for r in results if r.get('staff_review_status') == 'Pending')
        accepted = sum(1 for r in results if r.get('staff_review_status') == 'Accepted')
        overridden = sum(1 for r in results if r.get('staff_review_status') == 'Overridden')

        total = len(results)
        complete = (pending == 0 and total > 0)

        self.all_reviews_complete = complete

        return {
            'total': total,
            'pending': pending,
            'accepted': accepted,
            'overridden': overridden,
            'complete': complete
        }

    def get_summary(self) -> Dict:
        """
        Get complete summary of the line item.
        Used for aggregation at SBU level.
        """
        return {
            'line_item_name': self.line_item_name,
            'heuristic_count': len(self._get_all_results()),
            'heuristic_results': self._get_all_results(),
            'approved_amount': self.get_approved_amount(),
            'overall_flag': self.get_overall_flag(),
            'review_status': self.check_review_status(),
            'primary_heuristic': self.get_primary_heuristic()
        }


# =============================================================================
# TIER 3: SBU BASE CLASS
# =============================================================================

class SBU_Base:
    """
    Base class for all SBU aggregation classes.

    Provides:
      - calculate_total_arr()
      - check_aggregation_ready()
      - get_sbu_summary()
      - get_drill_down_data()
      - get_pending_reviews()
      - get_summary_by_flag()
      - export_to_dict()

    Subclasses MUST:
      - Call super().__init__(sbu_code) in their __init__
      - Set self.line_items dict mapping keys to LineItemBase instances

    The SBU config is automatically loaded from sbu_config.py.
    """

    def __init__(self, sbu_code: str):
        """
        Args:
            sbu_code: 'G', 'T', or 'D'
        """
        self.sbu_code = sbu_code.upper()
        self.config = get_sbu_config(self.sbu_code)
        self.sbu_name = self.config['sbu_name']

        # Subclass must populate this
        self.line_items: Dict[str, LineItemBase] = {}

        self.total_arr: float = 0.0
        self.aggregation_complete: bool = False

    def get_line_item(self, line_item_key: str) -> Optional[LineItemBase]:
        """Get a specific line item object."""
        return self.line_items.get(line_item_key)

    def calculate_total_arr(self) -> float:
        """
        Calculate total Annual Revenue Requirement.
        Sums expense items, subtracts non-expense items (like NTI).
        Uses is_expense flag from config to determine sign.
        """
        total = 0.0

        # Build lookup for is_expense flag
        expense_lookup = {}
        for item_config in self.config['line_items']:
            expense_lookup[item_config['key']] = item_config.get('is_expense', True)

        for key, line_item in self.line_items.items():
            approved = line_item.get_approved_amount()
            if approved is not None:
                is_expense = expense_lookup.get(key, True)
                if is_expense:
                    total += approved
                else:
                    total -= approved  # NTI and similar deductions

        self.total_arr = round(total, 2)
        return self.total_arr

    def check_aggregation_ready(self) -> Dict:
        """
        Check if all line items are ready for aggregation
        (all heuristics reviewed by staff).
        """
        statuses = {}
        all_complete = True

        for key, line_item in self.line_items.items():
            review_status = line_item.check_review_status()
            statuses[key] = review_status
            if not review_status['complete']:
                all_complete = False

        self.aggregation_complete = all_complete

        return {
            'ready_for_aggregation': all_complete,
            'line_item_statuses': statuses
        }

    def get_sbu_summary(self) -> Dict:
        """Get complete SBU summary with all line items."""
        line_summaries = {}
        for key, line_item in self.line_items.items():
            line_summaries[key] = line_item.get_summary()

        aggregation_status = self.check_aggregation_ready()
        total_arr = self.calculate_total_arr()

        return {
            'sbu_code': self.sbu_code,
            'sbu_name': self.sbu_name,
            'line_items': line_summaries,
            'total_arr': total_arr,
            'aggregation_status': aggregation_status,
            'aggregation_complete': self.aggregation_complete
        }

    def get_drill_down_data(self) -> Dict:
        """Get detailed drill-down data for dashboard display."""
        drill_down = {
            'sbu_name': self.sbu_name,
            'total_arr': self.total_arr,
            'line_items_detail': []
        }

        for key, line_item in self.line_items.items():
            summary = line_item.get_summary()

            line_detail = {
                'key': key,
                'name': summary['line_item_name'],
                'approved_amount': summary['approved_amount'],
                'overall_flag': summary['overall_flag'],
                'review_status': summary['review_status'],
                'heuristics': []
            }

            for heuristic in summary['heuristic_results']:
                heur_detail = {
                    'id': heuristic['heuristic_id'],
                    'name': heuristic['heuristic_name'],
                    'flag': heuristic.get('staff_override_flag') or heuristic['flag'],
                    'is_primary': heuristic['is_primary'],
                    'review_status': heuristic['staff_review_status'],
                    'reviewed_by': heuristic.get('reviewed_by'),
                    'reviewed_at': heuristic.get('reviewed_at'),
                    'approved_amount': (heuristic.get('staff_approved_amount')
                                        or heuristic.get('recommended_amount'))
                }
                line_detail['heuristics'].append(heur_detail)

            drill_down['line_items_detail'].append(line_detail)

        return drill_down

    def get_pending_reviews(self) -> List[Dict]:
        """Get list of all pending reviews across all line items."""
        pending = []

        for key, line_item in self.line_items.items():
            summary = line_item.get_summary()

            for heuristic in summary['heuristic_results']:
                if heuristic.get('staff_review_status') == 'Pending':
                    pending.append({
                        'line_item': summary['line_item_name'],
                        'heuristic_id': heuristic['heuristic_id'],
                        'heuristic_name': heuristic['heuristic_name'],
                        'flag': heuristic['flag'],
                        'is_primary': heuristic['is_primary']
                    })

        return pending

    def get_summary_by_flag(self) -> Dict:
        """Get summary of heuristics grouped by flag color."""
        summary = {
            'GREEN': [],
            'YELLOW': [],
            'RED': []
        }

        for key, line_item in self.line_items.items():
            line_summary = line_item.get_summary()

            for heuristic in line_summary['heuristic_results']:
                flag = heuristic.get('staff_override_flag') or heuristic['flag']
                if flag in summary:
                    summary[flag].append({
                        'line_item': line_summary['line_item_name'],
                        'heuristic_id': heuristic['heuristic_id'],
                        'heuristic_name': heuristic['heuristic_name'],
                        'is_primary': heuristic['is_primary']
                    })

        return {
            'total_green': len(summary['GREEN']),
            'total_yellow': len(summary['YELLOW']),
            'total_red': len(summary['RED']),
            'details': summary
        }

    def export_to_dict(self) -> Dict:
        """Export complete SBU data to dictionary (for JSON/Excel)."""
        return {
            'sbu_code': self.sbu_code,
            'sbu_name': self.sbu_name,
            'total_arr': self.total_arr,
            'aggregation_complete': self.aggregation_complete,
            'config': {
                'equity_base_cr': self.config.get('equity_base_cr'),
                'roe_rate': self.config.get('roe_rate'),
                'om_method': self.config.get('om_method'),
            },
            'line_items': {
                key: line_item.get_summary()
                for key, line_item in self.line_items.items()
            }
        }


# =============================================================================
# TIER 3: CONCRETE SBU CLASSES
# =============================================================================

class SBU_Generation(SBU_Base):
    """
    Strategic Business Unit - Generation (SBU-G)

    10 line items, 19 heuristics.
    Unique: Fuel Costs, Station-wise O&M norms.
    """

    def __init__(self):
        super().__init__('G')
        from line_items import create_line_items_for_sbu
        self.line_items = create_line_items_for_sbu('G')


class SBU_Transmission(SBU_Base):
    """
    Strategic Business Unit - Transmission (SBU-T)

    12 line items, 7 T-specific + shared heuristics.
    Unique: Bays/MVA/CktKm O&M, Line Compensation, Availability Incentive.
    Also manages T&D Loss heuristics (separate from ARR).
    """

    def __init__(self):
        super().__init__('T')
        from line_items import create_line_items_for_sbu
        self.line_items = create_line_items_for_sbu('T')

        # T&D Loss results (separate from ARR line items)
        self.td_loss_results = []

    def run_td_loss_heuristics(self, trans_loss_params=None, td_reward_params=None):
        """Run T&D loss heuristics (not part of ARR, but reported alongside)."""
        from heuristics.td_loss_heuristics import (
            heuristic_TRANS_LOSS_01,
            heuristic_TD_REWARD_01,
            FY_2023_24_TRANS_LOSS_DEFAULTS,
            FY_2023_24_TD_REWARD_DEFAULTS,
        )

        self.td_loss_results = []

        tp = trans_loss_params or FY_2023_24_TRANS_LOSS_DEFAULTS
        self.td_loss_results.append(heuristic_TRANS_LOSS_01(**tp))

        rp = td_reward_params or FY_2023_24_TD_REWARD_DEFAULTS
        self.td_loss_results.append(heuristic_TD_REWARD_01(**rp))

        return self.td_loss_results

    def get_sbu_summary(self):
        """Override to include T&D loss data."""
        summary = super().get_sbu_summary()
        summary['td_loss_results'] = self.td_loss_results
        summary['td_loss_count'] = len(self.td_loss_results)
        return summary
class SBU_Distribution(SBU_Base):
    """
    Strategic Business Unit - Distribution (SBU-D)
    
    21 line items, 30+ heuristics (most complex SBU).
    Unique: 5-parameter O&M formula, Power Purchase breakdown (16 sources),
    Security Deposit interest, Carrying Cost, T&D Loss tracking.
    """
    
    def __init__(self):
        super().__init__('D')
        from line_items import create_line_items_for_sbu
        self.line_items = create_line_items_for_sbu('D')
        
        # Distribution-specific metrics (separate from ARR)
        self.dist_loss_result = None
        self.td_gain_sharing_result = None
    
    def run_distribution_loss_heuristic(self, dist_loss_params):
        """Run distribution loss calculation (monitoring, not ARR item)."""
        from heuristics.distribution_heuristics import heuristic_DIST_LOSS_01
        
        self.dist_loss_result = heuristic_DIST_LOSS_01(**dist_loss_params)
        return self.dist_loss_result
    
    def run_td_gain_sharing_heuristic(self, td_params):
        """Run T&D loss gain/penalty sharing (ARR impact)."""
        from heuristics.distribution_heuristics import heuristic_TD_SHARE_01
        
        self.td_gain_sharing_result = heuristic_TD_SHARE_01(**td_params)
        return self.td_gain_sharing_result
    
    def get_sbu_summary(self):
        """Override to include distribution-specific metrics."""
        summary = super().get_sbu_summary()
        summary['dist_loss_result'] = self.dist_loss_result
        summary['td_gain_sharing_result'] = self.td_gain_sharing_result
        return summary

# Factory function
def create_sbu(sbu_code: str) -> SBU_Base:
    """
    Factory: Create an SBU instance by code.

    Args:
        sbu_code: 'G', 'T', or 'D'

    Returns:
        SBU_Generation, SBU_Transmission, or SBU_Distribution instance
    """
    sbu_map = {
        'G': SBU_Generation,
        'T': SBU_Transmission,
        # 'D': SBU_Distribution,  # Future
    }

    cls = sbu_map.get(sbu_code.upper())
    if cls is None:
        raise ValueError(f"Unknown SBU code: {sbu_code}. Available: {list(sbu_map.keys())}")
    return cls()

def create_sbu(sbu_code: str) -> SBU_Base:
    """
    Factory: Create an SBU instance by code.
    
    Args:
        sbu_code: 'G', 'T', or 'D'
    
    Returns:
        SBU_Generation, SBU_Transmission, or SBU_Distribution instance
    """
    sbu_map = {
        'G': SBU_Generation,
        'T': SBU_Transmission,
        'D': SBU_Distribution,  
    }
    
    cls = sbu_map.get(sbu_code.upper())
    if cls is None:
        raise ValueError(f"Unknown SBU code: {sbu_code}. Available: {list(sbu_map.keys())}")
    return cls()