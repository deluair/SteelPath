"""
Defines models for various steel production technologies in the SteelPath simulation.

Each technology model includes parameters for raw material consumption, energy use,
emissions, and other operational characteristics.
"""
import logging
from typing import Dict, Any, Optional, ClassVar
from pydantic import BaseModel, Field

from ..data_management.schemas import RawMaterialType, ProductionTechnologyType

logger = logging.getLogger(__name__)

class BaseTechnologyModel(BaseModel):
    """Base class for all production technology models."""
    technology_type: ProductionTechnologyType
    # Input requirements per tonne of crude steel produced
    raw_material_input_per_tonne_steel: Dict[RawMaterialType, float] = Field(default_factory=dict,
        description="Tonnes of each raw material required per tonne of crude steel.")
    energy_consumption_mwh_per_tonne_steel: float = Field(..., gt=0,
        description="Energy consumption in MWh per tonne of crude steel.")
    # Output characteristics
    co2_emissions_tonne_per_tonne_steel: float = Field(..., ge=0,
        description="Direct CO2 emissions in tonnes per tonne of crude steel (Scope 1). Does not include upstream emissions.")
    # Other operational parameters
    typical_efficiency: float = Field(default=0.9, ge=0.5, le=1.0, 
        description="Typical operational efficiency of this technology (0.5 to 1.0).")
    min_operational_capacity_tpa: float = Field(default=100000, gt=0,
        description="Minimum economic operational capacity in tonnes per annum.")
    max_operational_capacity_tpa: float = Field(default=10000000, gt=0,
        description="Maximum typical single unit capacity in tonnes per annum.")
    # Cost parameters (can be indicative, detailed costs handled by CostModel)
    indicative_opex_usd_per_tonne: Optional[float] = Field(default=None,
        description="Indicative operational cost excluding raw materials and energy, USD per tonne steel.")
    indicative_capex_usd_per_tpa: Optional[float] = Field(default=None,
        description="Indicative capital cost, USD per tonne of annual capacity.")

    # Class variable to store default parameters for each technology type
    _defaults_registry: ClassVar[Dict[ProductionTechnologyType, Dict[str, Any]]] = {}

    def __init__(self, **data: Any):
        # Load defaults if available for the specific technology type
        tech_type = data.get('technology_type')
        if tech_type and tech_type in self._defaults_registry:
            defaults = self._defaults_registry[tech_type].copy()
            # Override defaults with provided data
            for key, value in data.items():
                defaults[key] = value # This ensures data passed to constructor takes precedence
            super().__init__(**defaults)
        else:
            super().__init__(**data)

    @classmethod
    def register_defaults(cls, tech_type: ProductionTechnologyType, defaults: Dict[str, Any]):
        """Registers default parameters for a given technology type."""
        cls._defaults_registry[tech_type] = defaults

    @classmethod
    def get_model_for_technology(cls, tech_type: ProductionTechnologyType, **overrides: Any) -> 'BaseTechnologyModel':
        """Factory method to get a configured model for a specific technology."""
        if tech_type not in cls._defaults_registry:
            logger.warning(f"No default parameters registered for technology {tech_type}. Using base and overrides.")
            # Fallback to creating an instance with base class defaults + overrides
            # This requires technology_type to be in overrides or an error will occur if it's a required field.
            # Or, we can make technology_type an explicit argument here.
            return cls(technology_type=tech_type, **overrides)
        
        # Create a new instance using the registered defaults and any overrides
        # The __init__ method will handle merging defaults with overrides.
        return cls(technology_type=tech_type, **overrides)

# --- Registering Default Parameters for Specific Technologies ---
# These are illustrative values and should be based on actual data/research.

BaseTechnologyModel.register_defaults(
    ProductionTechnologyType.BF_BOF,
    {
        "raw_material_input_per_tonne_steel": {
            RawMaterialType.IRON_ORE: 1.4, # Tonnes of iron ore
            RawMaterialType.COKING_COAL: 0.7, # Tonnes of coking coal
            RawMaterialType.LIMESTONE: 0.25
        },
        "energy_consumption_mwh_per_tonne_steel": 5.0, # Primarily from coal
        "co2_emissions_tonne_per_tonne_steel": 1.8, # High emissions
        "typical_efficiency": 0.92,
        "indicative_opex_usd_per_tonne": 100, # Excluding materials/energy
        "indicative_capex_usd_per_tpa": 800,
        "min_operational_capacity_tpa": 1000000,
        "max_operational_capacity_tpa": 5000000,
    }
)

