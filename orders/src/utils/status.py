from enum import Enum


class OrderStatus(Enum):
    CREATE = "Create"
    PROGRAMMED = "Programmed"
    ON_TRANSIT = "On Transit"
    RESCHEDULE = "Reschedule"
    ERROR = "Error"
