# Python's libraries
from datetime import datetime

# Own's modules
from order_modules.data_access.dynamo_handler import DynamoDBHandler

from settings import ORDERS_TABLE_NAME
from settings import ORDERS_PRIMARY_KEY

# Third-party libraries
from boto3.dynamodb.conditions import Key


class OrderDAO:
    """
    A class for handling interactions with the DynamoDB table and the Lambda Function.
    """

    def __init__(self):
        """
        Initializes a new instance of the DAO class.
        """
        self.orders_db = DynamoDBHandler(
            table_name=ORDERS_TABLE_NAME,
            partition_key=ORDERS_PRIMARY_KEY,
        )

    def create_order(self, item: dict) -> dict:
        """
        Attempts to insert a new record for an order into the DynamoDB table.

        :param item: Order representation
        :type item: dict
        :return: a dictionary that contains the response object
        :rtype: dict
        """

        response = self.orders_db.insert_record(item)
        return response 
    
    def fetch_orders(self, primary_key: str, query_value: str) -> dict:
        """
        Attempts to retrieve order records from the DynamoDB table.

        :param primary_key: Field that we will use to query the table
        :type primary_key: str
        :param querie_value: Value that we will use to query the table
        :type querie_value: str
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        key_condition_expression = Key(primary_key).eq(query_value)
        response = self.orders_db.retrieve_records(key_condition_expression)
        return response