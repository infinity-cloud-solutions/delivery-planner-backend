from typing import List
from typing import Dict
from typing import Union

from pydantic import BaseModel
from pydantic import StrictStr
from pydantic import StrictFloat


class HIBerryOrder(BaseModel):
    client_name: StrictStr
    delivery_date: StrictStr
    delivery_time: StrictStr
    delivery_address: StrictStr
    order_items: List[Dict[str, Union[str, int, float]]]
    order_total_amount: StrictFloat
    order_payment_method: StrictStr
