# Python's libraries
import uuid
from typing import Dict
from typing import Any
from typing import List
from datetime import datetime

# Own's modules
from src.utils.status import OrderStatus


class OrderHelper():

    def build_order(
        self,
        order_data: Dict[str, Any],
        username: str,
        geolocation: Dict[str, float],
        errors: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """This function will create a dictionary to send to DynamoDB to create a new record

        Arguments:
            order_data -- Processed clients input
            username -- who is sending the request
            geolocation -- Lat and Long

        Returns:
            Object needed by DynamoDB to create a record
        """

        items = [item.__dict__ for item in order_data.get("cart_items", [])]
        data = {
            "id": str(uuid.uuid4()),
            "client_name": order_data.get("client_name"),
            "delivery_date": order_data.get("delivery_date"),
            "delivery_time": order_data.get("delivery_time"),
            "address": order_data.get("delivery_address"),
            "latitude": float(geolocation.get("latitude", 0)),
            "longitude": float(geolocation.get("longitude", 0)),
            "phone_number": order_data.get("phone_number"),
            "cart_items": items,
            "total_amount": float(order_data.get("total_amount", 0)),
            "payment_method": order_data.get("payment_method"),
            "created_by": username,
            "created_at": datetime.now().isoformat(),
            "updated_by": None,
            "updated_at": None,
            "errors": order_data.get("errors", []),
            "notes": None,
            "status": OrderStatus.CREATE.value,
            "delivery_sequence": None
        }
        return data
