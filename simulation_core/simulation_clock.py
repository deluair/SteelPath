"""
Defines the SimulationClock for managing time in the SteelPath simulation.
"""
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SimulationClock:
    """
    Manages simulation time, including current time and time steps.
    """
    def __init__(self, start_datetime_str, time_step_delta, end_datetime_str=None):
        """
        Initializes the simulation clock.

        Args:
            start_datetime_str (str): The starting date and time of the simulation (e.g., "YYYY-MM-DD HH:MM:SS").
            time_step_delta (timedelta): The duration of each simulation step.
            end_datetime_str (str, optional): The end date and time of the simulation. If None, simulation runs for a number of steps.
        """
        try:
            self.current_time = datetime.fromisoformat(start_datetime_str)
        except ValueError:
            logger.error(f"Invalid start_datetime_str format: {start_datetime_str}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.")
            raise
        
        if not isinstance(time_step_delta, timedelta):
            logger.error(f"time_step_delta must be a timedelta object, got {type(time_step_delta)}")
            raise TypeError("time_step_delta must be a timedelta object.")
            
        self.time_step_delta = time_step_delta
        self.start_time = self.current_time
        self.step_count = 0

        self.end_time = None
        if end_datetime_str:
            try:
                self.end_time = datetime.fromisoformat(end_datetime_str)
                if self.end_time <= self.start_time:
                    logger.error(f"End time {self.end_time} must be after start time {self.start_time}.")
                    raise ValueError("End time must be after start time.")
            except ValueError:
                logger.error(f"Invalid end_datetime_str format: {end_datetime_str}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.")
                raise
        
        logger.info(f"SimulationClock initialized. Start: {self.start_time}, Step: {self.time_step_delta}, End: {self.end_time if self.end_time else 'N/A'}")

    def tick(self):
        """
        Advances the simulation time by one time step.
        """
        self.current_time += self.time_step_delta
        self.step_count += 1
        logger.debug(f"Clock ticked. New time: {self.current_time}, Step: {self.step_count}")

    def get_current_time(self):
        """
        Returns the current simulation time as a datetime object.
        """
        return self.current_time

    def get_current_step(self):
        """
        Returns the current step number (0-indexed for the first step before any tick).
        """
        return self.step_count

    def is_finished(self, max_steps=None):
        """
        Checks if the simulation should end based on end_time or max_steps.

        Args:
            max_steps (int, optional): Maximum number of steps to run if end_time is not set.

        Returns:
            bool: True if the simulation should end, False otherwise.
        """
        if self.end_time and self.current_time >= self.end_time:
            logger.info(f"Simulation end time {self.end_time} reached or exceeded.")
            return True
        if max_steps is not None and self.step_count >= max_steps:
            logger.info(f"Maximum steps {max_steps} reached.")
            return True
        return False

    def reset(self):
        """
        Resets the clock to its initial state.
        """
        self.current_time = self.start_time
        self.step_count = 0
        logger.info("SimulationClock reset to start time.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # Example 1: Simulation with end date
    clock1 = SimulationClock(
        start_datetime_str="2024-01-01 00:00:00", 
        time_step_delta=timedelta(days=1),
        end_datetime_str="2024-01-05 00:00:00"
    )
    print(f"Initial time (Clock 1): {clock1.get_current_time()}, Step: {clock1.get_current_step()}")
    while not clock1.is_finished():
        clock1.tick()
        print(f"Time (Clock 1): {clock1.get_current_time()}, Step: {clock1.get_current_step()}")
    print("Clock 1 finished.")

    # Example 2: Simulation with max steps
    clock2 = SimulationClock(
        start_datetime_str="2024-01-01", 
        time_step_delta=timedelta(hours=12)
    )
    print(f"\nInitial time (Clock 2): {clock2.get_current_time()}, Step: {clock2.get_current_step()}")
    max_s = 5
    while not clock2.is_finished(max_steps=max_s):
        clock2.tick()
        print(f"Time (Clock 2): {clock2.get_current_time()}, Step: {clock2.get_current_step()}")
    print("Clock 2 finished.")

    clock2.reset()
    print(f"After reset (Clock 2): {clock2.get_current_time()}, Step: {clock2.get_current_step()}")
