from enum import Enum


class OrderStatus(Enum):
    CREATED = "Creada"
    PROGRAMMED = "Programada"
    ON_TRANSIT = "En ruta"
    RESCHEDULED = "Reprogramada"
    ERROR = "Error"
    DELIVERED = "Entregada"
