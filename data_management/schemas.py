"""
Pydantic schemas for data validation and structure definition in SteelPath.
"""
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import date

logger = logging.getLogger(__name__)

class ProductionTechnologyType(str, Enum):
    BF_BOF = "Blast Furnace-Basic Oxygen Furnace"
    EAF = "Electric Arc Furnace"
    DRI_EAF = "Direct Reduced Iron - Electric Arc Furnace"
    HYDROGEN_DRI = "Hydrogen-based DRI"
    ELECTROLYSIS = "Electrolysis-based"

class RawMaterialType(str, Enum):
    IRON_ORE = "Iron Ore"
    COKING_COAL = "Coking Coal"
    SCRAP_STEEL = "Scrap Steel"
    NATURAL_GAS = "Natural Gas"
    HYDROGEN = "Hydrogen"
    LIMESTONE = "Limestone"
    ALLOYS = "Alloys"

class SteelProductType(str, Enum):
    REBAR = "Rebar"
    STEEL_COIL = "Steel Coil"
    STEEL_PLATE = "Steel Plate"
    STRUCTURAL_STEEL = "Structural Steel"
    SPECIALTY_ALLOY = "Specialty Alloy"

class BaseSchema(BaseModel):
    class Config:
        anystr_strip_whitespace = True
        validate_assignment = True

class Location(BaseSchema):
    country: str = Field(..., description="Country of location")
    region: Optional[str] = Field(default=None, description="Region or state within the country")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Longitude")

class SteelPlantSchema(BaseSchema):
    plant_id: str = Field(..., description="Unique identifier for the steel plant")
    name: str = Field(..., description="Name of the steel plant")
    location: Location
    production_capacity_tonnes_per_year: float = Field(..., gt=0, description="Annual production capacity in tonnes")
    current_technology_mix: Dict[ProductionTechnologyType, float] = Field(..., description="Share of production by technology type (e.g., {ProductionTechnologyType.BF_BOF: 0.7, ProductionTechnologyType.EAF: 0.3})")
    operational_since: Optional[date] = Field(default=None, description="Date when the plant became operational")
    # Add more fields like emissions_intensity, energy_consumption_profile, etc.
    raw_material_storage_capacity: Optional[Dict[RawMaterialType, float]] = Field(default_factory=dict, description="Storage capacity for different raw materials in tonnes")
    efficiency_factor: float = Field(default=1.0, ge=0.5, le=1.5, description="Overall plant efficiency factor")

    @validator('current_technology_mix')
    def check_technology_mix_shares(cls, v):
        if not (0.999 <= sum(v.values()) <= 1.001): # Allow for small floating point inaccuracies
            raise ValueError('Technology mix shares must sum to approximately 1.0')
        for tech, share in v.items():
            if not (0 <= share <= 1):
                raise ValueError(f'Share for {tech} must be between 0 and 1')
        return v

class RawMaterialSchema(BaseSchema):
    material_id: str = Field(..., description="Unique ID for this batch/type of raw material")
    material_type: RawMaterialType
    source_location: Optional[Location] = Field(default=None)
    quality_grade: Optional[str] = Field(default=None, description="Quality grade, e.g., Fe content for iron ore")
    available_quantity_tonnes: float = Field(..., ge=0)
    unit_cost_usd_per_tonne: float = Field(..., ge=0)
    supplier_id: Optional[str] = Field(default=None)

class MarketDataPointSchema(BaseSchema):
    timestamp: date # or datetime
    product_type: SteelProductType
    region: str
    price_usd_per_tonne: float = Field(..., ge=0)
    demand_tonnes: Optional[float] = Field(default=None, ge=0)
    supply_tonnes: Optional[float] = Field(default=None, ge=0)

class TransportationRouteSchema(BaseSchema):
    route_id: str
    origin_location: Location
    destination_location: Location
    mode: str = Field(..., description="e.g., Ship, Rail, Truck")
    distance_km: float = Field(..., gt=0)
    cost_usd_per_tonne_km: float = Field(..., ge=0)
    capacity_tonnes_per_trip: Optional[float] = Field(default=None, gt=0)
    lead_time_days: Optional[float] = Field(default=None, ge=0)

class CarbonPricingSchema(BaseSchema):
    region: str
    start_date: date
    price_usd_per_tonne_co2: float = Field(..., ge=0)
    mechanism: str = Field(default="Carbon Tax", description="e.g., Carbon Tax, ETS Allowance Price")

# Example usage:
if __name__ == "__main__":
    plant_data = {
        "plant_id": "SP001",
        "name": "Global Steel Works",
        "location": {"country": "Germany", "region": "North Rhine-Westphalia"},
        "production_capacity_tonnes_per_year": 5000000,
        "current_technology_mix": {ProductionTechnologyType.BF_BOF: 1.0}
    }
    try:
        plant = SteelPlantSchema(**plant_data)
        print(f"Valid Plant: {plant.name}, ID: {plant.plant_id}")
        plant.location.latitude = 50.0
        print(f"Plant latitude: {plant.location.latitude}")
    except ValueError as e:
        print(f"Validation Error: {e}")

    invalid_mix_data = plant_data.copy()
    invalid_mix_data["current_technology_mix"] = {ProductionTechnologyType.BF_BOF: 0.7, ProductionTechnologyType.EAF: 0.2}
    try:
        SteelPlantSchema(**invalid_mix_data)
    except ValueError as e:
        print(f"Validation Error for mix: {e}")
