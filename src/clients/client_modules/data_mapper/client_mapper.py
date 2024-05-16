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

    def fetch_geolocation(self) -> Dict[str, float]:
        """
        Fetches geolocation data based on the client data's address.

        :return: A dictionary with latitude and longitude
        :rtype: Dict[str, float]
        """
        geolocation = self.client_data.get("geolocation", None)
        if geolocation is None:
            self.logger.info(
                "Input did not include geolocation data, invoking Geolocation Service"
            )
            geolocation = self.location_service.get_lat_and_long_from_street_address(
                str_address=self.client_data.get("address")
            )
            return geolocation
        else:
            self.logger.info("Using provided geolocation data from input")
            return geolocation

    def build_client(
        self,
        username: str,
    ) -> Dict[str, Any]:
        """This function will create a dictionary to send to DynamoDB to create a new record

        Arguments:
            username -- who is sending the request

        Returns:
            Object needed by DynamoDB to create a record
        """
        client_errors = []
        latitude = None
        longitude = None
        
        geolocation = self.fetch_geolocation()
        if geolocation is None:
            self.logger.info(
                "Geolocation Data is missing, adding to the list of errors"
            )
            client_errors.append(
                {
                    "code": "ADDRESS_NEEDS_GEO",
                    "value": "Client requires geolocation coordinates to be updated manually",
                }
            )
        else:
            latitude = float(geolocation.get("latitude", 0))
            longitude = float(geolocation.get("longitude", 0))

        data = {
            "phone_number": self.client_data["phone_number"],
            "name": self.client_data["name"],
            "address": self.client_data["address"],
            "latitude": latitude,
            "longitude": longitude,
            "email": self.client_data["email"],
            "errors": client_errors,
            "created_by": username,
            "created_at": datetime.now().isoformat(),
        }
        return data
