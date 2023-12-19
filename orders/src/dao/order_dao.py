# Own's modules
from src.data_access.dynamo_handler import DynamoDBHandler

import settings


class OrderDAO:
    """
    A class for handling interactions with the DynamoDB table and the Lambda Function.
    """

    def __init__(self):
        """
        Initializes a new instance of the DAO class.
        """
        self.orders_db = DynamoDBHandler(
            table_name=settings.ORDERS_TABLE_NAME,
            partition_key="Id",
        )

    def create_order(self, item: dict) -> dict:
        """
        Attempts to insert a new record for an approved payment into the DynamoDB table.

        :param item: Order representation
        :type item: dict
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        response = self.orders_db.insert_record(item)
        return response
