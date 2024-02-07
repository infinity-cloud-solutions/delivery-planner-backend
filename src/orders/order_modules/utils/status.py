from enum import Enum


class OrderStatus(Enum):
    CREATED = "Creada"
    PROGRAMMED = "ReProgramada"
    ON_TRANSIT = "En ruta"
    RESCHEDULED = "Reprogramar"
    ERROR = "Error"
    DELIVER = "Entregada"
    