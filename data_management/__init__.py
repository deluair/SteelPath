"""
Data Management Module for SteelPath.

Handles data loading, validation schemas, and synthetic data generation.
"""

from .schemas import (
    SteelPlantSchema, Location, ProductionTechnologyType, 
    RawMaterialSchema, RawMaterialType, 
    MarketDataPointSchema, SteelProductType,
    TransportationRouteSchema, CarbonPricingSchema,
    BaseSchema # Exporting BaseSchema can be useful too
)
from .data_loader import DataLoader
from .synthetic_data_generator import SyntheticDataGenerator

__all__ = [
    # Schemas
    "SteelPlantSchema",
    "Location",
    "ProductionTechnologyType",
    "RawMaterialSchema",
    "RawMaterialType",
    "MarketDataPointSchema",
    "SteelProductType",
    "TransportationRouteSchema",
    "CarbonPricingSchema",
    "BaseSchema",
    # Classes
    "DataLoader",
    "SyntheticDataGenerator"
]
