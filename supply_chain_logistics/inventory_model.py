"""
Inventory management models for the SteelPath simulation.

Handles tracking of raw material and finished product inventories, associated costs
(holding costs), and potentially stockout risks or service level calculations.
"""
import logging
from typing import Dict, Any, Optional, Union
from enum import Enum

from ..data_management.schemas import RawMaterialType, SteelProductType

logger = logging.getLogger(__name__)

class InventoryItemType(Enum):
    RAW_MATERIAL = "Raw Material"
    FINISHED_PRODUCT = "Finished Product"

class Inventory:
    """
    Represents an inventory for a specific item (raw material or finished product)
    at a particular location (e.g., a plant).
    """
    def __init__(self, item_id: Union[RawMaterialType, SteelProductType], 
                 item_type: InventoryItemType,
                 initial_quantity_tonnes: float = 0.0,
                 capacity_tonnes: Optional[float] = None,
                 holding_cost_usd_per_tonne_per_period: float = 0.1,
                 location_id: Optional[str] = None # e.g., plant_id
                 ):
        """
        Initializes an inventory account.

        Args:
            item_id (Union[RawMaterialType, SteelProductType]): The specific item being stored.
            item_type (InventoryItemType): Type of item.
            initial_quantity_tonnes (float): Starting quantity.
            capacity_tonnes (Optional[float]): Maximum storage capacity. None if unlimited.
            holding_cost_usd_per_tonne_per_period (float): Cost to hold one tonne for one simulation period.
            location_id (Optional[str]): Identifier for where this inventory is located.
        """
        self.item_id = item_id
        self.item_type = item_type
        self.quantity_tonnes = initial_quantity_tonnes
        self.capacity_tonnes = capacity_tonnes
        self.holding_cost_rate = holding_cost_usd_per_tonne_per_period
        self.location_id = location_id
        
        self.history: List[Dict[str, Any]] = [] # To track changes over time if needed
        logger.debug(f"Inventory initialized for {item_id} ({item_type.value}) at {location_id or 'unspecified location'} with {initial_quantity_tonnes} tonnes.")

    def add_stock(self, quantity_to_add: float, period: int) -> float:
        """
        Adds stock to the inventory.

        Args:
            quantity_to_add (float): Amount to add.
            period (int): Current simulation period for logging.

        Returns:
            float: The amount of stock actually added (could be less if capacity constrained).
        """
        if quantity_to_add < 0:
            logger.warning(f"Attempted to add negative stock ({quantity_to_add}) to {self.item_id}. Ignoring.")
            return 0

        available_capacity = float('inf')
        if self.capacity_tonnes is not None:
            available_capacity = self.capacity_tonnes - self.quantity_tonnes
        
        actually_added = min(quantity_to_add, available_capacity)
        
        self.quantity_tonnes += actually_added
        self._log_change(period, "add", actually_added, quantity_to_add > actually_added)
        
        if quantity_to_add > actually_added:
            logger.warning(f"Inventory capacity reached for {self.item_id} at {self.location_id}. Added {actually_added} instead of {quantity_to_add}.")
        return actually_added

    def remove_stock(self, quantity_to_remove: float, period: int) -> float:
        """
        Removes stock from the inventory.

        Args:
            quantity_to_remove (float): Amount to remove.
            period (int): Current simulation period for logging.

        Returns:
            float: The amount of stock actually removed (could be less if insufficient stock).
        """
        if quantity_to_remove < 0:
            logger.warning(f"Attempted to remove negative stock ({quantity_to_remove}) from {self.item_id}. Ignoring.")
            return 0

        actually_removed = min(quantity_to_remove, self.quantity_tonnes)
        self.quantity_tonnes -= actually_removed
        self._log_change(period, "remove", actually_removed, quantity_to_remove > actually_removed)

        if quantity_to_remove > actually_removed:
            logger.warning(f"Insufficient stock for {self.item_id} at {self.location_id}. Removed {actually_removed} instead of {quantity_to_remove}. Stockout occurred.")
        return actually_removed

    def get_current_stock_level(self) -> float:
        return self.quantity_tonnes

    def calculate_holding_cost(self, period_duration_fraction_of_year: float = 1.0/12) -> float:
        """
        Calculates the holding cost for the current stock level over a given period duration.
        Assumes holding_cost_rate is per some base period (e.g., per year), and this function scales it.
        For simplicity, let's assume holding_cost_rate is USD per tonne per period (e.g. month if period is month)
        """
        # If holding_cost_rate is annual, and period is monthly, then cost = Q * rate / 12
        # Here, assume self.holding_cost_rate is already for the 'period' of the simulation step.
        cost = self.quantity_tonnes * self.holding_cost_rate
        # self._log_change(period, "holding_cost_calc", cost, False) # If period is passed
        return cost

    def _log_change(self, period: int, action: str, amount: float, constrained: bool):
        self.history.append({
            "period": period,
            "action": action,
            "amount": amount,
            "constrained_by_capacity_or_stockout": constrained,
            "new_stock_level": self.quantity_tonnes
        })

