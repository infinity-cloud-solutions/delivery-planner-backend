
from typing import Union
from pydantic import BaseModel, StrictStr


class ShopifyNoteAttribute(BaseModel):
    name: StrictStr
    value: StrictStr


class ShopifyAddress(BaseModel):
    address1: Union[StrictStr, None] = None
    phone: Union[StrictStr, None] = None
    latitude: Union[float, None] = None
    longitude: Union[float, None] = None


class ShopifyCustomer(BaseModel):
    first_name: StrictStr
    last_name: StrictStr


class ShopifyLineItem(BaseModel):
    name: StrictStr
    price: float
    quantity: int


class ShopifyOrder(BaseModel):
    customer: ShopifyCustomer
    billing_address: Union[ShopifyAddress, None] = None
    shipping_address: Union[ShopifyAddress, None] = None
    line_items: list[ShopifyLineItem]
    current_subtotal_price: float
    note: Union[StrictStr, None] = None
    payment_gateway_names: Union[list[StrictStr], None] = []
    note_attributes: Union[list[ShopifyNoteAttribute], None] = []

    def line_items_to_dict(self) -> list[dict]:
        """
        Converts the line_items field to a list of dictionaries.

        Returns:
        list[dict]: A list of dictionaries representing each line item.
        """
        return [item.dict() for item in self.line_items]


class ShopifyPayload(BaseModel):
    payload: ShopifyOrder
