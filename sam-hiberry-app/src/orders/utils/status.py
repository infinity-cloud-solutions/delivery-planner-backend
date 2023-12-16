from enum import Enum


class OrderStatus(Enum):
    CREATE = "Create"
    PROGRAMMED = "Programmed"
    ON_ROUTE = "In Route"
    RESCHEDULE = "Reschedule"
    ERROR = "Error"
