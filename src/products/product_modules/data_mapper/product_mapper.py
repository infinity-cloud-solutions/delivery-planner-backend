# Python's libraries
import uuid
from typing import Dict
from typing import Any
from datetime import datetime


class ProductHelper():

    def build_product(
        self,
        product_data: Dict[str, Any],
        username: str,
    ) -> Dict[str, Any]:
        """This function will create a dictionary to send to DynamoDB to create a new record

        Arguments:
            order_data -- Processed clients input
            username -- who is sending the request

        Returns:
            Object needed by DynamoDB to create a record
        """
        id = product_data.get("id", None)
        if id is None:
            id = str(uuid.uuid4())

        data = {
            "id": id,
            "name": product_data["name"],
            "price": product_data["price"],
            "created_by": username,
            "created_at": datetime.now().isoformat(),
        }
        return data
