"""
Generates synthetic data for the SteelPath simulation.
This is useful for initializing the simulation when real data is not available
or for testing specific scenarios.
"""
import logging
import random
from typing import List, Dict, Any
from datetime import date, timedelta
import pandas as pd # For potential complex data generation or output

from .schemas import (SteelPlantSchema, Location, ProductionTechnologyType, RawMaterialSchema, 
                      RawMaterialType, MarketDataPointSchema, SteelProductType, CarbonPricingSchema)
# from ..config.settings import SimulationConfig # If config drives generation parameters

logger = logging.getLogger(__name__)

class SyntheticDataGenerator:
    """
    Generates various types of synthetic data based on predefined rules and randomness.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the generator.
        Args:
            config: Optional configuration dictionary to guide data generation.
        """
        self.config = config if config else {}
        self.rng = random.Random(self.config.get("random_seed", None)) # For reproducibility
        logger.info("SyntheticDataGenerator initialized.")

    def generate_location(self, country_list=None) -> Location:
        countries = country_list or ["USA", "China", "Germany", "India", "Brazil", "Russia", "Japan"]
        country = self.rng.choice(countries)
        return Location(
            country=country,
            region=f"{country}_Region_{self.rng.randint(1,5)}",
            latitude=self.rng.uniform(-90, 90),
            longitude=self.rng.uniform(-180, 180)
        )

    def generate_steel_plants(self, num_plants: int) -> List[SteelPlantSchema]:
        plants = []
        tech_types = list(ProductionTechnologyType)
        for i in range(num_plants):
            loc = self.generate_location()
            tech_mix = {}
            remaining_share = 1.0
            # Simple tech mix generation
            if self.rng.random() < 0.7: # Predominantly one tech
                main_tech = self.rng.choice(tech_types)
                tech_mix[main_tech] = remaining_share
            else: # Mix of two
                t1, t2 = self.rng.sample(tech_types, 2)
                s1 = self.rng.uniform(0.3, 0.7)
                tech_mix[t1] = round(s1, 2)
                tech_mix[t2] = round(1.0 - s1, 2)
            
            # Ensure sum is 1.0 after rounding
            current_sum = sum(tech_mix.values())
            if not (0.999 <= current_sum <= 1.001) and tech_mix:
                # Basic correction: assign remainder to the largest share
                if tech_mix:
                    largest_share_tech = max(tech_mix, key=tech_mix.get)
                    tech_mix[largest_share_tech] += (1.0 - current_sum)
                    tech_mix[largest_share_tech] = round(tech_mix[largest_share_tech],2)
            
            # Final check, if still not 1.0 due to multiple small shares, force it
            current_sum = sum(tech_mix.values())
            if not (0.999 <= current_sum <= 1.001) and tech_mix:
                 first_tech = list(tech_mix.keys())[0]
                 tech_mix[first_tech] = 1.0 - sum(v for k,v in tech_mix.items() if k != first_tech)
                 tech_mix[first_tech] = round(tech_mix[first_tech],2)

            if not tech_mix: # Fallback if empty
                tech_mix[self.rng.choice(tech_types)] = 1.0

            plant = SteelPlantSchema(
                plant_id=f"SYNTH_P{i+1:03d}",
                name=f"Synthetic Steel Plant {chr(65+i%26)}{(i//26)+1}",
                location=loc,
                production_capacity_tonnes_per_year=self.rng.uniform(500000, 10000000),
                current_technology_mix=tech_mix,
                operational_since=date(self.rng.randint(1980, 2020), self.rng.randint(1,12), self.rng.randint(1,28)),
                efficiency_factor=self.rng.uniform(0.85, 1.05)
            )
            plants.append(plant)
        logger.info(f"Generated {len(plants)} synthetic steel plants.")
        return plants

    def generate_raw_materials(self, num_material_types: int, num_sources_per_type: int) -> List[RawMaterialSchema]:
        materials = []
        material_types = list(RawMaterialType)
        for i in range(num_material_types):
            mat_type = self.rng.choice(material_types)
            for j in range(num_sources_per_type):
                material = RawMaterialSchema(
                    material_id=f"SYNTH_RM_{mat_type.name}_{j+1:02d}",
                    material_type=mat_type,
                    source_location=self.generate_location(),
                    quality_grade=f"Grade {self.rng.choice(['A', 'B', 'C'])}",
                    available_quantity_tonnes=self.rng.uniform(10000, 500000),
                    unit_cost_usd_per_tonne=self.rng.uniform(50, 800), # Wide range, depends on material
                    supplier_id=f"SYNTH_SUP_{self.rng.randint(1,20):02d}"
                )
                materials.append(material)
        logger.info(f"Generated {len(materials)} synthetic raw material entries.")
        return materials

    def generate_market_data(self, start_date_str: str, num_days: int, num_product_types: int, regions: List[str]) -> List[MarketDataPointSchema]:
        market_points = []
        product_types = self.rng.sample(list(SteelProductType), min(num_product_types, len(SteelProductType)))
        current_date = date.fromisoformat(start_date_str)

        base_prices = {ptype: self.rng.uniform(500,1200) for ptype in product_types}

        for day_idx in range(num_days):
            for region in regions:
                for p_type in product_types:
                    price_fluctuation = self.rng.uniform(-0.02, 0.02) # +/- 2% daily fluctuation
                    current_price = base_prices[p_type] * (1 + price_fluctuation)
                    base_prices[p_type] = current_price # Price walks randomly
                    
                    point = MarketDataPointSchema(
                        timestamp=current_date,
                        product_type=p_type,
                        region=region,
                        price_usd_per_tonne=max(50, round(current_price, 2)), # Ensure price doesn't go too low
                        demand_tonnes=self.rng.uniform(1000, 50000),
                        supply_tonnes=self.rng.uniform(800, 45000)
                    )
                    market_points.append(point)
            current_date += timedelta(days=1)
        logger.info(f"Generated {len(market_points)} synthetic market data points.")
        return market_points

    def generate_all_synthetic_data(self, params: Dict[str, Any]) -> Dict[str, List[Any]]:
        """
        Generates a comprehensive set of synthetic data based on input parameters.

        Args:
            params (Dict[str, Any]): Parameters to guide data generation, e.g.,
                {
                    "num_plants": 10,
                    "num_raw_material_types": 5,
                    "num_sources_per_material_type": 3,
                    "market_data_start_date": "2023-01-01",
                    "market_data_days": 30,
                    "market_product_types": 3,
                    "market_regions": ["North America", "Europe", "Asia"]
                }
        """
        logger.info("Generating all synthetic data based on parameters...")
        data = {}
        data["steel_plants"] = self.generate_steel_plants(params.get("num_plants", 5))
        data["raw_materials"] = self.generate_raw_materials(
            params.get("num_raw_material_types", 3),
            params.get("num_sources_per_material_type", 2)
        )
        data["market_data"] = self.generate_market_data(
            params.get("market_data_start_date", "2023-01-01"),
            params.get("market_data_days", 30),
            params.get("market_product_types", 2),
            params.get("market_regions", ["Global_East", "Global_West"])
        )
        # Add generation for other data types like transportation routes, carbon pricing etc.
        logger.info("Finished generating all synthetic data.")
        return data

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    generator = SyntheticDataGenerator(config={"random_seed": 42})

    plants = generator.generate_steel_plants(num_plants=3)
    for p in plants:
        print(p.model_dump_json(indent=2))

    materials = generator.generate_raw_materials(num_material_types=2, num_sources_per_type=1)
    for m in materials:
        print(m.model_dump_json(indent=2))
    
    market_params = {
        "market_data_start_date": "2024-01-01",
        "market_data_days": 2,
        "market_product_types": 1,
        "market_regions": ["TestRegion"]
    }
    market_data = generator.generate_market_data(**market_params)
    for md in market_data:
        print(md.model_dump_json(indent=2))

    all_data_params = {
        "num_plants": 2,
        "num_raw_material_types": 1,
        "num_sources_per_material_type": 1,
        "market_data_start_date": "2024-01-01",
        "market_data_days": 1,
        "market_product_types": 1,
        "market_regions": ["RegionX"]
    }
    
    comprehensive_data = generator.generate_all_synthetic_data(all_data_params)
    print(f"\nGenerated {len(comprehensive_data['steel_plants'])} plants, {len(comprehensive_data['raw_materials'])} materials, {len(comprehensive_data['market_data'])} market points.")
