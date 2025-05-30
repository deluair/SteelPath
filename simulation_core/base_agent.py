"""
Defines the BaseAgent class for all agents in the SteelPath simulation.
"""
import uuid
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for all agents participating in the simulation.
    Agents can represent steel plants, suppliers, consumers, markets, etc.
    """
    def __init__(self, agent_id=None, agent_type="BaseAgent"):
        """
        Initializes a new agent.

        Args:
            agent_id (str, optional): A unique identifier for the agent. 
                                      If None, a UUID will be generated.
            agent_type (str, optional): The type of the agent.
        """
        self.agent_id = agent_id if agent_id else str(uuid.uuid4())
        self.agent_type = agent_type
        # self.simulation_clock = None # Will be set by the engine
        # self.event_manager = None # Will be set by the engine
        logger.debug(f"{self.agent_type} '{self.agent_id}' created.")

    def setup(self, simulation_clock, event_manager):
        """
        Called by the simulation engine to provide access to core components.
        """
        # self.simulation_clock = simulation_clock
        # self.event_manager = event_manager
        pass

    def step(self, current_time):
        """
        Represents a single time step action for the agent.
        This method should be overridden by subclasses to define specific behaviors.

        Args:
            current_time: The current simulation time, provided by the SimulationClock.
        """
        logger.debug(f"{self.agent_type} '{self.agent_id}' stepping at time {current_time}.")
        # Abstract method - to be implemented by subclasses
        pass

    def get_status(self):
        """
        Returns the current status or state of the agent.
        This can be used for data collection and reporting.
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "current_status": "nominal"
        }

    def __repr__(self):
        return f"<{self.agent_type} (ID: {self.agent_id})>"
