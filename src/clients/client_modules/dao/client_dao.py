# Own's modules
from client_modules.data_access.dynamo_handler import DynamoDBHandler
import settings


class ClientDAO:
    """
    A class for handling interactions with the DynamoDB table and the Lambda Function.
    """

    def __init__(self):
        """
        Initializes a new instance of the DAO class.
        """
        self.clients_db = DynamoDBHandler(
            table_name=settings.CLIENTS_TABLE_NAME,
            partition_key="phone",
        )

    def create_client(self, item: dict) -> dict:
        """
        Attempts to insert a new record for a client into the DynamoDB table.

        :param item: Client representation
        :type item: dict
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        response = self.clients_db.insert_record(item)
        return response
