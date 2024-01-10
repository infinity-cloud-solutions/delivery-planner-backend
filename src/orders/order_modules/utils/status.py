from enum import Enum


class OrderStatus(Enum):
    CREATED = "Creada"
    PROGRAMMED = "Programada"
    ON_TRANSIT = "En ruta"
    RESCHEDULED = "Reprogramar"
    ERROR = "Error"
