# Python's libraries
import uuid
from typing import Dict
from typing import Any
from typing import List
from datetime import datetime

# Own's modules
from order_modules.utils.status import OrderStatus
from order_modules.dao.order_dao import OrderDAO
from order_modules.data_access.geolocation_handler import Geolocation
from order_modules.utils.delivery import DeliveryScheduler
from order_modules.errors.business_error import BusinessError

from settings import ORDERS_PRIMARY_KEY

# Third-party libraries
from aws_lambda_powertools import Logger


class OrderHelper():
    def __init__(
        self,
        order_data: Dict[str, Any],
        location_service: Geolocation = None
    ):
        self.order_data = order_data
        self.logger = Logger()
        self.location_service = location_service or Geolocation()

    def fetch_geolocation(self) -> Dict[str, float]:
        """
        Fetches geolocation data based on the order data's delivery address.

        :return: A dictionary with latitude and longitude
        :rtype: Dict[str, float]
        """
        geolocation_data = self.order_data.get("geolocation", None)
        if geolocation_data is not None and hasattr(geolocation_data, '_dict_'):
             geolocation = geolocation_data._dict_
        else:
            geolocation = {}        
        if geolocation is None:
            self.logger.info(
                "Input did not include geolocation data, invoking Geolocation Service")
            geolocation = self.location_service.get_lat_and_long_from_street_address(
                str_address=self.order_data.get("delivery_address")
            )
            return geolocation
        else:
            self.logger.info("Using provided geolocation data from input")
            return geolocation

    def get_available_driver(self,
                             geolocation: Dict[str, float],
                             delivery_time: str,
                             delivery_date: str):

        customer_location = (geolocation.get("latitude"),
                             geolocation.get("longitude"))

        if delivery_date is None:
            delivery_date = self.order_data.get(
                "delivery_date", datetime.now().strftime("%Y-%m-%d"))

        dao = OrderDAO()
        orders = dao.fetch_orders(
            primary_key=ORDERS_PRIMARY_KEY,
            query_value=delivery_date
        )
        orders = orders["payload"]

        planner = DeliveryScheduler()
        driver = planner.assign_driver_for_delivery(
            customer_location=customer_location,
            delivery_time=delivery_time,
            order_date=delivery_date,
            orders=orders
        )
        if driver:
            return driver
        else:
            raise BusinessError("No drivers available")

    def build_order(
        self,
        username: str,
        uid: str = None
    ) -> Dict[str, Any]:
        """This function will create a dictionary to send to DynamoDB to create a new record

        Arguments:
            username -- who is sending the request
            uid -- order unique identifier

        Returns:
            Object needed by DynamoDB to create a record
        """
        order_errors = []
        driver = None
        
        if uid is None:
            uid = str(uuid.uuid4())
        
        delivery_date = self.order_data.get("delivery_date")
        delivery_time = self.order_data.get("delivery_time")
        
        geolocation = self.fetch_geolocation()
        if geolocation is None:
            self.logger.info("Geolocation Data is missing, adding to the list of errors")
            order_errors.append(
                {
                    "code": "ADDRESS_NEEDS_GEO",
                    "value": "Order requires geolocation coordinates to be updated manually",
                }
            )
        else:
            driver = self.get_available_driver(geolocation,
                                            delivery_time,
                                            delivery_date)

        items = [item.__dict__ for item in self.order_data.get(
            "cart_items", [])]

        status = OrderStatus.ERROR.value if order_errors else OrderStatus.CREATED.value
        data = {
            "id": uid,
            "client_name": self.order_data.get("client_name"),
            "delivery_date": delivery_date,
            "delivery_time": delivery_time,
            "address": self.order_data.get("delivery_address"),
            "latitude": float(geolocation.get("latitude", 0)),
            "longitude": float(geolocation.get("longitude", 0)),
            "phone_number": self.order_data.get("phone_number"),
            "cart_items": items,
            "total_amount": float(self.order_data.get("total_amount", 0)),
            "payment_method": self.order_data.get("payment_method"),
            "created_by": username,
            "created_at": datetime.now().isoformat(),
            "updated_by": None,
            "updated_at": None,
            "errors": order_errors,
            "notes": None,
            "status": status,
            "delivery_sequence": None,
            "driver": driver
        }

        return data
