# Python libraries
import json
from decimal import Decimal
from typing import Dict
from typing import Any

# Own modules
from product_modules.utils.aws import AWSClientManager

# Third-party libraries
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError


class DynamoDBHandler:
    """
    A class for handling interactions with a DynamoDB table
    """
    HTTP_STATUS_OK = 200
    HTTP_STATUS_CREATED = 201
    HTTP_STATUS_NO_CONTENT = 204
    HTTP_STATUS_BAD_REQUEST = 400
    HTTP_STATUS_FORBIDDEN = 403
    HTTP_STATUS_NOT_FOUND = 404
    HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

    def __init__(self, table_name: str, partition_key: str, sort_key: str = None):
        self.table_name = table_name
        self.partition_key = partition_key
        self.sort_key = sort_key
        aws_resources_manager = AWSClientManager()
        dynamodb_resource = aws_resources_manager.dynamodb
        self.table = dynamodb_resource.Table(table_name)
        self.logger = Logger()

    def insert_record(
        self, item: dict
    ) -> Dict[str, Any]:
        """This function is used to save a record to a database.
        It takes in a dictionary, which is build from a Order Model, as an argument and attempts to put the item into the database.
        If the response from the database is successful, it returns a status of "success".
        If not, it returns a status of "error" along with the HTTP status code and details about the error message.
        If there is an AWS ClientError, it logs information about the error and also returns a status of "error" along
        with the HTTP status code and details about the error message.

        :param item: product representation built as a dict
        :type item: dict
        :return: A summary of the put_item action
        :rtype: Dict[str, Any]
        """
        try:
            db_item = json.loads(json.dumps(item), parse_float=Decimal)
            response = self.table.put_item(
                Item=db_item
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] == self.HTTP_STATUS_OK:
                self.logger.info(
                    "Product was created in DynamoDB"
                )
                return self.build_response_object(
                    status="success",
                    status_code=self.HTTP_STATUS_CREATED,
                    message="Record saved in DynamoDB"
                )
            else:
                message = response["Error"]["Message"]
                self.logger.error(f"Failed saving record: Details: {message}")
                return self.build_response_object(
                    status="error",
                    status_code=response["ResponseMetadata"]["HTTPStatusCode"],
                    message=message
                )
        except ClientError as error:
            message = f"{error.response['Error']['Message']}. {error.response['Error']['Code']}"
            self.logger.error(f"ClientError when saving record: Details: {message}")
            return self.build_response_object(
                status="error",
                status_code=error.response["ResponseMetadata"]["HTTPStatusCode"],
                message=message
            )
        except Exception as error:
            self.logger.error(f"Exception when saving record: Details: {error}")
            return self.build_response_object(
                status="error",
                status_code=self.HTTP_STATUS_INTERNAL_SERVER_ERROR,
                message=str(error)
            )

    def scan_table(
        self
    ) -> Dict[str, Any]:
        """This function is used to fetch all the records in the table.
        If the response from the database is successful, it returns a status of "success".
        If not, it returns a status of "error" along with the HTTP status code and details about the error message.
        If there is an AWS ClientError, it logs information about the error and also returns a status of "error" along
        with the HTTP status code and details about the error message.

        :return: A summary of the put_item action
        :rtype: Dict[str, Any]
        """
        try:
            response = self.table.scan()
            if response["ResponseMetadata"]["HTTPStatusCode"] == self.HTTP_STATUS_OK:
                self.logger.info(
                    "Products were retrieved from DynamoDB"
                )
                return self.build_response_object(
                    status="success",
                    status_code=self.HTTP_STATUS_OK,
                    message=f"{len(response['Items'])} were found in DynamoDB Products table",
                    payload=response["Items"]
                )
            else:
                message = response["Error"]["Message"]
                self.logger.error(f"Failed saving record: Details: {message}")
                return self.build_response_object(
                    status="error",
                    status_code=response["ResponseMetadata"]["HTTPStatusCode"],
                    message=message
                )
        except ClientError as error:
            message = f"{error.response['Error']['Message']}. {error.response['Error']['Code']}"
            self.logger.error(f"ClientError when saving record: Details: {message}")
            return self.build_response_object(
                status="error",
                status_code=error.response["ResponseMetadata"]["HTTPStatusCode"],
                message=message
            )
        except Exception as error:
            self.logger.error(f"Exception when saving record: Details: {error}")
            return self.build_response_object(
                status="error",
                status_code=self.HTTP_STATUS_INTERNAL_SERVER_ERROR,
                message=str(error)
            )
                        
    def delete_record(self, key: dict) -> Dict[str, Any]:
        """
        This function is used to delete a record from the DynamoDB table.
        It takes in a key dictionary as an argument and attempts to delete the item from the database.
        If the response from the database is successful, it returns a status of "success".
        If there is an AWS ClientError, it logs information about the error and also returns a status of "error" along
        with the HTTP status code and details about the error message.

        :param key: The key of the item to be deleted
        :type key: dict
        :return: A summary of the delete_item action
        :rtype: Dict[str, Any]
        """
        try:
            response = self.table.delete_item(Key=key)
            if response["ResponseMetadata"]["HTTPStatusCode"] == self.HTTP_STATUS_OK:
                self.logger.info(
                    f"Product with key {key} was deleted from DynamoDB"
                )
                return self.build_response_object(
                    status="success",
                    status_code=self.HTTP_STATUS_OK,
                    message="Record deleted from DynamoDB"
                )
            else:
                message = response["Error"]["Message"]
                self.logger.error(f"Failed deleting record: Details: {message}")
                return self.build_response_object(
                    status="error",
                    status_code=response["ResponseMetadata"]["HTTPStatusCode"],
                    message=message
                )
        except ClientError as error:
            message = f"{error.response['Error']['Message']}. {error.response['Error']['Code']}"
            self.logger.error(f"ClientError when deleting record: Details: {message}")
            return self.build_response_object(
                status="error",
                status_code=error.response["ResponseMetadata"]["HTTPStatusCode"],
                message=message
            )
        except Exception as error:
            self.logger.error(f"Exception when deleting record: Details: {error}")
            return self.build_response_object(
                status="error",
                status_code=self.HTTP_STATUS_INTERNAL_SERVER_ERROR,
                message=str(error)
            )

    def update_record(self, item: dict) -> Dict[str, Any]:
        """
        This function is used to update a record in the database using put_item.
        If the item already exists, it will be updated.

        :param item: Item as dict 
        :type item: dict
        :return: A summary of the put_item action
        :rtype: Dict[str, Any]
        """
        try:
            db_item = json.loads(json.dumps(item), parse_float=Decimal)
            response = self.table.put_item(Item=db_item)
            if response["ResponseMetadata"]["HTTPStatusCode"] == self.HTTP_STATUS_OK:
                self.logger.info("Product was updated in DynamoDB")
                return self.build_response_object(
                    status="success",
                    status_code=self.HTTP_STATUS_OK,
                    message="Record updated in DynamoDB"
                )
            else:
                message = response["Error"]["Message"]
                self.logger.error(f"Failed updating record: Details: {message}")
                return self.build_response_object(
                    status="error",
                    status_code=response["ResponseMetadata"]["HTTPStatusCode"],
                    message=message
                )
        except ClientError as error:
            message = f"{error.response['Error']['Message']}. {error.response['Error']['Code']}"
            self.logger.error(f"ClientError when updating record: Details: {message}")
            return self.build_response_object(
                status="error",
                status_code=error.response["ResponseMetadata"]["HTTPStatusCode"],
                message=message
            )
        except Exception as error:
            self.logger.error(f"Exception when updating record: Details: {error}")
            return self.build_response_object(
                status="error",
                status_code=self.HTTP_STATUS_INTERNAL_SERVER_ERROR,
                message=str(error)
            )
            
    def build_response_object(
        self,
        status: str,
        status_code: int,
        message: str,
        payload: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        This method maps an status code a message into the response dictionary

        :param status: Success or Error
        :type status: str
        :param status_code: Http Status Code
        :type status_code: int
        :param message: A string that contains the message to be returned
        :type error_message: str
        :param payload: Object with data from DynamoDb
        :type error_message: dict
        :return: a dictionary with the message
        :rtype: Dict[str, Any]
        """

        return {
            "status": status,
            "status_code": status_code,
            "message": message,
            "payload": payload
        }
