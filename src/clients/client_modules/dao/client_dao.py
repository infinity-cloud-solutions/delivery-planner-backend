# Own's modules
from client_modules.data_access.dynamo_handler import DynamoDBHandler
import settings

# Third-party libraries
from boto3.dynamodb.conditions import Key


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
            partition_key="phone_number",
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

    def update_client(self, item: dict) -> dict:
        """
        Attempts to update an existing record for a client in the DynamoDB table.
        If the client does not exist, a new record will be created.

        :param item: Client representation.
        :type item: dict
        :return: A dictionary that contains the response object.
        :rtype: dict
        """
        response = self.clients_db.update_record(item)
        return response

    def fetch_client(self, primary_key: str, query_value: str) -> dict:
        """
        Attempts to retrieve a client record from the DynamoDB table.

        :param primary_key: Field that we will use to query the table
        :type primary_key: str
        :param querie_value: Value that we will use to query the table
        :type querie_value: str
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        key_condition_expression = Key(primary_key).eq(query_value)
        response = self.clients_db.retrieve_records(key_condition_expression)
        return response

    def delete_client(self, phone_number: str) -> dict:
        """
        Attempts to delete a client from the DynamoDB table.
        :param phone_number: The id of the client to delete
        :type phone_number: str
        :return: a dictionary that contains the response object
        :rtype: dict
        """
        return self.clients_db.delete_record(phone_number)