BaseTechnologyModel.register_defaults(
    ProductionTechnologyType.EAF,
    {
        "raw_material_input_per_tonne_steel": {
            RawMaterialType.SCRAP_STEEL: 1.1, # Primarily scrap-based
            RawMaterialType.ALLOYS: 0.05,
            RawMaterialType.LIMESTONE: 0.05
        },
        "energy_consumption_mwh_per_tonne_steel": 0.6, # Electricity intensive
        "co2_emissions_tonne_per_tonne_steel": 0.4, # Lower if using green electricity
        "typical_efficiency": 0.95,
        "indicative_opex_usd_per_tonne": 60,
        "indicative_capex_usd_per_tpa": 500,
        "min_operational_capacity_tpa": 200000,
        "max_operational_capacity_tpa": 2000000,
    }
)

BaseTechnologyModel.register_defaults(
    ProductionTechnologyType.DRI_EAF,
    {
        "raw_material_input_per_tonne_steel": {
            RawMaterialType.IRON_ORE: 1.4, # For DRI production
            RawMaterialType.NATURAL_GAS: 0.3, # Or other reductant, for DRI. This is a simplified placeholder.
            RawMaterialType.SCRAP_STEEL: 0.2, # Can use some scrap
            RawMaterialType.LIMESTONE: 0.1
        },
        "energy_consumption_mwh_per_tonne_steel": 2.5, # Energy for DRI + EAF
        "co2_emissions_tonne_per_tonne_steel": 1.0, # Lower than BF-BOF, depends on NG source
        "typical_efficiency": 0.90,
        "indicative_opex_usd_per_tonne": 120,
        "indicative_capex_usd_per_tpa": 1000,
        "min_operational_capacity_tpa": 500000,
        "max_operational_capacity_tpa": 3000000,
    }
)

BaseTechnologyModel.register_defaults(
    ProductionTechnologyType.HYDROGEN_DRI,
    {
        "raw_material_input_per_tonne_steel": {
            RawMaterialType.IRON_ORE: 1.4,
            RawMaterialType.HYDROGEN: 0.055, # Tonnes of H2 per tonne of DRI (approx 55kg H2/t DRI)
            RawMaterialType.SCRAP_STEEL: 0.1, # Optional scrap addition
        },
        "energy_consumption_mwh_per_tonne_steel": 3.0, # Energy for H2-DRI + EAF (electricity for EAF, potentially for H2 prod)
        "co2_emissions_tonne_per_tonne_steel": 0.1, # Very low if using green hydrogen and green electricity
        "typical_efficiency": 0.88,
        "indicative_opex_usd_per_tonne": 150, # Can be higher due to H2 cost
        "indicative_capex_usd_per_tpa": 1500,
        "min_operational_capacity_tpa": 500000,
        "max_operational_capacity_tpa": 2500000,
    }
)

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    bf_bof_model = BaseTechnologyModel.get_model_for_technology(ProductionTechnologyType.BF_BOF)
    logger.info(f"BF-BOF Model: {bf_bof_model.model_dump_json(indent=2)}")

    eaf_model_custom = BaseTechnologyModel.get_model_for_technology(
        ProductionTechnologyType.EAF, 
        co2_emissions_tonne_per_tonne_steel=0.15, # Override for specific plant using more renewables
        indicative_opex_usd_per_tonne=55
    )
    logger.info(f"Custom EAF Model: {eaf_model_custom.model_dump_json(indent=2)}")

    h2_model = BaseTechnologyModel.get_model_for_technology(ProductionTechnologyType.HYDROGEN_DRI)
    logger.info(f"H2-DRI Model CO2 emissions: {h2_model.co2_emissions_tonne_per_tonne_steel} t/t steel")
    logger.info(f"H2-DRI H2 consumption: {h2_model.raw_material_input_per_tonne_steel.get(RawMaterialType.HYDROGEN)} t H2/t steel")
