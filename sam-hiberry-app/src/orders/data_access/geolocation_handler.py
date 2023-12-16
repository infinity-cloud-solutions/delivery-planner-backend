# Python's libraries
from typing import Dict

# Own's modules
from errors.source_error import SourceError
from utils.aws import AWSClientManager

from aws_lambda_powertools import Logger


class Geolocation():

    def get_lat_and_long_from_street_address(self, str_address: str) -> Dict(str, float):
        """This function will check AWS Locatio Service to match an address with a geolocation coordinates


        :param str_address: String representation of the address received by client inside the inputs payload
        :type str_address: str
        """
        aws_resources = AWSClientManager()
        location = None
        if isinstance(str_address, str):
            try:
                aws_repsonse = aws_resources.location.search_place_index_for_text(
                    IndexName="HiBerrySearchIndex", Text=str_address
                )
                if aws_repsonse["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    Logger.info(f"Location: {str_address} found")
                    location = aws_repsonse["Results"][0]
                else:
                    raise SourceError("AWS Response was not successfull")
            except Exception as e:
                raise Exception(f"Something failed while fetching data from AWS. Details {e}")
        else:
            raise TypeError("Input provided was not a string")
        return location
