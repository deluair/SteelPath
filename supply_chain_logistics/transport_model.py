"""
Models for transportation within the SteelPath simulation.

This module defines costs, lead times, capacities, and emissions associated
with different modes of transporting raw materials and finished steel products.
"""
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from ..data_management.schemas import Location, TransportationRouteSchema, RawMaterialType, SteelProductType
# from ..environmental_impact.emission_calculator import EmissionCalculator # If calculating transport emissions here

logger = logging.getLogger(__name__)

class TransportMode(BaseModel):
    mode_name: str
    cost_usd_per_tonne_km: float = Field(..., gt=0)
    capacity_tonnes_per_trip: Optional[float] = Field(default=None, gt=0)
    avg_speed_km_per_hour: Optional[float] = Field(default=None, gt=0)
    # Emissions factor (e.g., gCO2e per tonne-km) - could be detailed or simple
    co2e_g_per_tonne_km: float = Field(default=0, ge=0, description="CO2 equivalent emissions in grams per tonne-km")

    def calculate_trip_cost(self, distance_km: float, quantity_tonnes: float) -> float:
        return self.cost_usd_per_tonne_km * distance_km * quantity_tonnes

    def calculate_lead_time_hours(self, distance_km: float) -> Optional[float]:
        if self.avg_speed_km_per_hour and self.avg_speed_km_per_hour > 0:
            return distance_km / self.avg_speed_km_per_hour
        return None
    
    def calculate_trip_emissions_kgco2e(self, distance_km: float, quantity_tonnes: float) -> float:
        return (self.co2e_g_per_tonne_km * distance_km * quantity_tonnes) / 1000.0 # Convert grams to kg

# Predefined transport modes (can be loaded from config or data)
DEFAULT_TRANSPORT_MODES: Dict[str, TransportMode] = {
    "Truck": TransportMode(mode_name="Truck", cost_usd_per_tonne_km=0.15, capacity_tonnes_per_trip=25, avg_speed_km_per_hour=60, co2e_g_per_tonne_km=150),
    "Rail": TransportMode(mode_name="Rail", cost_usd_per_tonne_km=0.05, capacity_tonnes_per_trip=2000, avg_speed_km_per_hour=40, co2e_g_per_tonne_km=30),
    "Ship_Coastal": TransportMode(mode_name="Ship_Coastal", cost_usd_per_tonne_km=0.02, capacity_tonnes_per_trip=10000, avg_speed_km_per_hour=20, co2e_g_per_tonne_km=15),
    "Ship_Ocean": TransportMode(mode_name="Ship_Ocean", cost_usd_per_tonne_km=0.01, capacity_tonnes_per_trip=50000, avg_speed_km_per_hour=25, co2e_g_per_tonne_km=10),
    "Pipeline": TransportMode(mode_name="Pipeline", cost_usd_per_tonne_km=0.03, co2e_g_per_tonne_km=5) # Capacity/speed might not be per trip
}

