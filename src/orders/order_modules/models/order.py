from typing import List

from pydantic import BaseModel
from pydantic import StrictStr
from pydantic import confloat
from pydantic import conint
from pydantic import validator


class HIBerryProduct(BaseModel):
    name: StrictStr
    quantity: conint(ge=0)
    price: confloat(ge=0.0)


class HIBerryOrder(BaseModel):
    client_name: StrictStr
    delivery_date: StrictStr
    delivery_time: StrictStr
    delivery_address: StrictStr
    phone_number: StrictStr
    cart_items: List[HIBerryProduct]
    total_amount: confloat(ge=0.0)
    payment_method: StrictStr

    @validator("total_amount", pre=True, always=True)
    def calculate_total_amount(cls, value, values):
        calculated_total = sum(item.price * item.quantity for item in values.get("cart_items", []))

        if value is not None and calculated_total != value:
            raise ValueError("Provided total_amount does not match the calculated total from cart_items.")

        return calculated_total
