from unittest import TestCase
from unittest.mock import patch
import json
import os

from src.orders.app import create_order


class TestCreateOrderLambdaHandler(TestCase):

    def setUp(self):
        self.valid_input = {
            "client_name": "Test User",
            "delivery_date": "2023-12-20",
            "delivery_time": "9-1",
            "delivery_address": "Mock Address 1234, Colonia Juárez, Zapopan, Jalisco, 12345",
            "phone_number": "3312121212",
            "cart_items": [
                {"name": "Berry", "quantity": 2, "price": 10},
                {"name": "Mango", "quantity": 5, "price": 20},
            ],
            "total_amount": 120.00,
            "payment_method": "cash",
        }
        self.invalid_input = {
            "client_name": "Test User",
            "delivery_date": 2023,
            "delivery_time": "9-1",
            "delivery_address": "Mock Address 1234, Colonia Juárez, Zapopan, Jalisco, 12345",
            "phone_number": "3312121212",
            "cart_items": [
                {"name": "Berry", "quantity": 2, "price": 10},
                {"name": "Mango", "quantity": 5, "price": 20},
            ],
            "total_amount": 120.00,
            "payment_method": "cash",
        }

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch("src.orders.app.Geolocation.get_lat_and_long_from_street_address")
    @patch("src.orders.app.DoormanUtil")
    def test_give_a_valid_input_when_a_request_is_made_then_a_record_will_be_saved(
        self,
        doorman_mocked,
        geolocation_mocked,
        dao_mocked
    ):
        response = {
            "isBase64Encoded": False,
            "statusCode": 201,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": {"message": "Record was created"},
        }

        doorman_mocked.return_value.get_username_from_token.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = True
        doorman_mocked.return_value.get_body_from_request.return_value = self.valid_input
        doorman_mocked.return_value.build_response.return_value = response
        geolocation_mocked.return_value = {"latitude": 20.12, "longitude": -103.12}
        dao_mocked.return_value = None
        observed = create_order({"body": json.dumps(self.valid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.Geolocation.get_lat_and_long_from_street_address")
    @patch("src.orders.app.DoormanUtil")
    def test_give_an_invalid_input_when_a_request_is_made_then_a_bad_request_will_return(
        self,
        doorman_mocked,
        geolocation_mocked
    ):
        response = {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": {"message": "[{'loc': ('delivery_date',), 'msg': 'str type expected', 'type': 'type_error.str'}]"},
        }

        doorman_mocked.return_value.get_username_from_token.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = True
        doorman_mocked.return_value.get_body_from_request.return_value = self.invalid_input
        geolocation_mocked.return_value = {"latitude": 20.12, "longitude": -103.12}
        doorman_mocked.return_value.build_response.return_value = response
        observed = create_order({"body": json.dumps(self.invalid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch("src.orders.app.Geolocation.get_lat_and_long_from_street_address")
    @patch("src.orders.app.DoormanUtil")
    def test_give_a_valid_input_when_a_request_is_made_by_an_unauthorized_user_then_a_forbidden_will_return(
        self,
        doorman_mocked,
        geolocation_mocked,
        dao_mocked
    ):
        response = {
            "isBase64Encoded": False,
            "statusCode": 403,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": {"message": "user Mock User was not auth to create a new order"},
        }

        doorman_mocked.return_value.get_username_from_token.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = False
        doorman_mocked.return_value.get_body_from_request.return_value = self.valid_input
        doorman_mocked.return_value.build_response.return_value = response
        geolocation_mocked.return_value = {"latitude": 20.12, "longitude": -103.12}
        dao_mocked.return_value = None
        observed = create_order({"body": json.dumps(self.valid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch("src.orders.app.Geolocation.get_lat_and_long_from_street_address")
    @patch("src.orders.app.DoormanUtil")
    def test_give_an_unexpected_error_when_a_request_is_made_then_an_internal_server_error_will_return(
        self,
        doorman_mocked,
        geolocation_mocked,
        dao_mocked
    ):
        response = {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": {"message": "Error processing the order: Mocked"},
        }

        doorman_mocked.return_value.get_username_from_token.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = False
        doorman_mocked.return_value.get_body_from_request.return_value = self.valid_input
        doorman_mocked.return_value.build_response.return_value = response
        geolocation_mocked.side_effect = Exception("Mocked")
        dao_mocked.return_value = None
        observed = create_order({"body": json.dumps(self.valid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)
