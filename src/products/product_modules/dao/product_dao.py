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

    def fetch_products(self) -> dict:
        """
        Attempts to fetch all the records from DynamoDB table.

        :return: a dictionary that contains the response object
        :rtype: dict
        """
        response = self.products_db.scan_table()
        items = response["payload"]
        return items

    def update_product(self, item: dict) -> dict:
        """
        Attempts to update an existing record for a product in the DynamoDB table.
        If the product does not exist, a new record will be created.

        :param item: Product representation.
        :type item: dict
        :return: A dictionary that contains the response object.
        :rtype: dict
        """
        response = self.products_db.update_record(item)
        return response

    def delete_product(self, name: str) -> dict:
        """
        Attempts to delete a record for a product from the DynamoDB table.

        :param name: Name of the product to be deleted
        :type name: str
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        key = {"name": name}
        response = self.products_db.delete_record(key)
        return response
