"""
Calculates environmental emissions for the SteelPath simulation.

Focuses on CO2 emissions from production activities, energy consumption,
and raw material processing (Scope 1, 2, and potentially Scope 3 upstream).
"""
import logging
from typing import Dict, Any, Optional

from ..production_technology.technology_models import BaseTechnologyModel, ProductionTechnologyType
from ..data_management.schemas import RawMaterialType

logger = logging.getLogger(__name__)

class EmissionFactors(BaseModel):
    """Holds emission factors for various sources."""
    # Scope 1: Direct emissions from owned or controlled sources
    # These are often included in BaseTechnologyModel.co2_emissions_tonne_per_tonne_steel

    # Scope 2: Indirect emissions from the generation of purchased energy
    electricity_gco2_per_kwh: float = Field(default=400, description="Grams of CO2e per kWh of grid electricity. Varies significantly by region.")
    # Convert to tonnes_co2_per_mwh: (g/kWh * 1000 kWh/MWh) / 1,000,000 g/tonne = g/kWh / 1000
    # So, 400 g/kWh = 0.4 tCO2/MWh

    # Scope 3: All other indirect emissions (e.g., upstream emissions from raw materials)
    # These are complex and require Life Cycle Assessment (LCA) data.
    # Example: tCO2e per tonne of raw material produced and transported
    raw_material_upstream_emissions_tco2_per_tonne: Dict[RawMaterialType, float] = Field(default_factory=dict,
        description="Upstream (Scope 3) emissions in tCO2e per tonne of raw material.")

    def get_electricity_emission_factor_tco2_per_mwh(self) -> float:
        return self.electricity_gco2_per_kwh / 1000.0

