from datetime import datetime, timedelta, timezone
from typing import List

from pydantic import BaseModel, field_validator
from pydantic import StrictStr
from pydantic import StrictInt
from pydantic import StrictFloat
from pydantic import confloat
from pydantic import conint
from pydantic import validator

from order_modules.utils.status import OrderStatus
from order_modules.utils.source import OrderSource


def validate_date_format(date: StrictStr) -> StrictStr:
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return date
    except ValueError:
        raise ValueError(f"delivery_date must be in yyyy-mm-dd format, got {date}")


class Geolocation(BaseModel):
    latitude: StrictFloat
    longitude: StrictFloat


class HIBerryProduct(BaseModel):
    product: StrictStr
    quantity: conint(ge=0)
    price: confloat(ge=0.0)


class DeliveryDateMixin(BaseModel):
    delivery_date: StrictStr

    validate_date = field_validator("delivery_date")(validate_date_format)


class HIBerryOrder(DeliveryDateMixin):
    client_name: StrictStr
    delivery_date: StrictStr
    delivery_time: StrictStr
    delivery_address: StrictStr
    phone_number: StrictStr
    cart_items: List[HIBerryProduct]
    total_amount: confloat(ge=0.0)
    payment_method: StrictStr
    geolocation: Geolocation | None = None
    status: OrderStatus = OrderStatus.CREATED
    source: OrderSource = OrderSource.HIBERRYAPP
    notes: StrictStr | None = None

    @validator("total_amount", pre=True, always=True)
    def calculate_total_amount(cls, value, values):
        calculated_total = sum(
            item.price * item.quantity for item in values.get("cart_items", [])
        )

        if value is not None and calculated_total != value:
            raise ValueError(
                "Provided total_amount does not match the calculated total from cart_items."
            )

        return calculated_total

    @validator("delivery_date")
    def validate_delivery_date_future(cls, value):
        delivery_date = datetime.strptime(value, "%Y-%m-%d")

        # Get the current time in MX Central Time
        current_time = datetime.now(timezone(timedelta(hours=-6)))
        current_datetime = datetime.combine(current_time.date(), datetime.min.time())

        if delivery_date < current_datetime:
            raise ValueError(
                f"delivery_date must be today or in the future in MX Central Time, got {value}"
            )

        return value


class HIBerryOrderUpdate(HIBerryOrder):
    id: StrictStr
    original_date: StrictStr
    delivery_sequence: StrictInt | None = None
    cooler: StrictInt | None = None

    validate_date = field_validator("original_date")(validate_date_format)


class OrderPrimaryKey(DeliveryDateMixin):
    id: StrictStr
