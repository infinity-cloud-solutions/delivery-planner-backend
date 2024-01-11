# Python's libraries
from datetime import datetime

# Own's modules
from order_modules.data_access.dynamo_handler import DynamoDBHandler
from order_modules.errors.business_error import BusinessError
from order_modules.utils.delivery import DeliveryScheduler

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

        date = item.get("delivery_date", datetime.now().strftime("%Y-%m-%d"))
        customer_location = (item.get("latitude"), item.get("longitude"))
        delivery_time = item.get("delivery_time")
        orders = self.fetch_orders(
            primary_key=ORDERS_PRIMARY_KEY,
            query_value=date
        )
        orders = orders["payload"]
        planner = DeliveryScheduler()
        driver = planner.assign_driver_for_delivery(
            customer_location=customer_location,
            delivery_time=delivery_time,
            order_date=date,
            orders=orders
        )
        if driver:
            item["driver"] = driver
            response = self.orders_db.insert_record(item)
            response["payload"] = {"driver": driver}
        else:
            raise BusinessError("No drivers available")
        return response

    def fetch_orders(self, primary_key: str, query_value: str) -> dict:
        """
        Attempts to insert a new record for an order into the DynamoDB table.

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
