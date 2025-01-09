from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import uuid


class EventType(Enum):
    """Event types for a trading system."""
    MARKET = "MARKET"
    ORDER = "ORDER"
    SIGNAL = "SIGNAL"
    ERROR = "ERROR"


class Event(ABC):
    """
    Abstract base class for a trading system event.

    Attributes:
        __event_id (str): Unique event ID.
        __event_type (EventType): Type of event.
        __priority (int): Event priority.
        __created_at (datetime): Event creation time.
        __metadata (dict): Optional metadata.
    """

    def __init__(
            self,
            event_id: str,
            event_type: EventType,
            priority: int,
            created_at: datetime,
            metadata: dict = None
    ):
        """
        Initialize the event.

        Args:
            created_at (datetime): Event creation time.
            event_id (str): Unique event ID.
            priority (int): Event priority.
            event_type (EventType): Type of event.
            metadata (dict, optional): Additional data.
        """
        self.__created_at = datetime.now()
        self.__event_id = str(uuid.uuid4())
        self.__priority = priority
        self.__event_type = event_type
        self.__metadata = metadata or {}

    def get_created_at(self) -> datetime:
        """Return the event creation time."""
        return self.__created_at

    def get_event_id(self) -> str:
        """Return the unique event ID."""
        return self.__event_id

    def get_priority(self) -> int:
        """Return the event priority."""
        return self.__priority

    def get_event_type(self) -> EventType:
        """Return the event type."""
        return self.__event_type

    def get_metadata(self) -> dict:
        """Return the metadata dictionary."""
        return self.__metadata

    @abstractmethod
    def process(self):
        """Process the event (must be overridden)."""
        pass
