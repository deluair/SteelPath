"""
Data loading utilities for the SteelPath simulation.
Capable of loading data from various sources like CSV files.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

# from ..config.settings import DataPaths # Assuming config structure
from .schemas import (SteelPlantSchema, RawMaterialSchema, MarketDataPointSchema, 
                      TransportationRouteSchema, CarbonPricingSchema) # Add other schemas as needed

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Handles loading of all necessary data for the simulation.
    """
    def __init__(self, input_data_dir: Optional[Path] = None):
        """
        Initializes the DataLoader.

        Args:
            input_data_dir (Optional[Path]): The base directory where input data files are located.
        """
        self.input_data_dir = input_data_dir
        if self.input_data_dir and not self.input_data_dir.is_dir():
            logger.warning(f"Input data directory not found: {self.input_data_dir}. DataLoader may not find files.")

    def _load_csv_data(self, file_name: str, schema: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Helper function to load data from a CSV file and optionally validate with a Pydantic schema.

        Args:
            file_name (str): The name of the CSV file (e.g., "plants.csv").
            schema (Optional[Any]): The Pydantic schema to validate each row against.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a row.
                                   Returns an empty list if file not found or on error.
        """
        if not self.input_data_dir:
            logger.error("Input data directory not set. Cannot load CSV data.")
            return []
        
        file_path = self.input_data_dir / file_name
        try:
            df = pd.read_csv(file_path)
            # Convert NaNs to None for Pydantic compatibility if necessary
            df = df.where(pd.notnull(df), None)
            records = df.to_dict(orient='records')
            if schema:
                validated_records = []
                for i, record in enumerate(records):
                    try:
                        # Pydantic models expect nested dicts, not dot-notation from flat CSVs directly for nested schemas
                        # This might require pre-processing if CSV is flat for nested models like Location in SteelPlantSchema
                        # For simplicity, assuming CSV structure matches schema or pre-processing is done.
                        validated_records.append(schema(**record).model_dump())
                    except ValueError as e:
                        logger.error(f"Validation error in {file_name}, row {i+2}: {e} for record {record}")
                        # Decide whether to skip, raise, or include partially
                logger.info(f"Successfully loaded and validated {len(validated_records)} records from {file_name}.")
                return validated_records
            else:
                logger.info(f"Successfully loaded {len(records)} records from {file_name} (no schema validation).")
                return records
        except FileNotFoundError:
            logger.error(f"Data file not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return []

    def load_steel_plants(self, file_name: str = "steel_plants.csv") -> List[SteelPlantSchema]:
        """
        Loads steel plant data.
        Assumes CSV has columns matching SteelPlantSchema fields, potentially requiring pre-processing for nested fields.
        """
        # This is a simplified load. Real CSVs for nested Pydantic models might need more complex parsing
        # or a flatter CSV structure that's then transformed. For example, location_country, location_latitude etc.
        raw_data = self._load_csv_data(file_name)
        plants = []
        for record in raw_data:
            try:
                # Example: if location is flat in CSV as location_country, location_latitude etc.
                # We might need to transform it here before passing to SteelPlantSchema
                # For now, assume the record can be directly unpacked if structured correctly or pre-processed.
                if 'location' in record and isinstance(record['location'], str):
                    # If location is a stringified dict, parse it (not robust, better to have flat columns)
                    import json
                    try: record['location'] = json.loads(record['location'].replace("'", '"'))
                    except: pass # or log error
                
                plants.append(SteelPlantSchema(**record))
            except ValueError as e:
                logger.error(f"Error validating steel plant data: {e} for record {record}")
        return plants

    def load_raw_materials(self, file_name: str = "raw_materials.csv") -> List[RawMaterialSchema]:
        """Loads raw material data."""
        raw_data = self._load_csv_data(file_name)
        materials = []
        for record in raw_data:
            try:
                materials.append(RawMaterialSchema(**record))
            except ValueError as e:
                logger.error(f"Error validating raw material data: {e} for record {record}")
        return materials

    def load_market_data(self, file_name: str = "market_data.csv") -> List[MarketDataPointSchema]:
        """Loads market data time series."""
        raw_data = self._load_csv_data(file_name)
        market_points = []
        for record in raw_data:
            try:
                market_points.append(MarketDataPointSchema(**record))
            except ValueError as e:
                logger.error(f"Error validating market data: {e} for record {record}")
        return market_points

    def load_all_data(self) -> Dict[str, List[Any]]:
        """
        Loads all essential data for the simulation.
        """
        logger.info("Loading all simulation data...")
        all_data = {
            "steel_plants": self.load_steel_plants(),
            "raw_materials": self.load_raw_materials(),
            "market_data": self.load_market_data(),
            # Add other data types here, e.g.:
            # "transportation_routes": self._load_csv_data("transport_routes.csv", TransportationRouteSchema),
            # "carbon_pricing": self._load_csv_data("carbon_pricing.csv", CarbonPricingSchema),
        }
        logger.info("Finished loading all data.")
        return all_data

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Create dummy CSV files for testing
    # You would need to create these files in a 'data/input' subdirectory relative to this script, or adjust path.
    dummy_data_dir = Path(__file__).parent / "dummy_data_for_loader"
    dummy_input_dir = dummy_data_dir / "input"
    dummy_input_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy steel_plants.csv
    plants_df = pd.DataFrame([
        {"plant_id": "P001", "name": "Plant Alpha", "location": '{"country": "USA", "latitude": 40.0}', "production_capacity_tonnes_per_year": 1000000, "current_technology_mix": '{"BF_BOF": 1.0}', "efficiency_factor": 0.9},
        {"plant_id": "P002", "name": "Plant Beta", "location": '{"country": "China", "longitude": 110.0}', "production_capacity_tonnes_per_year": 2000000, "current_technology_mix": '{"EAF": 0.5, "DRI_EAF": 0.5}', "operational_since": "2010-05-15"}
    ])
    plants_df.to_csv(dummy_input_dir / "steel_plants.csv", index=False)

    # Create dummy raw_materials.csv
    materials_df = pd.DataFrame([
        {"material_id": "RM01", "material_type": "IRON_ORE", "available_quantity_tonnes": 50000, "unit_cost_usd_per_tonne": 120},
        {"material_id": "RM02", "material_type": "SCRAP_STEEL", "available_quantity_tonnes": 20000, "unit_cost_usd_per_tonne": 400}
    ])
    materials_df.to_csv(dummy_input_dir / "raw_materials.csv", index=False)

    loader = DataLoader(input_data_dir=dummy_input_dir)
    loaded_plants = loader.load_steel_plants()
    print(f"\nLoaded {len(loaded_plants)} plants:")
    for p in loaded_plants:
        print(p.model_dump_json(indent=2))
    
    loaded_materials = loader.load_raw_materials()
    print(f"\nLoaded {len(loaded_materials)} raw materials:")
    for m in loaded_materials:
        print(m.model_dump_json(indent=2))

    # Clean up dummy files (optional)
    # import shutil
    # shutil.rmtree(dummy_data_dir)
