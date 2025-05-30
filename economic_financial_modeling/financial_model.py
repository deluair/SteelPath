"""
Financial models for agents in the SteelPath simulation.

This module includes functions for calculating Net Present Value (NPV),
Return on Investment (ROI), cash flow analysis, and other financial metrics.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy_financial as npf # Requires numpy to be installed

logger = logging.getLogger(__name__)

class FinancialCalculator:
    """
    Provides methods for common financial calculations relevant to simulation agents.
    """
    def __init__(self, default_discount_rate: float = 0.10):
        """
        Initializes the FinancialCalculator.

        Args:
            default_discount_rate (float): The default annual discount rate to use for NPV calculations
                                           if not otherwise specified.
        """
        self.default_discount_rate = default_discount_rate
        logger.info(f"FinancialCalculator initialized with default discount rate: {default_discount_rate:.2%}")

    def calculate_npv(self, cash_flows: List[float], discount_rate: Optional[float] = None) -> float:
        """
        Calculates the Net Present Value (NPV) of a series of cash flows.

        Args:
            cash_flows (List[float]): A list of cash flows. The first element is typically
                                      the initial investment (negative), followed by future
                                      cash flows (positive or negative).
            discount_rate (Optional[float]): The annual discount rate. If None, uses the
                                             calculator's default discount rate.

        Returns:
            float: The Net Present Value.
        """
        rate = discount_rate if discount_rate is not None else self.default_discount_rate
        if not cash_flows:
            return 0.0
        
        try:
            # npf.npv expects the rate first, then the list of cash flows.
            # The first cash flow cash_flows[0] is typically the initial investment at t=0.
            # npf.npv discounts all flows starting from the first one. If cash_flows[0] is at t=0, it should not be discounted by the formula `value / (1+rate)**(i+1)`.
            # npf.npv handles this correctly: cash_flows[0] + sum(cash_flows[i] / (1+rate)**i for i in 1 to N)
            # However, the common finance definition is -InitialInvestment + sum(CF_t / (1+r)^t)
            # If cash_flows[0] is initial investment (negative), npf.npv(rate, cash_flows) is correct.
            npv_value = npf.npv(rate, cash_flows)
            logger.debug(f"Calculated NPV with rate {rate:.2%} for cash flows {cash_flows}: {npv_value:.2f}")
            return float(npv_value) # Ensure it's a standard float
        except Exception as e:
            logger.error(f"Error calculating NPV: {e}. Cash flows: {cash_flows}, Rate: {rate}")
            return 0.0 # Or raise error

    def calculate_irr(self, cash_flows: List[float]) -> Optional[float]:
        """
        Calculates the Internal Rate of Return (IRR) for a series of cash flows.

        Args:
            cash_flows (List[float]): A list of cash flows, with the initial investment
                                      typically being the first (negative) value.

        Returns:
            Optional[float]: The IRR, or None if calculation fails (e.g., no sign change).
        """
        if not cash_flows or len(cash_flows) < 2:
            logger.warning("IRR calculation requires at least two cash flows.")
            return None
        try:
            irr_value = npf.irr(cash_flows)
            # npf.irr can return nan if no solution or multiple solutions.
            if irr_value is not None and not (isinstance(irr_value, float) and irr_value != irr_value): # Check for NaN
                logger.debug(f"Calculated IRR for cash flows {cash_flows}: {irr_value:.4%}")
                return float(irr_value)
            else:
                logger.warning(f"IRR calculation did not converge or resulted in NaN for cash flows: {cash_flows}")
                return None
        except Exception as e: # numpy_financial might raise errors for certain cash flow patterns
            logger.error(f"Error calculating IRR: {e}. Cash flows: {cash_flows}")
            return None

    def calculate_roi(self, net_profit: float, total_investment: float) -> Optional[float]:
        """
        Calculates the Return on Investment (ROI).

        Args:
            net_profit (float): The net profit from the investment (Gain - Cost).
            total_investment (float): The total cost of the investment.

        Returns:
            Optional[float]: The ROI as a decimal (e.g., 0.1 for 10%), or None if investment is zero.
        """
        if total_investment == 0:
            logger.warning("Cannot calculate ROI with zero total investment.")
            return None
        
        roi_value = net_profit / total_investment
        logger.debug(f"Calculated ROI with net profit {net_profit} and investment {total_investment}: {roi_value:.2%}")
        return roi_value

    def calculate_payback_period(self, initial_investment: float, annual_cash_flows: List[float]) -> Optional[float]:
        """
        Calculates the Payback Period for an investment.
        This version assumes uniform annual cash flows after the initial investment for simplicity,
        or uses cumulative cash flow for non-uniform flows.

        Args:
            initial_investment (float): The initial investment (a positive value).
            annual_cash_flows (List[float]): A list of subsequent annual cash inflows (positive values).

        Returns:
            Optional[float]: The payback period in years, or None if payback never occurs.
        """
        if initial_investment <= 0:
            logger.warning("Initial investment must be positive for payback period calculation.")
            return 0.0 # Or None, depending on interpretation
        
        cumulative_cash_flow = 0.0
        for i, cash_flow in enumerate(annual_cash_flows):
            cumulative_cash_flow += cash_flow
            if cumulative_cash_flow >= initial_investment:
                # Payback occurs in year i+1
                # If exact, it's i+1. If fractional:
                years = i
                remaining_investment = initial_investment - (cumulative_cash_flow - cash_flow)
                payback_in_year = remaining_investment / cash_flow if cash_flow > 0 else 0
                period = years + payback_in_year
                logger.debug(f"Payback period: {period:.2f} years.")
                return period
        
        logger.warning("Payback period not reached with the given cash flows.")
        return None

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    fin_calc = FinancialCalculator(default_discount_rate=0.08)

    # NPV Example
    # Initial investment: -100,000; Cash flows for 5 years: 30,000, 35,000, 40,000, 45,000, 50,000
    investment_flows = [-100000, 30000, 35000, 40000, 45000, 50000]
    npv = fin_calc.calculate_npv(investment_flows)
    print(f"NPV Example: NPV = ${npv:.2f}")

    npv_custom_rate = fin_calc.calculate_npv(investment_flows, discount_rate=0.12)
    print(f"NPV Example (12% rate): NPV = ${npv_custom_rate:.2f}")

    # IRR Example
    irr = fin_calc.calculate_irr(investment_flows)
    if irr is not None:
        print(f"IRR Example: IRR = {irr:.4%}")
    else:
        print("IRR Example: Could not calculate IRR.")

    # ROI Example
    # Investment = 100,000; Total Gain from Investment = 120,000 => Net Profit = 20,000
    roi = fin_calc.calculate_roi(net_profit=20000, total_investment=100000)
    if roi is not None:
        print(f"ROI Example: ROI = {roi:.2%}")

    # Payback Period Example
    initial_inv = 100000
    yearly_flows = [20000, 30000, 40000, 50000] # Cumulative: 20k, 50k, 90k, 140k
    payback = fin_calc.calculate_payback_period(initial_inv, yearly_flows)
    if payback is not None:
        print(f"Payback Period Example: {payback:.2f} years") # Expect 3 + (10000/50000) = 3.2 years

    no_payback_flows = [10000, 10000, 10000]
    no_payback = fin_calc.calculate_payback_period(initial_inv, no_payback_flows)
    if no_payback is None:
        print("Payback Example (No Payback): Payback period not reached.")
