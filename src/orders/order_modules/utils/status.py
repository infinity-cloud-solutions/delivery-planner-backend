from enum import Enum


class OrderStatus(Enum):
    CREATED = "Created"
    PROGRAMMED = "Programmed"
    ON_TRANSIT = "On Transit"
    RESCHEDULED = "Rescheduled"
    ERROR = "Error"
