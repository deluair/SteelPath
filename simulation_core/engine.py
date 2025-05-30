"""
Defines the main SimulationEngine for the SteelPath platform.
"""
import logging
import os # Added for path operations
import random # Added for sample data generation
import pandas as pd # Added for data manipulation
import matplotlib.pyplot as plt # Added for plotting
import io # Added for saving plot to buffer
import base64 # Added for embedding plot in HTML
from production_technology.technology_models import BaseTechnologyModel, ProductionTechnologyType
from data_management.schemas import RawMaterialType, SteelProductType
# from .simulation_clock import SimulationClock
# from .event_manager import EventManager
# from ..config.settings import SimulationConfig # Assuming config structure
# from ..data_management.data_loader import DataLoader # Assuming data loader

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Orchestrates the steel industry simulation, managing agents, time, and events.
    """
    def __init__(self, config):
        """
        Initializes the simulation engine.

        Args:
            config (SimulationConfig): The simulation configuration object.
        """
        self.config = config
        # self.clock = SimulationClock(start_date=config.start_date, time_step=config.time_step)
        # self.event_manager = EventManager()
        # self.data_loader = DataLoader(config.data_paths)
        self.agents = []
        self.results = []
        
        # Initialize steel plant simulation parameters
        self.plant_capacity_tpa = 2000000  # 2 million tonnes per annum
        self.technology_mix = {
            ProductionTechnologyType.BF_BOF: 0.6,
            ProductionTechnologyType.EAF: 0.3,
            ProductionTechnologyType.DRI_EAF: 0.1
        }
        
        # Load technology models
        self.tech_models = {}
        for tech_type in self.technology_mix.keys():
            self.tech_models[tech_type] = BaseTechnologyModel.get_model_for_technology(tech_type)
        
        # Market conditions
        self.base_steel_price = 650  # USD per tonne
        self.price_volatility = 0.15  # 15% volatility
        
        # Raw material prices (USD per tonne)
        self.raw_material_prices = {
            RawMaterialType.IRON_ORE: 120,
            RawMaterialType.COKING_COAL: 280,
            RawMaterialType.SCRAP_STEEL: 450,
            RawMaterialType.NATURAL_GAS: 8,  # USD per MMBtu, converted to tonne equivalent
            RawMaterialType.HYDROGEN: 3500,  # USD per tonne (expensive green hydrogen)
            RawMaterialType.LIMESTONE: 25,
            RawMaterialType.ALLOYS: 1200
        }
        
        # Energy prices
        self.electricity_price_usd_per_mwh = 80
        
        logger.info("SimulationEngine initialized with realistic steel industry parameters.")

    def _initialize_agents(self):
        """
        Loads and initializes all agents (plants, suppliers, markets, etc.).
        """
        # Placeholder: Load agent configurations from data or config
        # Example: self.agents.append(SteelPlantAgent(...))
        logger.info("Initializing agents...")
        # For now, let's assume a simple agent list is populated elsewhere or via config
        pass

    def _setup_simulation(self):
        """
        Sets up the initial state of the simulation.
        """
        logger.info("Setting up simulation environment...")
        self._initialize_agents()
        # Potentially load market data, initial inventories, etc.
        pass

    def run_step(self, current_step):
        """
        Runs a single step of the simulation.

        Args:
            current_step (int): The current simulation step number.
        """
        # self.clock.tick()
        # current_time = self.clock.get_current_time()
        # logger.info(f"Running simulation step for time: {current_time}")

        # self.event_manager.process_events(current_time)

        for agent in self.agents:
            # agent.step(current_time, self.event_manager)
            pass

        # Collect data for this step
        step_data = self._collect_step_data(current_step)
        self.results.append(step_data)
        pass

    def run_simulation(self):
        """
        Runs the full simulation from start to finish.
        """
        self._setup_simulation()
        logger.info("Starting simulation run...")

        # num_steps = self.config.get('simulation_settings', {}).get('duration_steps', 100) # Example
        # for step in range(num_steps):
        #     if self.clock.is_finished(num_steps): # Or based on end_date
        #         break
        #     self.run_step()
        #     if (step + 1) % 10 == 0: # Log progress
        #         logger.info(f"Completed step {step + 1}/{num_steps}")
        
        # Placeholder for loop
        for i in range(self.config.get('simulation_parameters', {}).get('number_of_steps', 10)):
            logger.info(f"Executing step {i+1}")
            self.run_step(current_step=i + 1) # Pass the actual current step

        logger.info("Simulation run completed.")
        return self._finalize_results()

    def _collect_step_data(self, current_time_or_step):
        """
        Collects relevant data from agents and the environment at the current step.
        Now uses realistic steel industry data based on technology models.
        """
        logger.info(f"Collecting data for step/time: {current_time_or_step}")
        
        # Calculate daily production (assuming 350 operating days per year)
        daily_capacity = self.plant_capacity_tpa / 350
        
        # Simulate capacity utilization (80-95%)
        capacity_utilization = random.uniform(0.80, 0.95)
        daily_production = daily_capacity * capacity_utilization
        
        # Calculate weighted averages based on technology mix
        total_co2_emissions = 0
        total_energy_consumption = 0
        total_raw_material_cost = 0
        
        for tech_type, share in self.technology_mix.items():
            tech_model = self.tech_models[tech_type]
            production_by_tech = daily_production * share
            
            # CO2 emissions
            co2_by_tech = production_by_tech * tech_model.co2_emissions_tonne_per_tonne_steel
            total_co2_emissions += co2_by_tech
            
            # Energy consumption
            energy_by_tech = production_by_tech * tech_model.energy_consumption_mwh_per_tonne_steel
            total_energy_consumption += energy_by_tech
            
            # Raw material costs
            for material, consumption_per_tonne in tech_model.raw_material_input_per_tonne_steel.items():
                material_cost = production_by_tech * consumption_per_tonne * self.raw_material_prices[material]
                total_raw_material_cost += material_cost
        
        # Calculate energy costs
        energy_cost = total_energy_consumption * self.electricity_price_usd_per_mwh
        
        # Market price with volatility
        market_price = self.base_steel_price * (1 + random.uniform(-self.price_volatility, self.price_volatility))
        
        # Calculate profit margin
        revenue = daily_production * market_price
        variable_costs = total_raw_material_cost + energy_cost
        gross_profit = revenue - variable_costs
        profit_margin = (gross_profit / revenue) * 100 if revenue > 0 else 0
        
        # Simulate market demand fluctuation
        demand_factor = random.uniform(0.85, 1.15)  # ±15% demand variation
        market_demand = daily_capacity * demand_factor
        
        return {
            "step": current_time_or_step,
            "production_volume_tonnes": round(daily_production, 1),
            "capacity_utilization_percent": round(capacity_utilization * 100, 1),
            "co2_emissions_tonnes": round(total_co2_emissions, 2),
            "co2_intensity_kg_per_tonne": round((total_co2_emissions / daily_production) * 1000, 1),
            "energy_consumption_mwh": round(total_energy_consumption, 1),
            "energy_intensity_mwh_per_tonne": round(total_energy_consumption / daily_production, 2),
            "market_price_usd_per_tonne": round(market_price, 2),
            "raw_material_cost_usd": round(total_raw_material_cost, 2),
            "energy_cost_usd": round(energy_cost, 2),
            "revenue_usd": round(revenue, 2),
            "profit_margin_percent": round(profit_margin, 1),
            "market_demand_tonnes": round(market_demand, 1),
            "supply_demand_ratio": round(daily_production / market_demand, 3)
        }

    def _finalize_results(self):
        """
        Processes and returns the final simulation results.
        """
        logger.info("Finalizing simulation results.")
        # Potentially aggregate, summarize, or save results
        return self.results

    def load_initial_data(self):
        """
        Loads all necessary initial data for the simulation.
        This could include plant specifications, raw material prices, demand forecasts, etc.
        """
        logger.info("Loading initial simulation data...")
        # initial_data = self.data_loader.load_all()
        # Process and structure this data as needed by the engine and agents
        # Example: self.market_conditions = initial_data.get('market_data')
        # return initial_data
        return {"plants": [], "market_data": {}}

    def generate_reports(self, results):
        """
        Generates reports from the simulation results.
        Now includes comprehensive steel industry analysis with multiple plots and detailed summary.
        """
        logger.info("Generating reports...")
        
        if not results:
            logger.info("No results to report.")
            html_content = "<html><head><title>SteelPath Simulation Report</title></head><body>"
            html_content += "<h1>SteelPath Simulation Results</h1>"
            html_content += "<p>No results to report.</p>"
            html_content += "</body></html>"
        else:
            logger.info(f"Collected {len(results)} data points.")
            df = pd.DataFrame(results)

            # --- Executive Summary ---
            total_production = df['production_volume_tonnes'].sum()
            avg_capacity_util = df['capacity_utilization_percent'].mean()
            total_co2 = df['co2_emissions_tonnes'].sum()
            avg_co2_intensity = df['co2_intensity_kg_per_tonne'].mean()
            avg_energy_intensity = df['energy_intensity_mwh_per_tonne'].mean()
            avg_profit_margin = df['profit_margin_percent'].mean()
            total_revenue = df['revenue_usd'].sum()
            
            summary_stats = "<h2>Executive Summary</h2>"
            summary_stats += "<div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;'>"
            summary_stats += "<h3>Production Performance</h3>"
            summary_stats += "<ul>"
            summary_stats += f"<li><strong>Total Production:</strong> {total_production:,.0f} tonnes over {len(results)} days</li>"
            summary_stats += f"<li><strong>Average Capacity Utilization:</strong> {avg_capacity_util:.1f}%</li>"
            summary_stats += f"<li><strong>Daily Average Production:</strong> {total_production/len(results):,.0f} tonnes/day</li>"
            summary_stats += "</ul>"
            
            summary_stats += "<h3>Environmental Impact</h3>"
            summary_stats += "<ul>"
            summary_stats += f"<li><strong>Total CO2 Emissions:</strong> {total_co2:,.0f} tonnes</li>"
            summary_stats += f"<li><strong>Average CO2 Intensity:</strong> {avg_co2_intensity:.0f} kg CO2/tonne steel</li>"
            summary_stats += f"<li><strong>Average Energy Intensity:</strong> {avg_energy_intensity:.2f} MWh/tonne steel</li>"
            summary_stats += "</ul>"
            
            summary_stats += "<h3>Financial Performance</h3>"
            summary_stats += "<ul>"
            summary_stats += f"<li><strong>Total Revenue:</strong> ${total_revenue:,.0f}</li>"
            summary_stats += f"<li><strong>Average Profit Margin:</strong> {avg_profit_margin:.1f}%</li>"
            summary_stats += f"<li><strong>Average Steel Price:</strong> ${df['market_price_usd_per_tonne'].mean():.2f}/tonne</li>"
            summary_stats += "</ul>"
            summary_stats += "</div>"

            # --- Generate Multiple Plots ---
            plots_html = ""
            
            # Plot 1: Production Volume and Capacity Utilization
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            ax1.plot(df['step'], df['production_volume_tonnes'], marker='o', linestyle='-', color='steelblue')
            ax1.set_title('Daily Steel Production Volume')
            ax1.set_xlabel('Day')
            ax1.set_ylabel('Production (tonnes)')
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(df['step'], df['capacity_utilization_percent'], marker='s', linestyle='-', color='orange')
            ax2.set_title('Capacity Utilization')
            ax2.set_xlabel('Day')
            ax2.set_ylabel('Utilization (%)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64_1 = base64.b64encode(img_buffer.read()).decode('utf-8')
            plt.close()
            
            plots_html += f"<h2>Production Analysis</h2><img src='data:image/png;base64,{img_base64_1}' alt='Production Analysis' style='max-width: 100%; margin: 10px 0;'>"
            
            # Plot 2: Environmental Metrics
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            ax1.plot(df['step'], df['co2_emissions_tonnes'], marker='o', linestyle='-', color='red')
            ax1.set_title('Daily CO2 Emissions')
            ax1.set_xlabel('Day')
            ax1.set_ylabel('CO2 Emissions (tonnes)')
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(df['step'], df['co2_intensity_kg_per_tonne'], marker='s', linestyle='-', color='darkred')
            ax2.set_title('CO2 Intensity')
            ax2.set_xlabel('Day')
            ax2.set_ylabel('CO2 Intensity (kg/tonne steel)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64_2 = base64.b64encode(img_buffer.read()).decode('utf-8')
            plt.close()
            
            plots_html += f"<h2>Environmental Impact Analysis</h2><img src='data:image/png;base64,{img_base64_2}' alt='Environmental Analysis' style='max-width: 100%; margin: 10px 0;'>"
            
            # Plot 3: Financial Performance
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            ax1.plot(df['step'], df['market_price_usd_per_tonne'], marker='o', linestyle='-', color='green')
            ax1.set_title('Steel Market Price')
            ax1.set_xlabel('Day')
            ax1.set_ylabel('Price (USD/tonne)')
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(df['step'], df['profit_margin_percent'], marker='s', linestyle='-', color='darkgreen')
            ax2.set_title('Profit Margin')
            ax2.set_xlabel('Day')
            ax2.set_ylabel('Profit Margin (%)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64_3 = base64.b64encode(img_buffer.read()).decode('utf-8')
            plt.close()
            
            plots_html += f"<h2>Financial Performance Analysis</h2><img src='data:image/png;base64,{img_base64_3}' alt='Financial Analysis' style='max-width: 100%; margin: 10px 0;'>"

            # --- Technology Mix Information ---
            tech_info = "<h2>Technology Mix</h2>"
            tech_info += "<div style='background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0;'>"
            tech_info += "<p>This simulation models a steel plant with the following technology mix:</p>"
            tech_info += "<ul>"
            for tech_type, share in self.technology_mix.items():
                tech_model = self.tech_models[tech_type]
                tech_info += f"<li><strong>{tech_type.value}:</strong> {share*100:.0f}% of production"
                tech_info += f" (CO2 intensity: {tech_model.co2_emissions_tonne_per_tonne_steel:.1f} t/t steel)</li>"
            tech_info += "</ul>"
            tech_info += "</div>"

            # --- Data Table ---
            data_table_html = "<h2>Detailed Daily Data</h2>"
            data_table_html += "<div style='overflow-x: auto;'>"
            data_table_html += df.to_html(index=False, border=1, classes='table table-striped', float_format='{:.2f}'.format)
            data_table_html += "</div>"

            # --- Assemble HTML Content ---
            html_content = "<html><head><title>SteelPath Simulation Report</title>"
            html_content += "<style>"
            html_content += "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }"
            html_content += "h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }"
            html_content += "h2 { color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 15px; }"
            html_content += "h3 { color: #2c3e50; margin-top: 20px; }"
            html_content += "table { border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 0.9em; }"
            html_content += "th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }"
            html_content += "th { background-color: #3498db; color: white; font-weight: bold; }"
            html_content += "tr:nth-child(even) { background-color: #f8f9fa; }"
            html_content += "img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }"
            html_content += "ul { margin-left: 20px; }"
            html_content += "li { margin: 5px 0; }"
            html_content += ".highlight { background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }"
            html_content += "</style></head><body>"
            html_content += "<h1>🏭 SteelPath Simulation Report</h1>"
            html_content += f"<p><em>Simulation Period: {len(results)} days | Plant Capacity: {self.plant_capacity_tpa:,} tonnes/year</em></p>"
            html_content += summary_stats
            html_content += tech_info
            html_content += plots_html
            html_content += data_table_html
            html_content += "<hr><p style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>Generated by SteelPath Simulation Platform</p>"
            html_content += "</body></html>"

        # --- Save HTML Report ---
        report_filename = "simulation_report.html"
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        if not os.path.exists(reports_dir):
            try:
                os.makedirs(reports_dir)
            except OSError as e:
                logger.error(f"Error creating reports directory {reports_dir}: {e}")
                reports_dir = "."
        
        report_file_path = os.path.join(reports_dir, report_filename)

        try:
            with open(report_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report generated: {os.path.abspath(report_file_path)}")
            print(f"HTML report generated: {os.path.abspath(report_file_path)}")
        except IOError as e:
            logger.error(f"Error writing HTML report to {report_file_path}: {e}")
            print(f"Error writing HTML report to {report_file_path}: {e}")
        pass

if __name__ == '__main__':
    # Example usage (requires config setup)
    logging.basicConfig(level=logging.INFO)
    mock_config = {
        "simulation_parameters": {"number_of_steps": 5},
        "start_date": "2023-01-01",
        "time_step": {"days": 1}
    }
    engine = SimulationEngine(config=mock_config)
    results = engine.run_simulation()
    print(f"Simulation finished. Results count: {len(results)}")
