from typing import List
from datetime import datetime

from pydantic import StrictStr
from pydantic import StrictInt
from pydantic import BaseModel
from pydantic import field_validator


def validate_date_format(date: StrictStr) -> StrictStr:
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return date
    except ValueError:
        raise ValueError(f"date must be in yyyy-mm-dd format, got {date}")


class ScheduleRequestModel(BaseModel):
    date: StrictStr
    available_drivers: List[int]

    validate_date = field_validator("date")(validate_date_format)


class OrderModel(BaseModel):
    id: StrictStr
    delivery_date: StrictStr
    delivery_sequence: StrictInt
    driver: StrictInt
    status: StrictStr


class UpdateScheduleRequestModel(BaseModel):
    orders: List[OrderModel]
