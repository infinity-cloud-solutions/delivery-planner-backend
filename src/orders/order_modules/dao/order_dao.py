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
            sort_key="id",
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

    def get_order(self, delivery_date: str, order_id: str) -> dict:
        """
        Attempts to retrieve a single order record from the DynamoDB table.

        :param delivery_date: The delivery date (partition key)
        :type delivery_date: str
        :param order_id: The order id (sort key)
        :type order_id: str
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        response = self.orders_db.get_item(
            partition_key_value=delivery_date,
            sort_key_value=order_id,
        )
        return response

    def update_order(self, item: dict) -> dict:
        """
        Attempts to update specific fields of an order record, preserving any
        fields not present in item (e.g. created_by, created_at, created_month).

        :param item: Order representation
        :type item: dict
        :return: a dictionary that contains the response object
        :rtype: dict
        """

        response = self.orders_db.update_item_fields(item)
        return response

    def delete_order(self, delivery_date: str, order_id: str) -> dict:
        """
        Attempts to delete an order from the DynamoDB table.
        :param delivery_date: The delivery date of the order
        :type delivery_date: str
        :param order_id: The unique identifier of the order
        :type order_id: str
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        return self.orders_db.delete_record(delivery_date, order_id)