class TransportCostCalculator:
    """
    Calculates transportation costs, lead times, and emissions for given routes and quantities.
    """
    def __init__(self, transport_modes: Optional[Dict[str, TransportMode]] = None):
        """
        Initializes the calculator with available transport modes.
        Args:
            transport_modes (Optional[Dict[str, TransportMode]]): A dictionary of available transport modes.
                                                                  If None, uses DEFAULT_TRANSPORT_MODES.
        """
        self.modes = transport_modes if transport_modes else DEFAULT_TRANSPORT_MODES
        logger.info(f"TransportCostCalculator initialized with {len(self.modes)} modes.")

    def get_transport_details(self, route: TransportationRouteSchema, quantity_tonnes: float) -> Optional[Dict[str, Any]]:
        """
        Calculates cost, lead time, and emissions for transporting a given quantity along a route.

        Args:
            route (TransportationRouteSchema): The transportation route schema.
            quantity_tonnes (float): The quantity of goods to transport in tonnes.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with 'cost_usd', 'lead_time_days', 'emissions_kgco2e',
                                      or None if the mode is not found or data is insufficient.
        """
        mode_name = route.mode
        if mode_name not in self.modes:
            logger.warning(f"Transport mode '{mode_name}' not found in calculator.")
            return None

        mode = self.modes[mode_name]
        
        # Use route-specific costs/times if available, otherwise calculate from mode defaults
        total_cost = route.cost_usd_per_tonne_km * route.distance_km * quantity_tonnes
        
        lead_time_hours = None
        if route.lead_time_days is not None:
            lead_time_hours = route.lead_time_days * 24
        elif mode.avg_speed_km_per_hour:
            lead_time_hours = mode.calculate_lead_time_hours(route.distance_km)
        
        lead_time_days_calc = lead_time_hours / 24.0 if lead_time_hours is not None else None

        # Emissions calculation
        # This could be more sophisticated, e.g., using an EmissionCalculator instance
        emissions_kg = mode.calculate_trip_emissions_kgco2e(route.distance_km, quantity_tonnes)

        # Consider capacity constraints if relevant for the calculation context
        # (e.g., number of trips required)
        num_trips = 1
        if mode.capacity_tonnes_per_trip and quantity_tonnes > mode.capacity_tonnes_per_trip:
            num_trips = (quantity_tonnes + mode.capacity_tonnes_per_trip -1) // mode.capacity_tonnes_per_trip # Ceiling division
            # Adjust cost and emissions if they are per-trip rather than per-tonne-km in some models
            # Current model is per-tonne-km, so num_trips mainly affects lead time if trips are sequential
            # or if there's a per-trip fixed cost (not modeled here yet)

        return {
            "cost_usd": total_cost,
            "lead_time_days": lead_time_days_calc,
            "emissions_kgco2e": emissions_kg,
            "num_trips_if_constrained": num_trips,
            "mode_used": mode_name
        }

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    calculator = TransportCostCalculator()

    # Dummy route
    route_data = {
        "route_id": "R1",
        "origin_location": {"country": "A"},
        "destination_location": {"country": "B"},
        "mode": "Rail",
        "distance_km": 1000,
        "cost_usd_per_tonne_km": 0.045, # Route specific cost
        # "lead_time_days": 2.5 # Route specific lead time
    }
    sample_route = TransportationRouteSchema(**route_data)
    quantity = 5000 # tonnes

    details = calculator.get_transport_details(sample_route, quantity)
    if details:
        print(f"\nTransport Details for Route {sample_route.route_id} ({quantity} tonnes via {details['mode_used']}):")
        print(f"  Cost: ${details['cost_usd']:.2f}")
        print(f"  Lead Time: {details['lead_time_days']:.2f} days" if details['lead_time_days'] is not None else "  Lead Time: N/A")
        print(f"  Emissions: {details['emissions_kgco2e']:.2f} kg CO2e")
        print(f"  Number of trips (if capacity constrained by mode): {details['num_trips_if_constrained']}")

    # Example with a mode not having avg_speed (e.g., Pipeline if lead time is fixed or complex)
    route_data_pipeline = route_data.copy()
    route_data_pipeline["mode"] = "Pipeline"
    route_data_pipeline["cost_usd_per_tonne_km"] = DEFAULT_TRANSPORT_MODES["Pipeline"].cost_usd_per_tonne_km
    route_data_pipeline["lead_time_days"] = 5 # Assume fixed for pipeline
    sample_pipeline_route = TransportationRouteSchema(**route_data_pipeline)
    
    pipeline_details = calculator.get_transport_details(sample_pipeline_route, 100000)
    if pipeline_details:
        print(f"\nTransport Details for Route {sample_pipeline_route.route_id} ({100000} tonnes via {pipeline_details['mode_used']}):")
        print(f"  Cost: ${pipeline_details['cost_usd']:.2f}")
        print(f"  Lead Time: {pipeline_details['lead_time_days']:.2f} days")
        print(f"  Emissions: {pipeline_details['emissions_kgco2e']:.2f} kg CO2e")
