# Python's libraries
from typing import Dict
from typing import Any
from datetime import datetime

# Own's modules
from client_modules.data_access.geolocation_handler import Geolocation

# Third-party libraries
from aws_lambda_powertools import Logger


class ClientHelper:
    def __init__(
        self, client_data: Dict[str, Any], location_service: Geolocation = None
    ):
        self.client_data = client_data
        self.logger = Logger()
        self.location_service = location_service or Geolocation()

    def fetch_geolocation(self, address_field_name: str) -> Dict[str, float]:
        """
        Fetches geolocation data based on the client data's address.

        :return: A dictionary with latitude and longitude
        :rtype: Dict[str, float]
        """
        self.logger.info(f"Invoking Geolocation Service for {address_field_name}")

        geolocation = self.location_service.get_lat_and_long_from_street_address(
            str_address=self.client_data.get(address_field_name)
        )
        return geolocation

    def get_geolocation_data(
        self,
        address_field_name: str,
        geo_field_name: str,
        error_code: str,
        client_errors: list,
    ) -> Dict[str, float]:
        """
        Helper method to get geolocation data and handle errors.

        :param address_field_name: The field name in client_data for the address.
        :param geo_field_name: The field name in client_data for pre-fetched geolocation.
        :param error_code: The error code to use if geolocation data is missing.
        :param client_errors: The list to append errors to.
        :return: A dictionary with latitude and longitude, or None if not available.
        """
        geolocation = self.client_data.get(geo_field_name)
        if geolocation is None:
            geolocation = self.fetch_geolocation(address_field_name)
            if geolocation is None:
                self.logger.info(
                    f"Geolocation Data for {address_field_name} is missing, adding to the list of errors"
                )
                client_errors.append(
                    {
                        "code": error_code,
                        "value": f"Client requires geolocation coordinates for {address_field_name} to be updated manually",
                    }
                )
        return geolocation

    def build_client(self, username: str) -> Dict[str, Any]:
        """This function will create a dictionary to send to DynamoDB to create/update a new record

        Arguments:
            username -- who is sending the request

        Returns:
            Object needed by DynamoDB to create/update a record
        """
        client_errors = []

        address_geolocation = self.get_geolocation_data(
            "address", "address_geolocation", "ADDRESS_NEEDS_GEO", client_errors
        )
        address_latitude = (
            float(address_geolocation.get("latitude", 0)) if address_geolocation else None
        )
        address_longitude = (
            float(address_geolocation.get("longitude", 0)) if address_geolocation else None
        )

        second_address_latitude = None
        second_address_longitude = None
        if self.client_data.get("second_address") is not None:
            second_address_geolocation = self.get_geolocation_data(
                "second_address", "second_address_geolocation", "SECOND_ADDRESS_NEEDS_GEO", client_errors
            )
            second_address_latitude = (
                float(second_address_geolocation.get("latitude", 0)) if second_address_geolocation else None
            )
            second_address_longitude = (
                float(second_address_geolocation.get("longitude", 0)) if second_address_geolocation else None
            )

        data = {
            "phone_number": self.client_data["phone_number"],
            "name": self.client_data["name"],
            "address": self.client_data["address"],
            "second_address": self.client_data["second_address"],
            "address_latitude": address_latitude,
            "address_longitude": address_longitude,
            "second_address_latitude": second_address_latitude,
            "second_address_longitude": second_address_longitude,
            "discount": self.client_data["discount"],
            "email": self.client_data["email"],
            "errors": client_errors,
            "last_modified_by": username,
            "last_modified_at": datetime.now().isoformat(),
        }
        return data
