"""
Defines the EventManager for handling discrete events in the simulation.
"""
import heapq
import logging

logger = logging.getLogger(__name__)

class Event:
    """
    Represents a discrete event in the simulation.
    """
    def __init__(self, time, target_agent_id, event_type, data=None):
        self.time = time  # Simulation time at which the event occurs
        self.target_agent_id = target_agent_id # ID of the agent to process this event
        self.event_type = event_type # Type of event (e.g., 'MATERIAL_ARRIVAL', 'PRICE_CHANGE')
        self.data = data if data is not None else {} # Optional data payload

    def __lt__(self, other):
        # heapq is a min-heap, so compare by time
        return self.time < other.time

    def __repr__(self):
        return f"Event(Time: {self.time}, Target: {self.target_agent_id}, Type: {self.event_type}, Data: {self.data})"

class EventManager:
    """
    Manages a queue of events and processes them at the appropriate simulation time.
    """
    def __init__(self):
        self.event_queue = []  # A min-heap (priority queue) of (time, event_object)
        logger.info("EventManager initialized.")

    def schedule_event(self, event_time, target_agent_id, event_type, data=None):
        """
        Schedules a new event.

        Args:
            event_time: The simulation time for the event.
            target_agent_id: The ID of the agent that should handle this event.
            event_type (str): A string identifying the type of event.
            data (dict, optional): Additional data associated with the event.
        """
        new_event = Event(event_time, target_agent_id, event_type, data)
        heapq.heappush(self.event_queue, new_event)
        logger.debug(f"Scheduled: {new_event}")

    def get_next_event_time(self):
        """
        Returns the time of the next scheduled event, or None if queue is empty.
        """
        if not self.event_queue:
            return None
        return self.event_queue[0].time

    def process_events(self, current_time, agents_map):
        """
        Processes all events scheduled up to the current_time.

        Args:
            current_time: The current simulation time.
            agents_map (dict): A dictionary mapping agent_id to agent objects.
                               This is used to deliver events to the target agent.
        """
        processed_events = []
        while self.event_queue and self.event_queue[0].time <= current_time:
            event = heapq.heappop(self.event_queue)
            logger.debug(f"Processing: {event}")
            
            target_agent = agents_map.get(event.target_agent_id)
            if target_agent:
                if hasattr(target_agent, 'handle_event'):
                    target_agent.handle_event(event)
                else:
                    logger.warning(f"Agent {event.target_agent_id} has no handle_event method for {event.event_type}")
            else:
                logger.warning(f"Target agent {event.target_agent_id} not found for event {event.event_type}")
            processed_events.append(event)
        return processed_events

    def clear_events(self):
        """
        Clears all events from the queue.
        """
        self.event_queue = []
        logger.info("All events cleared from EventManager.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    manager = EventManager()
    manager.schedule_event(10, "plant_A", "RAW_MATERIAL_DELIVERY", {"material": "iron_ore", "quantity": 1000})
    manager.schedule_event(5, "market_B", "PRICE_UPDATE", {"product": "steel_coil", "price": 750})
    manager.schedule_event(10, "plant_C", "MAINTENANCE_START")

    print(f"Next event time: {manager.get_next_event_time()}")

    # Mock agents for processing
    class MockAgent:
        def __init__(self, id):
            self.id = id
        def handle_event(self, event):
            print(f"Agent {self.id} handling {event}")
    
    agents = {"plant_A": MockAgent("plant_A"), "market_B": MockAgent("market_B"), "plant_C": MockAgent("plant_C")}

    print("\nProcessing events at time 5:")
    manager.process_events(5, agents)
    print(f"\nNext event time: {manager.get_next_event_time()}")

    print("\nProcessing events at time 10:")
    manager.process_events(10, agents)
    print(f"\nNext event time: {manager.get_next_event_time()}")
