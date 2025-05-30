"""
Market models for the SteelPath simulation.

This module simulates market dynamics, including price formation based on supply,
 demand, and potentially other market factors for steel products and raw materials.
"""
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from ..data_management.schemas import MarketDataPointSchema, SteelProductType, RawMaterialType
# from ..simulation_core.base_agent import BaseAgent # If agents directly interact with market

logger = logging.getLogger(__name__)

class MarketClearingMechanism(Enum):
    SIMPLE_PRICE_ADJUSTMENT = "Simple Price Adjustment"
    AUCTION_BASED = "Auction Based"
    # Add other mechanisms as needed

class MarketModel:
    """
    Simulates market behavior for various commodities (steel products, raw materials).
    """
    def __init__(self, initial_market_conditions: Optional[List[MarketDataPointSchema]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initializes the MarketModel.

        Args:
            initial_market_conditions (Optional[List[MarketDataPointSchema]]): 
                A list of initial market data points.
            config (Optional[Dict[str, Any]]): Configuration for the market model, 
                                                e.g., price elasticity, clearing mechanism.
        """
        self.config = config if config else {}
        self.current_prices: Dict[Any, float] = {} # Keyed by (product_type, region) or RawMaterialType
        self.supply_offers: Dict[Any, Dict[str, float]] = {} # Key: (product/material, region), Value: {agent_id: quantity}
        self.demand_bids: Dict[Any, Dict[str, float]] = {}   # Key: (product/material, region), Value: {agent_id: quantity}
        
        if initial_market_conditions:
            for mdp in initial_market_conditions:
                key = (mdp.product_type, mdp.region) # Assuming MarketDataPointSchema is for products
                self.current_prices[key] = mdp.price_usd_per_tonne
        
        self.clearing_mechanism = MarketClearingMechanism[self.config.get("clearing_mechanism", "SIMPLE_PRICE_ADJUSTMENT")]
        self.price_adjustment_factor = self.config.get("price_adjustment_factor", 0.05) # e.g., 5% change based on imbalance

        logger.info(f"MarketModel initialized with {self.clearing_mechanism.value} clearing mechanism.")

    def submit_supply_offer(self, agent_id: str, item: Any, quantity: float, region: Optional[str] = None, price: Optional[float] = None):
        """
        An agent submits an offer to supply a certain quantity of an item.
        Args:
            agent_id (str): ID of the agent making the offer.
            item (Any): SteelProductType or RawMaterialType.
            quantity (float): Quantity offered.
            region (Optional[str]): Region for the offer (esp. for products).
            price (Optional[float]): Asking price (used in some mechanisms).
        """
        market_key = (item, region) if region else item
        if market_key not in self.supply_offers:
            self.supply_offers[market_key] = {}
        self.supply_offers[market_key][agent_id] = quantity # Could also store price
        logger.debug(f"Agent {agent_id} offered {quantity} of {item} in {region or 'global market'}.")

    def submit_demand_bid(self, agent_id: str, item: Any, quantity: float, region: Optional[str] = None, price: Optional[float] = None):
        """
        An agent submits a bid to demand a certain quantity of an item.
        Args:
            agent_id (str): ID of the agent making the bid.
            item (Any): SteelProductType or RawMaterialType.
            quantity (float): Quantity demanded.
            region (Optional[str]): Region for the bid.
            price (Optional[float]): Bid price (used in some mechanisms).
        """
        market_key = (item, region) if region else item
        if market_key not in self.demand_bids:
            self.demand_bids[market_key] = {}
        self.demand_bids[market_key][agent_id] = quantity # Could also store price
        logger.debug(f"Agent {agent_id} bid for {quantity} of {item} in {region or 'global market'}.")

    def get_market_price(self, item: Any, region: Optional[str] = None) -> Optional[float]:
        """
        Retrieves the current market price for an item in a specific region.
        """
        market_key = (item, region) if region else item
        price = self.current_prices.get(market_key)
        if price is None:
            logger.warning(f"Price for {item} in {region or 'global market'} not found.")
        return price

    def clear_market(self) -> Dict[str, Any]:
        """
        Clears the market based on the chosen mechanism, updates prices, and determines transactions.
        Returns:
            Dict[str, Any]: A summary of market clearing results (e.g., new prices, transactions).
        """
        logger.info("Clearing market...")
        transactions = [] # List of (seller_id, buyer_id, item, quantity, price)
        updated_prices = self.current_prices.copy()

        all_market_keys = set(self.supply_offers.keys()) | set(self.demand_bids.keys())

        for market_key in all_market_keys:
            total_supply = sum(self.supply_offers.get(market_key, {}).values())
            total_demand = sum(self.demand_bids.get(market_key, {}).values())
            current_price = self.current_prices.get(market_key, self.config.get("default_price", 100)) # Default if no price

            logger.debug(f"Market for {market_key}: Supply={total_supply}, Demand={total_demand}, Price=${current_price}")

            if self.clearing_mechanism == MarketClearingMechanism.SIMPLE_PRICE_ADJUSTMENT:
                if total_supply > 0 or total_demand > 0: # Avoid division by zero or no activity
                    imbalance = total_demand - total_supply
                    # Adjust price based on imbalance: if demand > supply, price increases, and vice-versa.
                    # This is a very basic model. Elasticity should be considered.
                    if total_supply > 0 : # Avoid division by zero if only demand exists
                        price_change_factor = (imbalance / total_supply) * self.price_adjustment_factor if total_supply > total_demand else (imbalance / total_demand) * self.price_adjustment_factor
                    elif total_demand > 0: # Only demand exists, price should likely go up significantly or stay at a ceiling
                        price_change_factor = self.price_adjustment_factor # Increase price if only demand
                    else: # No supply, no demand
                        price_change_factor = 0

                    new_price = current_price * (1 + price_change_factor)
                    new_price = max(new_price, self.config.get("min_price", 10)) # Price floor
                    updated_prices[market_key] = round(new_price, 2)
                    logger.info(f"Market {market_key}: Price updated from ${current_price:.2f} to ${new_price:.2f} (Imbalance: {imbalance})")
                
                # Simple transaction matching (pro-rata or random, not implemented here for brevity)
                # For now, just log the imbalance. Actual transactions would be more complex.

            elif self.clearing_mechanism == MarketClearingMechanism.AUCTION_BASED:
                # Implement auction logic (e.g., double auction)
                # This would involve matching bids and offers based on price, etc.
                logger.warning("Auction-based clearing not yet fully implemented.")
                updated_prices[market_key] = current_price # Placeholder

        self.current_prices = updated_prices
        # Reset offers and bids for the next period
        self.supply_offers.clear()
        self.demand_bids.clear()

        return {"new_prices": self.current_prices, "transactions": transactions} # Transactions not populated yet

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    initial_conditions = [
        MarketDataPointSchema(timestamp=date(2023,1,1), product_type=SteelProductType.REBAR, region="North America", price_usd_per_tonne=700)
    ]
    market_config = {"price_adjustment_factor": 0.1, "default_price": 100}
    market = MarketModel(initial_market_conditions=initial_conditions, config=market_config)

    # Simulate some agent actions
    market.submit_supply_offer(agent_id="PlantA", item=SteelProductType.REBAR, quantity=1000, region="North America")
    market.submit_supply_offer(agent_id="PlantB", item=SteelProductType.REBAR, quantity=1500, region="North America")
    market.submit_demand_bid(agent_id="BuyerX", item=SteelProductType.REBAR, quantity=2000, region="North America")
    market.submit_demand_bid(agent_id="BuyerY", item=SteelProductType.REBAR, quantity=1000, region="North America")

    print(f"Initial price for Rebar in NA: ${market.get_market_price(SteelProductType.REBAR, 'North America')}")
    results = market.clear_market()
    print(f"New price for Rebar in NA: ${results['new_prices'].get((SteelProductType.REBAR, 'North America'))}")

    # Test raw material market (no initial price, should use default)
    market.submit_supply_offer(agent_id="Supplier1", item=RawMaterialType.IRON_ORE, quantity=50000)
    market.submit_demand_bid(agent_id="PlantA", item=RawMaterialType.IRON_ORE, quantity=60000)
    results_rm = market.clear_market()
    print(f"New price for Iron Ore (global): ${results_rm['new_prices'].get(RawMaterialType.IRON_ORE)}")
