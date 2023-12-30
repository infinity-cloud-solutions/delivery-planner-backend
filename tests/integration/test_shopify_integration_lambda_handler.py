import json
import os
from unittest import TestCase
from unittest import mock
from unittest.mock import patch, Mock

from src.orders.integration.app import lambda_handler
from botocore.exceptions import ClientError


class TestShopifyOrderIntegrationFunction(TestCase):
    def setUp(self):
        self.event_path = "./integration/events/"
        self.context = Mock()
        os.environ['CREATE_ORDER_FUNCTION_NAME'] = 'CreateOrderFunction'
        self.event = self.load_event("1916.json")
        
    def load_event(self, filename):
        with open(os.path.join(self.event_path, filename), 'r') as file:
            return json.load(file)

    @patch('src.orders.integration.app.logger')
    @patch('src.orders.integration.app.boto3.client')
    def test_successful_invocation(self, mock_boto3_client, mock_logger):
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {
            'Payload': Mock(read=Mock(return_value=json.dumps({"statusCode": 200, "body": json.dumps({"message": "Success"})}).encode("utf-8")))
        }
        mock_boto3_client.return_value = mock_lambda_client

        lambda_handler(self.event, self.context)

        mock_lambda_client.invoke.assert_called_once()
        mock_logger.info.assert_called_with("Order created.")

    @patch('src.orders.integration.app.boto3.client')
    def test_client_error_on_invoke(self, mock_boto3_client):
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Boto3 Error"}}, "Invoke")
        mock_boto3_client.return_value = mock_lambda_client

        with self.assertRaises(ClientError):
            lambda_handler(self.event, self.context)

    @patch('src.orders.integration.app.logger')
    @patch('src.orders.integration.app.boto3.client')
    def test_lambda_error_response(self, mock_boto3_client, mock_logger):
      
        mock_lambda_client = Mock()

        mock_lambda_client.invoke.return_value = {
            'Payload': Mock(read=Mock(return_value=json.dumps({"statusCode": 400, "body": json.dumps({"message": "Bad request"})}).encode("utf-8")))
        }
        mock_boto3_client.return_value = mock_lambda_client

        lambda_handler(self.event, self.context)
        mock_logger.error.assert_called_with(mock.ANY)