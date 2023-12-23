# Own's modules
from product_modules.data_access.dynamo_handler import DynamoDBHandler

import settings


class ProductDAO:
    """
    A class for handling interactions with the DynamoDB table and the Lambda Function.
    """

    def __init__(self):
        """
        Initializes a new instance of the DAO class.
        """
        self.products_db = DynamoDBHandler(
            table_name=settings.PRODUCTS_TABLE_NAME,
            partition_key="Id",
        )

    def create_product(self, item: dict) -> dict:
        """
        Attempts to insert a new record for a product into the DynamoDB table.

        :param item: Product representation
        :type item: dict
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        response = self.products_db.insert_record(item)
        return response
