"""
Configuration settings for the SteelPath simulation platform.
Uses Pydantic for data validation and management.
"""
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, FilePath, DirectoryPath
# import yaml # To be used when loading from YAML

logger = logging.getLogger(__name__)

class TimeSettings(BaseModel):
    start_datetime: str = Field(default="2024-01-01T00:00:00", description="Simulation start date and time (ISO format).")
    end_datetime: Optional[str] = Field(default=None, description="Simulation end date and time (ISO format, optional).")
    time_step_days: int = Field(default=1, description="Duration of each simulation step in days.")
    max_simulation_steps: Optional[int] = Field(default=365, description="Maximum number of simulation steps if end_datetime is not provided.")

class DataPaths(BaseModel):
    input_data_dir: Optional[DirectoryPath] = Field(default=None, description="Directory for input data files.")
    output_data_dir: Optional[DirectoryPath] = Field(default="./output_data", description="Directory for simulation output.")
    # Example: plant_data_file: Optional[FilePath] = Field(default=None, description="Path to plant data CSV.")

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR).")
    log_file: Optional[str] = Field(default="simulation.log", description="Path to the log file. If None, logs to console.")

class SimulationParameters(BaseModel):
    simulation_name: str = Field(default="SteelPath_Default_Sim", description="Name of the simulation run.")
    # Add other high-level simulation parameters here
    number_of_plants: int = Field(default=10, description="Example: Number of steel plants to simulate.")

class SimulationConfig(BaseModel):
    """
    Main configuration model for the SteelPath simulation.
    """
    time_settings: TimeSettings = Field(default_factory=TimeSettings)
    data_paths: DataPaths = Field(default_factory=DataPaths)
    logging_config: LoggingConfig = Field(default_factory=LoggingConfig)
    simulation_parameters: SimulationParameters = Field(default_factory=SimulationParameters)
    # Add other specific configuration sections as needed, e.g.:
    # economic_model_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # supply_chain_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        validate_assignment = True # Re-validate on assignment

def load_config(config_file_path: Optional[FilePath] = None) -> SimulationConfig:
    """
    Loads simulation configuration.
    Currently returns a default configuration. 
    Future: Load from a YAML file or other sources.

    Args:
        config_file_path (Optional[FilePath]): Path to the configuration file (e.g., YAML).

    Returns:
        SimulationConfig: The loaded (or default) simulation configuration.
    """
    if config_file_path:
        logger.info(f"Loading configuration from {config_file_path}...")
        # try:
        #     with open(config_file_path, 'r') as f:
        #         config_dict = yaml.safe_load(f)
        #     return SimulationConfig(**config_dict)
        # except FileNotFoundError:
        #     logger.error(f"Configuration file not found: {config_file_path}. Returning default config.")
        #     return SimulationConfig()
        # except yaml.YAMLError as e:
        #     logger.error(f"Error parsing YAML configuration file {config_file_path}: {e}. Returning default config.")
        #     return SimulationConfig()
        # except Exception as e:
        #     logger.error(f"Unexpected error loading config from {config_file_path}: {e}. Returning default config.")
        #     return SimulationConfig()
        # Placeholder until YAML loading is fully implemented
        logger.warning(f"YAML loading from {config_file_path} not yet implemented. Returning default config.")
        return SimulationConfig()
    else:
        logger.info("No configuration file provided. Using default configuration.")
        return SimulationConfig()

# Example of accessing configuration
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Get default config
    default_config = load_config()
    print("Default Configuration:")
    print(f"Simulation Name: {default_config.simulation_parameters.simulation_name}")
    print(f"Start Date: {default_config.time_settings.start_datetime}")
    print(f"Log Level: {default_config.logging_config.level}")
    print(f"Output Dir: {default_config.data_paths.output_data_dir}")

    # Example: Create a config dictionary (e.g., from a loaded YAML)
    custom_settings_dict = {
        "time_settings": {
            "start_datetime": "2025-01-01T00:00:00",
            "max_simulation_steps": 100
        },
        "simulation_parameters": {
            "simulation_name": "Custom_Steel_Run_1"
        },
        "logging_config": {
            "level": "DEBUG"
        }
    }
    custom_config = SimulationConfig(**custom_settings_dict)
    print("\nCustom Configuration:")
    print(f"Simulation Name: {custom_config.simulation_parameters.simulation_name}")
    print(f"Start Date: {custom_config.time_settings.start_datetime}")
    print(f"Log Level: {custom_config.logging_config.level}")
    
    # To load from a file (once implemented):
    # loaded_from_file_config = load_config("path/to/your/config.yaml")
    # print(f"\nLoaded Config Name: {loaded_from_file_config.simulation_parameters.simulation_name}")
