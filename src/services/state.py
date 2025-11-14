from enum import Enum

"""
src/services/state.py

State Machine for Delivery Locker System.

This module defines a simple state machine for managing the states of a delivery locker system.
"""

class State(Enum):
    """
    Enumeration of possible states for the delivery locker system.
    """
    IDLE = 0
    NO_SPACE_AVAILABLE = 1
    COURIER_WAITING = 2
    MAIN_DOOR_OPEN = 3
    DISABLING = 4

class StateMachine:
    """
    State machine for managing the states of the delivery locker system.
    """
    def __init__(self):
        """
        Initialize the state machine to the IDLE state.
        """
        self.state = State.IDLE

    def set_state(self, new_state):
        """
        Set the current state of the state machine.

        Args:
            new_state (State): The new state to set.

        Returns:
            None
        """
        if isinstance(new_state, State):
            self.state = new_state
        else:
            raise ValueError("Invalid state")

    def get_state(self):
        """
        Get the current state of the state machine.

        Returns:
            State: The current state.
        """
        return self.state