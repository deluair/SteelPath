# SteelPath: Integrated Economic-Environmental Optimization for Global Steel Manufacturing

This project aims to develop a sophisticated Python-based simulation platform addressing the steel industry's challenges: carbon emissions, technological transformation, and supply chain dynamics.

## Project Overview

SteelPath is a simulation tool designed to model and optimize the global steel manufacturing landscape. It considers economic factors, environmental impacts (particularly carbon emissions), technological advancements, and complex supply chain interactions. The goal is to provide insights and decision-support for navigating the transition towards a more sustainable and efficient steel industry.

See `docs/project_overview.md` for a more in-depth conceptual overview (once populated).

## Project Structure

The project is organized into the following main directories:

- `config/`: Contains configuration files for the simulation, including simulation parameters, time settings, and data paths.
- `data_management/`: Handles data loading, validation (schemas), and generation of synthetic data if needed.
- `docs/`: Project documentation, including overviews and detailed explanations.
- `economic_financial_modeling/`: Modules for cost analysis, financial modeling, investment decisions, and market dynamics.
- `environmental_impact/`: Models for calculating environmental impacts, primarily CO2 emissions.
- `main.py`: The main entry point to run the simulation.
- `notebooks/`: Jupyter notebooks for analysis, experimentation, and visualization.
- `optimization_engine/`: Core logic for optimization algorithms (if applicable).
- `production_technology/`: Models for different steel production technologies (e.g., BF-BOF, EAF, DRI).
- `requirements.txt`: A list of Python package dependencies for the project.
- `scenario_analysis/`: Tools and scripts for defining and running different simulation scenarios.
- `simulation_core/`: The heart of the simulation, including the simulation engine, base agent definitions, event manager, and simulation clock.
- `supply_chain_logistics/`: Models for inventory management, sourcing strategies, and transportation.
- `tests/`: Unit and integration tests for the codebase.
- `utils/`: Utility functions, helper scripts, and logging configurations.

## Getting Started

### Prerequisites

- Python 3.8+ (refer to `requirements.txt` for specific package versions)
- Git (for version control)

### Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd SteelPath/steel_path_simulation
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Simulation

To run the default simulation, execute the main script from the `steel_path_simulation` directory:

```bash
python main.py
```

This will initialize the simulation based on the default configurations. You can modify `config/config.yaml` (or create one from `config.yaml.example`) to customize simulation parameters.

## Contributing

(Details on how to contribute will be added here - e.g., coding standards, pull request process).

## License

(License information will be added here - e.g., MIT, Apache 2.0).
