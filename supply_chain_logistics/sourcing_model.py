"""
Sourcing models for raw materials in the SteelPath simulation.

Helps agents decide which suppliers to source raw materials from, considering factors
like price, availability, transportation costs, lead times, and supplier reliability.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

from ..data_management.schemas import RawMaterialSchema, RawMaterialType, TransportationRouteSchema
from .transport_model import TransportCostCalculator
# from ..economic_financial_modeling.market_model import MarketModel # If prices are dynamic from a market

logger = logging.getLogger(__name__)

class SupplierInfo(BaseModel):
    supplier_id: str
    material_type: RawMaterialType
    available_quantity_tonnes: float
    unit_price_usd_per_tonne: float # Price at supplier's location (FOB)
    location: Any # Could be a simple string ID or a Location schema
    # Optional: reliability_score (0-1), lead_time_from_supplier_days (processing time at supplier)

class SourcingDecision:
    """
    Represents a decision to source a certain quantity of material from a specific supplier.
    """
    def __init__(self, supplier: SupplierInfo, quantity_tonnes: float,
                 transport_route: Optional[TransportationRouteSchema],
                 transport_details: Optional[Dict[str, Any]],
                 total_delivered_cost_usd_per_tonne: float):
        self.supplier = supplier
        self.quantity_tonnes = quantity_tonnes
        self.transport_route = transport_route
        self.transport_details = transport_details # Cost, lead time, emissions from TransportCostCalculator
        self.total_delivered_cost_usd_per_tonne = total_delivered_cost_usd_per_tonne
        self.total_cost_for_quantity = total_delivered_cost_usd_per_tonne * quantity_tonnes

    def __repr__(self):
        return (f"SourcingDecision(Supplier: {self.supplier.supplier_id}, Qty: {self.quantity_tonnes}t, "
                f"Delivered Cost/t: ${self.total_delivered_cost_usd_per_tonne:.2f}, Total Cost: ${self.total_cost_for_quantity:.2f})")

class SourcingOptimizer:
    """
    Optimizes sourcing decisions for a purchasing agent (e.g., a steel plant).
    """
    def __init__(self, transport_calc: TransportCostCalculator, 
                 # market_model: Optional[MarketModel] = None, # If using dynamic market prices
                 config: Optional[Dict[str, Any]] = None):
        """
        Initializes the SourcingOptimizer.
        Args:
            transport_calc (TransportCostCalculator): For calculating transport costs and details.
            config (Optional[Dict[str, Any]]): Configuration for sourcing logic, e.g., risk aversion.
        """
        self.transport_calc = transport_calc
        # self.market_model = market_model 
        self.config = config if config else {}
        logger.info("SourcingOptimizer initialized.")

    def find_best_suppliers(self, 
                            demanded_material: RawMaterialType, 
                            demanded_quantity_tonnes: float,
                            available_suppliers: List[SupplierInfo],
                            plant_location: Any, # Location of the demanding plant
                            available_routes: List[TransportationRouteSchema]
                           ) -> List[SourcingDecision]:
        """
        Finds the best supplier(s) to meet a demand for a raw material.
        This is a simplified greedy approach: sorts by delivered cost and picks until demand is met.
        More complex models could use linear programming for true optimization across multiple materials/suppliers.

        Args:
            demanded_material (RawMaterialType): The type of material needed.
            demanded_quantity_tonnes (float): The total quantity needed.
            available_suppliers (List[SupplierInfo]): List of potential suppliers for this material.
            plant_location (Any): The location of the plant (used as destination for transport).
            available_routes (List[TransportationRouteSchema]): All possible transport routes.

        Returns:
            List[SourcingDecision]: A list of sourcing decisions, ordered by preference, 
                                    attempting to fulfill the demanded quantity.
        """
        if demanded_quantity_tonnes <= 0:
            return []

        candidate_options: List[Tuple[float, SupplierInfo, TransportationRouteSchema, Dict[str, Any]]] = []

        for supplier in available_suppliers:
            if supplier.material_type != demanded_material or supplier.available_quantity_tonnes <= 0:
                continue

            # Find a route from this supplier to the plant
            # This is a simplification; route finding can be complex.
            # Assume direct routes are listed in available_routes.
            # A real system might query a route database or use a graph algorithm.
            route_to_plant = None
            for r in available_routes:
                # Matching criteria for route: supplier location to plant location for the material
                # This requires locations to be comparable. For simplicity, assume location is an ID.
                # A more robust way is to use Location objects and check for equality or proximity.
                if hasattr(supplier.location, 'country') and hasattr(plant_location, 'country'): # If using Location schema
                    if r.origin_location.country == supplier.location.country and \
                       r.destination_location.country == plant_location.country: # Simplified match
                        route_to_plant = r
                        break
                elif isinstance(supplier.location, str) and isinstance(plant_location, str):
                    if r.origin_location == supplier.location and r.destination_location == plant_location:
                         route_to_plant = r
                         break
            
            if not route_to_plant:
                logger.debug(f"No direct transport route found from supplier {supplier.supplier_id} at {supplier.location} to plant at {plant_location}.")
                continue

            # Calculate transport details for a nominal 1 tonne (or full quantity if fixed trip costs dominate)
            # For per-tonne-km costs, quantity doesn't change per-tonne transport cost, but affects total and emissions.
            # Let's use 1 tonne for per-unit cost calculation, then scale for actual quantity.
            transport_details_per_tonne = self.transport_calc.get_transport_details(route_to_plant, quantity_tonnes=1)

            if not transport_details_per_tonne:
                logger.warning(f"Could not get transport details for route {route_to_plant.route_id} for supplier {supplier.supplier_id}.")
                continue
            
            transport_cost_per_tonne = transport_details_per_tonne['cost_usd']
            delivered_cost_per_tonne = supplier.unit_price_usd_per_tonne + transport_cost_per_tonne
            
            candidate_options.append((delivered_cost_per_tonne, supplier, route_to_plant, transport_details_per_tonne))

        # Sort candidates by the lowest delivered cost per tonne
        candidate_options.sort(key=lambda x: x[0])

        sourcing_decisions: List[SourcingDecision] = []
        remaining_demand = demanded_quantity_tonnes

        for cost_per_tonne, supplier, route, base_transport_details in candidate_options:
            if remaining_demand <= 0: break

            quantity_from_this_supplier = min(remaining_demand, supplier.available_quantity_tonnes)
            if quantity_from_this_supplier <= 0: continue

            # Recalculate transport details for the actual quantity (esp. for emissions, num_trips)
            actual_transport_details = self.transport_calc.get_transport_details(route, quantity_from_this_supplier)
            if not actual_transport_details:
                 logger.error(f"Failed to recalculate transport for actual quantity {quantity_from_this_supplier} from {supplier.supplier_id}")
                 continue # Should not happen if per-tonne worked

            decision = SourcingDecision(
                supplier=supplier,
                quantity_tonnes=quantity_from_this_supplier,
                transport_route=route,
                transport_details=actual_transport_details,
                total_delivered_cost_usd_per_tonne=cost_per_tonne
            )
            sourcing_decisions.append(decision)
            remaining_demand -= quantity_from_this_supplier
            logger.info(f"Selected supplier {supplier.supplier_id} for {quantity_from_this_supplier}t of {demanded_material.value} at ${cost_per_tonne:.2f}/t delivered.")

        if remaining_demand > 0:
            logger.warning(f"Could not fully meet demand for {demanded_material.value}. Shortfall of {remaining_demand:.2f} tonnes.")
        
        return sourcing_decisions

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Dependencies
    transport_calculator = TransportCostCalculator()

    # Plant Location (simplified)
    plant_loc_schema = Location(country="Germany", region="Ruhr")

    # Available Suppliers (SupplierInfo instances)
    supplier1 = SupplierInfo(supplier_id="S1", material_type=RawMaterialType.IRON_ORE, available_quantity_tonnes=100000, unit_price_usd_per_tonne=110, location=Location(country="Brazil"))
    supplier2 = SupplierInfo(supplier_id="S2", material_type=RawMaterialType.IRON_ORE, available_quantity_tonnes=50000, unit_price_usd_per_tonne=120, location=Location(country="Australia"))
    supplier3 = SupplierInfo(supplier_id="S3", material_type=RawMaterialType.COKING_COAL, available_quantity_tonnes=30000, unit_price_usd_per_tonne=280, location=Location(country="Australia"))
    supplier4 = SupplierInfo(supplier_id="S4", material_type=RawMaterialType.IRON_ORE, available_quantity_tonnes=20000, unit_price_usd_per_tonne=100, location=Location(country="Sweden")) # Closer, potentially cheaper transport

    suppliers_list = [supplier1, supplier2, supplier3, supplier4]

    # Available Routes (TransportationRouteSchema instances)
    # Simplified: Assume direct routes exist and their costs are per tonne-km from default modes
    # A real setup would have specific route data (distance, specific costs, etc.)
    routes_list = [
        TransportationRouteSchema(route_id="R_BR_DE", origin_location=supplier1.location, destination_location=plant_loc_schema, mode="Ship_Ocean", distance_km=10000, cost_usd_per_tonne_km=DEFAULT_TRANSPORT_MODES["Ship_Ocean"].cost_usd_per_tonne_km),
        TransportationRouteSchema(route_id="R_AU_DE", origin_location=supplier2.location, destination_location=plant_loc_schema, mode="Ship_Ocean", distance_km=15000, cost_usd_per_tonne_km=DEFAULT_TRANSPORT_MODES["Ship_Ocean"].cost_usd_per_tonne_km),
        TransportationRouteSchema(route_id="R_SE_DE", origin_location=supplier4.location, destination_location=plant_loc_schema, mode="Ship_Coastal", distance_km=1000, cost_usd_per_tonne_km=DEFAULT_TRANSPORT_MODES["Ship_Coastal"].cost_usd_per_tonne_km),
    ]

    # Sourcing Optimizer
    optimizer = SourcingOptimizer(transport_calc=transport_calculator)

    # Scenario: Demand for Iron Ore
    demand_qty_iron_ore = 70000 # tonnes
    print(f"\n--- Sourcing {demand_qty_iron_ore}t of Iron Ore --- ")
    iron_ore_decisions = optimizer.find_best_suppliers(
        demanded_material=RawMaterialType.IRON_ORE,
        demanded_quantity_tonnes=demand_qty_iron_ore,
        available_suppliers=suppliers_list,
        plant_location=plant_loc_schema,
        available_routes=routes_list
    )

    if iron_ore_decisions:
        for decision in iron_ore_decisions:
            print(decision)
            # print(f"  Transport cost: ${decision.transport_details['cost_usd'] / decision.quantity_tonnes if decision.quantity_tonnes else 0:.2f}/t, Emissions: {decision.transport_details['emissions_kgco2e']:.2f} kg CO2e")
    else:
        print("No suitable suppliers found or demand could not be met.")
    
    total_sourced = sum(d.quantity_tonnes for d in iron_ore_decisions)
    print(f"Total Iron Ore Sourced: {total_sourced} / {demand_qty_iron_ore} tonnes")