class InventoryManager:
    """
    Manages multiple inventory accounts for an entity (e.g., a steel plant).
    """
    def __init__(self, manager_id: str):
        self.manager_id = manager_id
        self.inventories: Dict[Union[RawMaterialType, SteelProductType], Inventory] = {}
        logger.info(f"InventoryManager initialized for {manager_id}.")

    def add_inventory_item(self, inventory: Inventory):
        if inventory.item_id in self.inventories:
            logger.warning(f"Inventory for {inventory.item_id} already exists for {self.manager_id}. Overwriting is not allowed; update existing instead.")
            return
        self.inventories[inventory.item_id] = inventory
        logger.debug(f"Added inventory item {inventory.item_id} for manager {self.manager_id}.")

    def get_inventory(self, item_id: Union[RawMaterialType, SteelProductType]) -> Optional[Inventory]:
        return self.inventories.get(item_id)

    def process_period_end(self, period: int) -> Dict[str, float]:
        """Calculates total holding costs for all items for the period."""
        total_holding_cost = 0.0
        for item_id, inv in self.inventories.items():
            cost = inv.calculate_holding_cost()
            total_holding_cost += cost
            logger.debug(f"Holding cost for {item_id} at {self.manager_id} for period {period}: ${cost:.2f}")
        logger.info(f"Total holding cost for {self.manager_id} for period {period}: ${total_holding_cost:.2f}")
        return {"total_holding_cost": total_holding_cost}

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Create an inventory manager for a plant
    plant_X_inv_manager = InventoryManager(manager_id="PlantX")

    # Setup inventory for Iron Ore
    iron_ore_inv = Inventory(
        item_id=RawMaterialType.IRON_ORE,
        item_type=InventoryItemType.RAW_MATERIAL,
        initial_quantity_tonnes=10000,
        capacity_tonnes=50000,
        holding_cost_usd_per_tonne_per_period=0.5, # e.g., $0.5 per tonne per month
        location_id="PlantX"
    )
    plant_X_inv_manager.add_inventory_item(iron_ore_inv)

    # Setup inventory for Rebar (finished product)
    rebar_inv = Inventory(
        item_id=SteelProductType.REBAR,
        item_type=InventoryItemType.FINISHED_PRODUCT,
        initial_quantity_tonnes=500,
        capacity_tonnes=2000,
        holding_cost_usd_per_tonne_per_period=1.0,
        location_id="PlantX"
    )
    plant_X_inv_manager.add_inventory_item(rebar_inv)

    # Simulate some operations for period 1
    current_period = 1
    print(f"\n--- Period {current_period} --- ")
    # Receive Iron Ore shipment
    received_ore = iron_ore_inv.add_stock(5000, period=current_period)
    print(f"Received {received_ore} tonnes of Iron Ore. New stock: {iron_ore_inv.get_current_stock_level()} tonnes.")

    # Consume Iron Ore for production
    consumed_ore = iron_ore_inv.remove_stock(12000, period=current_period)
    print(f"Consumed {consumed_ore} tonnes of Iron Ore. New stock: {iron_ore_inv.get_current_stock_level()} tonnes.")

    # Produce Rebar
    produced_rebar = rebar_inv.add_stock(800, period=current_period)
    print(f"Produced {produced_rebar} tonnes of Rebar. New stock: {rebar_inv.get_current_stock_level()} tonnes.")

    # Ship Rebar (try to ship more than available)
    shipped_rebar = rebar_inv.remove_stock(1500, period=current_period)
    print(f"Shipped {shipped_rebar} tonnes of Rebar. New stock: {rebar_inv.get_current_stock_level()} tonnes.")

    # Calculate end-of-period holding costs
    period_costs = plant_X_inv_manager.process_period_end(period=current_period)
    print(f"Total holding costs for PlantX at end of period {current_period}: ${period_costs['total_holding_cost']:.2f}")

    # Try to overfill capacity
    print("\n--- Attempting to overfill Iron Ore --- ")
    ore_to_add_over_cap = 40000
    print(f"Current Iron Ore: {iron_ore_inv.get_current_stock_level()}, Capacity: {iron_ore_inv.capacity_tonnes}")
    actually_added_ore = iron_ore_inv.add_stock(ore_to_add_over_cap, period=current_period)
    print(f"Attempted to add {ore_to_add_over_cap}, actually added: {actually_added_ore}. New stock: {iron_ore_inv.get_current_stock_level()}")
