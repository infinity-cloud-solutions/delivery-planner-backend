# Python's libraries
import json
from datetime import datetime

# Own's modules
from order_modules.errors.util_error import UtilError
from order_modules.utils.encoders import DecimalEncoder

# Third-party libraries
from aws_lambda_powertools import Logger


class DoormanUtil(object):

    def __init__(self, _request, _logger=None):
        self.logger = _logger or Logger()
        self.request = _request

    def get_body_from_request(self):
        if "body" not in self.request:
            raise UtilError(
                _message="There is no body in request data",
                _error=None,
                _logger=self.logger
            )

        if self.request['body'] is None:
            raise UtilError(
                _message="The body node is null",
                _error=None,
                _logger=self.logger,
            )
        # Check if body is already a dict and return it directly
        if isinstance(self.request['body'], dict):
            return self.request['body']
        try:
            body = json.loads(self.request['body'])
        except Exception as e:
            raise UtilError(
                _message=f"The body was not a JSON object. Details: {e}",
                _error=None,
                _logger=self.logger,
            )

        return body

    def get_date_param_from_request(self):
        date = self.get_query_param_from_request(
            _query_param_name="date",
            _is_required=True
        )
        return self._transform_date(date)
    
    def get_query_param_from_request(self, _query_param_name, _is_required=False):
        if 'queryStringParameters' not in self.request:
            if _is_required:
                raise UtilError(
                    _message="There is no queryStringParameters in request data",
                    _error=None,
                    _logger=self.logger,
                )
            else:
                return None

        if _query_param_name not in self.request['queryStringParameters']:
            if _is_required:
                raise UtilError(
                    _message=f"There is no {_query_param_name} in queryStringParameters",
                    _error=None,
                    _logger=self.logger,
                )
            else:
                return None

        try:
            query_parameters = self.request['queryStringParameters'][_query_param_name]
            query_param_value = None

            if query_parameters is None or \
                    query_parameters == "":
                if _is_required:
                    raise UtilError(
                        _message=f"Value of {_query_param_name} is missing",
                        _error=None,
                        _logger=self.logger,
                    )

                query_param_value = None

            else:
                query_param_value = self.request['queryStringParameters'][_query_param_name]

            return query_param_value

        except Exception as e:
            raise UtilError(
                _message=str(e),
                _error=str(e),
                _logger=self.logger
            )

    def build_response(self, payload: dict, status_code: int) -> dict:
        """This code defines the response_success function, which is used to return a response to the client.
        The function takes two parameters: payload and status_code.
        The payload parameter is used to provide the body of the response,
        while the status_code parameter is used to set the status code of the response.
        The function then creates a response dictionary with headers that allow for cross-origin requests, as well as setting the status code and body of the response.
        Finally, it logs the response and returns it to the client.

        :param _payload: payload to return to client, defaults to None
        :type _payload: dict, optional
        :param _status_code: HTTP status code, 201 for create
        :type _status_code: int, optional
        :return: dict with the formatted response
        :rtype: dict
        """
        response = {
            "isBase64Encoded": False,
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": json.dumps(payload, cls=DecimalEncoder)
        }

        return response

    def get_username_from_token(self):
        # ToDO
        return "Admin"

    def auth_user(self):
        return True
