"""
Cost models for the SteelPath simulation.

This module defines classes and functions to calculate various costs associated
with steel production, including operational, capital, and carbon costs.
"""
import logging
from typing import Dict, Any, Optional

from ..data_management.schemas import SteelPlantSchema, RawMaterialSchema, ProductionTechnologyType, RawMaterialType
# from ..config.settings import GlobalEconomicParameters # Assuming a config for global params

logger = logging.getLogger(__name__)

class CostCalculator:
    """
    A utility class to calculate different types of costs for a steel plant or process.
    """
    def __init__(self, economic_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the CostCalculator.

        Args:
            economic_params (Optional[Dict[str, Any]]): Dictionary containing global economic parameters
                                                       like discount rates, default prices if not available,
                                                       carbon cost per tonne, etc.
        """
        self.params = economic_params if economic_params else {}
        # Example: self.carbon_price_per_tonne_co2 = self.params.get("carbon_price_per_tonne_co2", 50) # USD
        logger.info("CostCalculator initialized.")

    def calculate_raw_material_cost(self, 
                                      materials_consumed: Dict[RawMaterialType, float], 
                                      material_prices: Dict[RawMaterialType, float]) -> float:
        """
        Calculates the total cost of raw materials consumed.

        Args:
            materials_consumed (Dict[RawMaterialType, float]): Tonnes of each raw material type consumed.
            material_prices (Dict[RawMaterialType, float]): Price per tonne for each raw material type.

        Returns:
            float: Total cost of raw materials.
        """
        total_cost = 0.0
        for material_type, quantity in materials_consumed.items():
            price = material_prices.get(material_type)
            if price is None:
                logger.warning(f"Price for material {material_type} not found. Skipping in cost calculation.")
                continue
            total_cost += quantity * price
        return total_cost

    def calculate_operational_cost(self, 
                                   plant: SteelPlantSchema, 
                                   production_volume_tonnes: float,
                                   raw_material_costs: float,
                                   # Add other factors like energy, labor, maintenance
                                   energy_consumed_mwh: float = 0,
                                   energy_price_usd_per_mwh: float = 0,
                                   labor_cost_usd: float = 0,
                                   maintenance_cost_usd: float = 0
                                   ) -> float:
        """
        Calculates the total operational cost (OPEX) for a given production volume.

        Args:
            plant (SteelPlantSchema): The steel plant data.
            production_volume_tonnes (float): The amount of steel produced in tonnes.
            raw_material_costs (float): Total cost of raw materials.
            energy_consumed_mwh (float): Energy consumed in MWh.
            energy_price_usd_per_mwh (float): Price of energy per MWh.
            labor_cost_usd (float): Total labor costs.
            maintenance_cost_usd (float): Total maintenance costs.

        Returns:
            float: Total operational cost.
        """
        # This is a simplified model. A more detailed model would consider technology-specific costs.
        total_opex = raw_material_costs
        total_opex += energy_consumed_mwh * energy_price_usd_per_mwh
        total_opex += labor_cost_usd
        total_opex += maintenance_cost_usd
        
        # Add a fixed operational cost component if applicable (e.g., from plant.fixed_opex_per_year)
        # fixed_opex_per_tonne = (plant.annual_fixed_opex or 0) / plant.production_capacity_tonnes_per_year if plant.production_capacity_tonnes_per_year else 0
        # total_opex += fixed_opex_per_tonne * production_volume_tonnes

        logger.debug(f"Calculated OPEX for plant {plant.plant_id} producing {production_volume_tonnes} tonnes: {total_opex}")
        return total_opex

    def calculate_capital_cost(self, 
                               technology_type: ProductionTechnologyType, 
                               capacity_tonnes_per_year: float,
                               location_factor: float = 1.0) -> float:
        """
        Calculates the estimated capital cost (CAPEX) for a new installation or major upgrade.

        Args:
            technology_type (ProductionTechnologyType): The type of production technology.
            capacity_tonnes_per_year (float): The new or added capacity in tonnes per year.
            location_factor (float): A factor to adjust for regional cost differences.

        Returns:
            float: Estimated total capital cost.
        """
        # Placeholder: CAPEX models are complex and depend heavily on technology and scale.
        # These would typically come from a database or detailed engineering models.
        base_capex_per_tonne = {
            ProductionTechnologyType.BF_BOF: self.params.get("capex_bof_per_tonne", 800), # USD/tonne capacity
            ProductionTechnologyType.EAF: self.params.get("capex_eaf_per_tonne", 500),
            ProductionTechnologyType.DRI_EAF: self.params.get("capex_dri_eaf_per_tonne", 1000),
            ProductionTechnologyType.HYDROGEN_DRI: self.params.get("capex_h2_dri_per_tonne", 1500),
            ProductionTechnologyType.ELECTROLYSIS: self.params.get("capex_electrolysis_per_tonne", 2000) # Highly variable
        }.get(technology_type, 1000) # Default if not found

        capex = base_capex_per_tonne * capacity_tonnes_per_year * location_factor
        logger.debug(f"Calculated CAPEX for {technology_type} with capacity {capacity_tonnes_per_year} t/yr: {capex}")
        return capex

    def calculate_carbon_emission_cost(self, 
                                       co2_emissions_tonnes: float, 
                                       carbon_price_usd_per_tonne_co2: Optional[float] = None) -> float:
        """
        Calculates the cost associated with CO2 emissions.

        Args:
            co2_emissions_tonnes (float): Total CO2 emissions in tonnes.
            carbon_price_usd_per_tonne_co2 (Optional[float]): The price of carbon per tonne of CO2.
                                                              If None, uses value from economic_params.

        Returns:
            float: Total cost of CO2 emissions.
        """
        price = carbon_price_usd_per_tonne_co2
        if price is None:
            price = self.params.get("carbon_price_per_tonne_co2", 0) # Default to 0 if not set globally or locally
        
        emission_cost = co2_emissions_tonnes * price
        logger.debug(f"Calculated carbon emission cost for {co2_emissions_tonnes} tonnes CO2 at ${price}/tonne: {emission_cost}")
        return emission_cost

# Example usage (conceptual)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Dummy plant data (replace with actual SteelPlantSchema instance)
    dummy_plant_data = {
        "plant_id": "P001", "name": "Test Plant", 
        "location": {"country": "Testland"},
        "production_capacity_tonnes_per_year": 1000000,
        "current_technology_mix": {ProductionTechnologyType.BF_BOF: 1.0}
    }
    plant_schema = SteelPlantSchema(**dummy_plant_data)

    # Dummy economic parameters
    econ_params = {
        "carbon_price_per_tonne_co2": 75, # USD
        "capex_bof_per_tonne": 850
    }
    cost_calc = CostCalculator(economic_params=econ_params)

    # Raw material cost example
    consumed = {RawMaterialType.IRON_ORE: 1500, RawMaterialType.COKING_COAL: 700}
    prices = {RawMaterialType.IRON_ORE: 120, RawMaterialType.COKING_COAL: 300}
    rm_cost = cost_calc.calculate_raw_material_cost(consumed, prices)
    print(f"Raw Material Cost: ${rm_cost}")

    # Operational cost example
    opex = cost_calc.calculate_operational_cost(
        plant=plant_schema, 
        production_volume_tonnes=10000, 
        raw_material_costs=rm_cost / (1000000/10000), # Scaled for example
        energy_consumed_mwh=5000, 
        energy_price_usd_per_mwh=60,
        labor_cost_usd=100000,
        maintenance_cost_usd=50000
    )
    print(f"Operational Cost: ${opex}")

    # Capital cost example
    capex = cost_calc.calculate_capital_cost(ProductionTechnologyType.EAF, 500000)
    print(f"Capital Cost for new EAF: ${capex}")

    # Carbon cost example
    carbon_cost = cost_calc.calculate_carbon_emission_cost(co2_emissions_tonnes=20000)
    print(f"Carbon Emission Cost: ${carbon_cost}")
    carbon_cost_local_price = cost_calc.calculate_carbon_emission_cost(co2_emissions_tonnes=20000, carbon_price_usd_per_tonne_co2=100)
    print(f"Carbon Emission Cost (local price): ${carbon_cost_local_price}")