class EmissionCalculator:
    """
    Calculates CO2 and other relevant emissions based on simulation activities.
    """
    def __init__(self, emission_factors: Optional[EmissionFactors] = None):
        """
        Initializes the EmissionCalculator.

        Args:
            emission_factors (Optional[EmissionFactors]): Predefined emission factors.
                                                          If None, default factors will be used.
        """
        self.factors = emission_factors if emission_factors else EmissionFactors()
        # Example default upstream emissions (highly simplified, for illustration)
        if not self.factors.raw_material_upstream_emissions_tco2_per_tonne:
            self.factors.raw_material_upstream_emissions_tco2_per_tonne = {
                RawMaterialType.IRON_ORE: 0.1,  # tCO2e/tonne for mining, processing, transport
                RawMaterialType.COKING_COAL: 0.2,
                RawMaterialType.SCRAP_STEEL: 0.05, # Lower due to recycling benefits
                RawMaterialType.NATURAL_GAS: 0.25, # For production and transport, combustion elsewhere
                RawMaterialType.HYDROGEN: 10.0, # Grey H2 from SMR. Green H2 would be near 0.
            }
        logger.info("EmissionCalculator initialized.")

    def calculate_production_emissions(
        self, 
        technology_model: BaseTechnologyModel, 
        production_tonnes_steel: float,
        energy_consumed_mwh_by_source: Optional[Dict[str, float]] = None, # e.g., {"grid_electricity": 100, "natural_gas_combustion_mwh": 50}
        raw_materials_consumed_tonnes: Optional[Dict[RawMaterialType, float]] = None
    ) -> Dict[str, float]:
        """
        Calculates emissions from a specific production activity.

        Args:
            technology_model (BaseTechnologyModel): The technology model used for production.
            production_tonnes_steel (float): The amount of steel produced in tonnes.
            energy_consumed_mwh_by_source (Optional[Dict[str, float]]): 
                Energy consumed in MWh, broken down by source (e.g., grid electricity, on-site NG combustion).
                If None, uses technology_model.energy_consumption_mwh_per_tonne_steel for electricity.
            raw_materials_consumed_tonnes (Optional[Dict[RawMaterialType, float]]): 
                Actual raw materials consumed. If None, uses technology_model defaults per tonne of steel.

        Returns:
            Dict[str, float]: A dictionary of emissions by scope (e.g., scope1_tco2, scope2_tco2, scope3_tco2).
        """
        emissions_summary = {
            "scope1_direct_tco2": 0.0,
            "scope2_indirect_energy_tco2": 0.0,
            "scope3_upstream_materials_tco2": 0.0,
            "total_co2_equivalent_tco2": 0.0
        }

        # Scope 1: Direct process emissions
        # This is usually defined in the technology model itself (e.g., from carbon in coal, process reactions)
        emissions_summary["scope1_direct_tco2"] = technology_model.co2_emissions_tonne_per_tonne_steel * production_tonnes_steel

        # Scope 2: Indirect emissions from purchased electricity
        # If energy_consumed_mwh_by_source is provided, use that. Otherwise, estimate from tech model.
        grid_electricity_mwh = 0
        if energy_consumed_mwh_by_source and "grid_electricity" in energy_consumed_mwh_by_source:
            grid_electricity_mwh = energy_consumed_mwh_by_source["grid_electricity"]
        elif not energy_consumed_mwh_by_source: # If no breakdown, assume all tech model energy is grid electricity
            grid_electricity_mwh = technology_model.energy_consumption_mwh_per_tonne_steel * production_tonnes_steel
        
        emissions_summary["scope2_indirect_energy_tco2"] = grid_electricity_mwh * self.factors.get_electricity_emission_factor_tco2_per_mwh()
        # Note: If other energy sources (e.g., purchased steam) are used, their Scope 2 emissions should be added.
        # If energy is generated on-site (e.g., NG combustion), those are Scope 1 (covered by tech model or need separate calc).

        # Scope 3: Upstream emissions from raw materials
        actual_materials = raw_materials_consumed_tonnes
        if not actual_materials:
            # Estimate based on technology model defaults if not provided
            actual_materials = {mat: qty * production_tonnes_steel 
                                for mat, qty in technology_model.raw_material_input_per_tonne_steel.items()}
        
        scope3_mat_emissions = 0.0
        for material_type, quantity in actual_materials.items():
            factor = self.factors.raw_material_upstream_emissions_tco2_per_tonne.get(material_type, 0)
            scope3_mat_emissions += quantity * factor
        emissions_summary["scope3_upstream_materials_tco2"] = scope3_mat_emissions

        # Total emissions
        emissions_summary["total_co2_equivalent_tco2"] = (
            emissions_summary["scope1_direct_tco2"] + 
            emissions_summary["scope2_indirect_energy_tco2"] + 
            emissions_summary["scope3_upstream_materials_tco2"]
        )

        logger.debug(f"Emissions for {production_tonnes_steel}t steel via {technology_model.technology_type.value}: {emissions_summary}")
        return emissions_summary

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Get a technology model (assuming technology_models.py is in a sibling directory or installed package)
    # This relative import works if you run this script from the parent directory of environmental_impact and production_technology
    # For direct script execution within its own folder, Python might struggle with relative imports like this.
    # Consider adding the project root to PYTHONPATH or using a different execution method for testing.
    try:
        bf_bof_tech = BaseTechnologyModel.get_model_for_technology(ProductionTechnologyType.BF_BOF)
        eaf_tech = BaseTechnologyModel.get_model_for_technology(ProductionTechnologyType.EAF)
        h2_dri_tech = BaseTechnologyModel.get_model_for_technology(ProductionTechnologyType.HYDROGEN_DRI)
    except Exception as e:
        logger.error(f"Could not load technology models for example: {e}. Ensure paths are correct or run from project root.")
        # Dummy models for example to proceed if import fails
        class DummyTechModel(BaseModel):
            technology_type: ProductionTechnologyType
            co2_emissions_tonne_per_tonne_steel: float
            energy_consumption_mwh_per_tonne_steel: float
            raw_material_input_per_tonne_steel: Dict = {}
        bf_bof_tech = DummyTechModel(technology_type=ProductionTechnologyType.BF_BOF, co2_emissions_tonne_per_tonne_steel=1.8, energy_consumption_mwh_per_tonne_steel=5.0)
        eaf_tech = DummyTechModel(technology_type=ProductionTechnologyType.EAF, co2_emissions_tonne_per_tonne_steel=0.4, energy_consumption_mwh_per_tonne_steel=0.6)
        h2_dri_tech = DummyTechModel(technology_type=ProductionTechnologyType.HYDROGEN_DRI, co2_emissions_tonne_per_tonne_steel=0.1, energy_consumption_mwh_per_tonne_steel=3.0,
                                     raw_material_input_per_tonne_steel={RawMaterialType.HYDROGEN: 0.055})

    # Default emission factors
    calc = EmissionCalculator()
    
    print("--- BF-BOF Emissions (1000 tonnes steel) ---")
    bf_emissions = calc.calculate_production_emissions(bf_bof_tech, 1000)
    for k, v in bf_emissions.items(): print(f"  {k}: {v:.2f} tCO2e")

    # Custom factors (e.g., cleaner grid)
    custom_factors = EmissionFactors(electricity_gco2_per_kwh=100) # Cleaner grid
    custom_factors.raw_material_upstream_emissions_tco2_per_tonne[RawMaterialType.HYDROGEN] = 0.5 # Green H2
    calc_custom = EmissionCalculator(emission_factors=custom_factors)

    print("\n--- EAF Emissions (500 tonnes steel, custom factors) ---")
    eaf_emissions = calc_custom.calculate_production_emissions(eaf_tech, 500)
    for k, v in eaf_emissions.items(): print(f"  {k}: {v:.2f} tCO2e")

    print("\n--- H2-DRI Emissions (200 tonnes steel, custom factors for green H2) ---")
    # Specify actual raw materials if they differ from model defaults or for clarity
    h2_consumed_actual = {RawMaterialType.HYDROGEN: 200 * h2_dri_tech.raw_material_input_per_tonne_steel.get(RawMaterialType.HYDROGEN, 0.055)}
    h2_emissions = calc_custom.calculate_production_emissions(h2_dri_tech, 200, raw_materials_consumed_tonnes=h2_consumed_actual)
    for k, v in h2_emissions.items(): print(f"  {k}: {v:.2f} tCO2e")
