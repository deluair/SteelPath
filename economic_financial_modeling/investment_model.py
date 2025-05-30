"""
Investment decision models for the SteelPath simulation.

This module helps agents decide on investments in new technologies, capacity expansions,
or retrofits based on economic viability, strategic goals, and policy constraints.
"""
import logging
from typing import Dict, Any, Optional, List

from ..data_management.schemas import SteelPlantSchema, ProductionTechnologyType
from .financial_model import FinancialCalculator
from .cost_model import CostCalculator
# from ..config.settings import InvestmentConfig # If there are global investment parameters

logger = logging.getLogger(__name__)

class InvestmentEvaluator:
    """
    Evaluates potential investments for steel plants or companies.
    """
    def __init__(self, financial_calc: FinancialCalculator, cost_calc: CostCalculator, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initializes the InvestmentEvaluator.

        Args:
            financial_calc (FinancialCalculator): For NPV, IRR calculations.
            cost_calc (CostCalculator): For estimating CAPEX, OPEX of potential investments.
            config (Optional[Dict[str, Any]]): Configuration for investment decisions,
                                                e.g., required ROI, max payback period.
        """
        self.financial_calc = financial_calc
        self.cost_calc = cost_calc
        self.config = config if config else {}
        self.min_required_npv = self.config.get("min_required_npv", 0)
        self.min_required_irr = self.config.get("min_required_irr", 0.12) # 12% default
        self.max_payback_period_years = self.config.get("max_payback_period_years", 10)
        logger.info("InvestmentEvaluator initialized.")

    def evaluate_new_technology_investment(
        self,
        current_plant_state: Optional[SteelPlantSchema], # None if greenfield
        proposed_technology: ProductionTechnologyType,
        proposed_capacity_tpa: float, # Tonnes Per Annum
        estimated_annual_revenue_usd: List[float], # Projected revenues over project lifetime
        estimated_annual_opex_usd: List[float],    # Projected OPEX (excl. depreciation) over project lifetime
        project_lifetime_years: int,
        discount_rate: Optional[float] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates an investment in a new production technology (greenfield or brownfield addition).

        Args:
            current_plant_state (Optional[SteelPlantSchema]): Current state if brownfield, else None.
            proposed_technology (ProductionTechnologyType): The technology to invest in.
            proposed_capacity_tpa (float): Capacity of the new unit.
            estimated_annual_revenue_usd (List[float]): Projected revenues for each year of project life.
            estimated_annual_opex_usd (List[float]): Projected operational costs for each year.
            project_lifetime_years (int): Expected operational lifetime of the investment.
            discount_rate (Optional[float]): Specific discount rate for this project.
            additional_params (Optional[Dict[str, Any]]): Location factors, specific capex adjustments etc.

        Returns:
            Dict[str, Any]: Evaluation results (e.g., NPV, IRR, payback, recommendation).
        """
        additional_params = additional_params or {}
        location_factor = additional_params.get("location_factor", 1.0)

        # 1. Calculate CAPEX
        initial_capex = self.cost_calc.calculate_capital_cost(
            technology_type=proposed_technology,
            capacity_tonnes_per_year=proposed_capacity_tpa,
            location_factor=location_factor
        )
        if initial_capex is None or initial_capex <= 0:
            logger.error("Could not calculate valid CAPEX for the proposed investment.")
            return {"decision": "Reject", "reason": "Invalid CAPEX calculation", "npv": None, "irr": None}

        # 2. Construct Cash Flows
        # Ensure revenue and opex lists match project lifetime, or handle appropriately
        if len(estimated_annual_revenue_usd) != project_lifetime_years or \
           len(estimated_annual_opex_usd) != project_lifetime_years:
            logger.error(f"Revenue/OPEX streams length must match project lifetime ({project_lifetime_years} years).")
            # Simplistic handling: truncate or pad with last value if lengths differ (not ideal)
            # A more robust solution would be required for real-world scenarios.
            return {"decision": "Reject", "reason": "Mismatch in cash flow stream lengths.", "npv": None, "irr": None}

        annual_net_cash_flows = [rev - opx for rev, opx in zip(estimated_annual_revenue_usd, estimated_annual_opex_usd)]
        project_cash_flows = [-initial_capex] + annual_net_cash_flows

        # 3. Financial Metrics
        npv = self.financial_calc.calculate_npv(project_cash_flows, discount_rate)
        irr = self.financial_calc.calculate_irr(project_cash_flows)
        payback_period = self.financial_calc.calculate_payback_period(initial_capex, annual_net_cash_flows)

        # 4. Decision Logic (Simplified)
        is_viable = True
        reasons = []

        if npv < self.min_required_npv:
            is_viable = False
            reasons.append(f"NPV ({npv:.2f}) below minimum required ({self.min_required_npv:.2f})")
        
        if irr is None or irr < self.min_required_irr:
            is_viable = False
            reasons.append(f"IRR ({irr if irr is not None else 'N/A':.2%}) below minimum required ({self.min_required_irr:.2%})")

        if payback_period is None or payback_period > self.max_payback_period_years:
            is_viable = False
            reasons.append(f"Payback period ({payback_period if payback_period is not None else 'N/A':.2f} yrs) exceeds max ({self.max_payback_period_years} yrs)")

        decision = "Accept" if is_viable else "Reject"
        
        logger.info(f"Investment evaluation for {proposed_technology.value} (Cap: {proposed_capacity_tpa} tpa):")
        logger.info(f"  CAPEX: ${initial_capex:.2f}")
        logger.info(f"  NPV: ${npv:.2f}, IRR: {irr if irr is not None else 'N/A':.2%}, Payback: {payback_period if payback_period is not None else 'N/A'} yrs")
        logger.info(f"  Decision: {decision}. Reasons: {'; '.join(reasons) if reasons else 'Met all criteria.'}")

        return {
            "decision": decision,
            "reason": '; '.join(reasons) if reasons else "Met all criteria.",
            "capex_usd": initial_capex,
            "npv_usd": npv,
            "irr_percent": irr * 100 if irr is not None else None, # Return as percentage
            "payback_years": payback_period,
            "cash_flows_usd": project_cash_flows
        }

    # Could add methods for evaluating retrofits, capacity expansions of existing tech, etc.

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Setup dependencies
    fin_calc = FinancialCalculator(default_discount_rate=0.10)
    cost_calc_params = {"capex_eaf_per_tonne": 450, "carbon_price_per_tonne_co2": 50}
    cost_calc = CostCalculator(economic_params=cost_calc_params)
    
    investment_config = {
        "min_required_npv": 100000, # Min $100k NPV
        "min_required_irr": 0.15,    # Min 15% IRR
        "max_payback_period_years": 8
    }
    evaluator = InvestmentEvaluator(financial_calc, cost_calc, config=investment_config)

    # Scenario 1: Profitable EAF investment
    print("\n--- Scenario 1: Profitable EAF ---")
    lifetime = 15
    # Simplified: Assume constant revenue and OPEX for demonstration
    # In reality, these would vary year by year based on market forecasts, efficiency degradation, etc.
    annual_revenue = [20000000] * lifetime # $20M/yr
    annual_opex = [12000000] * lifetime    # $12M/yr
    
    eaf_investment_results = evaluator.evaluate_new_technology_investment(
        current_plant_state=None, # Greenfield
        proposed_technology=ProductionTechnologyType.EAF,
        proposed_capacity_tpa=200000, # 200k tpa EAF
        estimated_annual_revenue_usd=annual_revenue,
        estimated_annual_opex_usd=annual_opex,
        project_lifetime_years=lifetime,
        discount_rate=0.10 # Project specific discount rate
    )
    print(f"EAF Investment Decision: {eaf_investment_results['decision']}")
    print(f"Reason: {eaf_investment_results['reason']}")
    print(f"NPV: ${eaf_investment_results['npv_usd']:.2f}, IRR: {eaf_investment_results['irr_percent']:.2f}%" if eaf_investment_results['irr_percent'] is not None else "IRR: N/A")

    # Scenario 2: Less profitable Hydrogen DRI (higher CAPEX)
    print("\n--- Scenario 2: Less Profitable H2-DRI ---")
    cost_calc_params_h2 = {"capex_h2_dri_per_tonne": 1600}
    cost_calc_h2 = CostCalculator(economic_params=cost_calc_params_h2)
    evaluator_h2 = InvestmentEvaluator(financial_calc, cost_calc_h2, config=investment_config)

    h2_annual_revenue = [25000000] * lifetime # Higher revenue due to green premium?
    h2_annual_opex = [15000000] * lifetime   # Higher OPEX due to hydrogen costs?

    h2_dri_investment_results = evaluator_h2.evaluate_new_technology_investment(
        current_plant_state=None, # Greenfield
        proposed_technology=ProductionTechnologyType.HYDROGEN_DRI,
        proposed_capacity_tpa=150000, # 150k tpa H2-DRI
        estimated_annual_revenue_usd=h2_annual_revenue,
        estimated_annual_opex_usd=h2_annual_opex,
        project_lifetime_years=lifetime,
        discount_rate=0.10
    )
    print(f"H2-DRI Investment Decision: {h2_dri_investment_results['decision']}")
    print(f"Reason: {h2_dri_investment_results['reason']}")
    print(f"NPV: ${h2_dri_investment_results['npv_usd']:.2f}, IRR: {h2_dri_investment_results['irr_percent']:.2f}%" if h2_dri_investment_results['irr_percent'] is not None else "IRR: N/A")
