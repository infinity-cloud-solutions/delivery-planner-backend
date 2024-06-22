# Python libraries
from typing import Dict
from typing import Any
from typing import List

# Own modules
from delivery_modules.utils.aws import AWSClientManager

# Third-party libraries
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


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

    def update_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """This function is used to update records to the DB.

        :param item: Order representation built as a dict
        :type item: dict
        :return: A summary of the update_item action
        :rtype: Dict[str, Any]
        """
        try:
            total_records = len(records)
            self.logger.debug(f"Total records to update: {total_records}")
            for index, record in enumerate(records, start=1):
                self.logger.debug(f"Updating record {index} of {total_records}")

                update_expression = "SET delivery_sequence = :val, #status = :statusVal, #driver = :driverVal"
                expression_attribute_values = {
                    ":val": record["delivery_sequence"],
                    ":statusVal": "Programada",
                    ":driverVal": record["driver"],
                }
                expression_attribute_names = {"#status": "status", "#driver": "driver"}
                self.table.update_item(
                    Key={"delivery_date": record["delivery_date"], "id": record["id"]},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExpressionAttributeNames=expression_attribute_names,
                )

            return self.build_response_object(
                status="success",
                status_code=self.HTTP_STATUS_OK,
                message="Records updated in DynamoDB",
            )
        except ClientError as error:
            message = f"{error.response['Error']['Message']}. {error.response['Error']['Code']}"
            self.logger.error(f"ClientError when saving record: Details: {message}")
            return self.build_response_object(
                status="error",
                status_code=error.response["ResponseMetadata"]["HTTPStatusCode"],
                message=message,
            )
        except Exception as error:
            self.logger.error(f"Exception when saving record: Details: {error}")
            return self.build_response_object(
                status="error",
                status_code=self.HTTP_STATUS_INTERNAL_SERVER_ERROR,
                message=str(error),
            )

    def retrieve_records(self, key_condition_expression: Key) -> Dict[str, Any]:
        try:
            response = self.table.query(
                KeyConditionExpression=key_condition_expression,
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] == self.HTTP_STATUS_OK:
                self.logger.info("Order were fetched from DynamoDB")
                return self.build_response_object(
                    status="success",
                    status_code=self.HTTP_STATUS_OK,
                    message=f"{len(response['Items'])} items were found",
                    payload=response["Items"],
                )
            else:
                message = response["Error"]["Message"]
                self.logger.error(f"Failed saving record: Details: {message}")
                return self.build_response_object(
                    status="error",
                    status_code=response["ResponseMetadata"]["HTTPStatusCode"],
                    message=message,
                )
        except ClientError as error:
            message = f"{error.response['Error']['Message']}. {error.response['Error']['Code']}"
            self.logger.error(f"ClientError when saving record: Details: {message}")
            return self.build_response_object(
                status="error",
                status_code=error.response["ResponseMetadata"]["HTTPStatusCode"],
                message=message,
            )
        except Exception as error:
            self.logger.error(f"Exception when saving record: Details: {error}")
            return self.build_response_object(
                status="error",
                status_code=self.HTTP_STATUS_INTERNAL_SERVER_ERROR,
                message=str(error),
            )

    def build_response_object(
        self,
        status: str,
        status_code: int,
        message: str,
        payload: Dict[str, Any] = None,
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
            "payload": payload,
        }
