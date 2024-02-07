from unittest import TestCase
from unittest.mock import patch
from datetime import datetime
import json
import os
import uuid

from src.orders.app import create_order


class TestCreateOrderLambdaHandler(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.valid_input = {
            "client_name": "Test User",
            "delivery_date": datetime.now().strftime("%Y-%m-%d"),
            "delivery_time": "9-1",
            "delivery_address": "Mock Address 1234, Colonia Juárez, Zapopan, Jalisco, 12345",
            "phone_number": "3312121212",
            "cart_items": [
                {"product": "Berry", "quantity": 2, "price": 10, "sku": "222222"},
                {"product": "Mango", "quantity": 5, "price": 20, "sku": "111111"},
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

    @patch("uuid.uuid4")
    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch("src.orders.app.OrderHelper.get_available_driver")
    @patch(
        "order_modules.data_mapper.order_mapper.Geolocation.get_lat_and_long_from_street_address"
    )
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    @patch("src.orders.app.DoormanUtil.auth_user")
    @patch("src.orders.app.DoormanUtil.get_username_from_context")
    def test_give_a_valid_input_when_a_request_is_made_then_a_record_will_be_saved(
        self,
        get_username_mocked,
        auth_user_mocked,
        get_body_mocked,
        geolocation_mocked,
        get_driver_mocked,
        dao_mocked,
        uuid_mock,
    ):
        get_driver_mocked.return_value = 2
        mock_id = "123e4567-e89b-12d3-a456-426614174000"
        uuid_mock.return_value = uuid.UUID(mock_id)

        response = {
            "isBase64Encoded": False,
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": json.dumps(
                {"id": mock_id, "status": "Creada", "assigned_driver": 2, "errors": []}
            ),
        }

        dao_response = {
            "status": "success",
            "status_code": 201,
            "message": "Record saved in DynamoDB",
            "payload": None,
        }
        get_username_mocked.return_value = "Mock User"
        auth_user_mocked.return_value = True
        get_body_mocked.return_value = self.valid_input
        geolocation_mocked.return_value = {"latitude": 20.12, "longitude": -103.12}
        dao_mocked.return_value = dao_response
        observed = create_order({"body": json.dumps(self.valid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch(
        "order_modules.data_mapper.order_mapper.Geolocation.get_lat_and_long_from_street_address"
    )
    @patch("src.orders.app.DoormanUtil")
    def test_give_an_invalid_input_when_a_request_is_made_then_a_bad_request_will_return(
        self, doorman_mocked, geolocation_mocked
    ):
        response = {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-apigateway-header,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS, DELETE",
            },
            "body": {
                "message": "[{'loc': ('delivery_date',), 'msg': 'str type expected', 'type': 'type_error.str'}]"
            },
        }

        doorman_mocked.return_value.get_username_from_context.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = True
        doorman_mocked.return_value.get_body_from_request.return_value = (
            self.invalid_input
        )
        geolocation_mocked.return_value = {"latitude": 20.12, "longitude": -103.12}
        doorman_mocked.return_value.build_response.return_value = response
        observed = create_order({"body": json.dumps(self.invalid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch(
        "order_modules.data_mapper.order_mapper.Geolocation.get_lat_and_long_from_street_address"
    )
    @patch("src.orders.app.DoormanUtil")
    def test_give_a_valid_input_when_a_request_is_made_by_an_unauthorized_user_then_a_forbidden_will_return(
        self, doorman_mocked, geolocation_mocked, dao_mocked
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

        doorman_mocked.return_value.get_username_from_context.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = False
        doorman_mocked.return_value.get_body_from_request.return_value = (
            self.valid_input
        )
        doorman_mocked.return_value.build_response.return_value = response
        geolocation_mocked.return_value = {"latitude": 20.12, "longitude": -103.12}
        dao_mocked.return_value = None
        observed = create_order({"body": json.dumps(self.valid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch("order_modules.data_mapper.order_mapper.Geolocation")
    @patch("src.orders.app.DoormanUtil")
    def test_give_an_unexpected_error_when_a_request_is_made_then_an_internal_server_error_will_return(
        self, doorman_mocked, geolocation_mocked, dao_mocked
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

        doorman_mocked.return_value.get_username_from_context.return_value = "Mock User"
        doorman_mocked.return_value.auth_user.return_value = False
        doorman_mocked.return_value.get_body_from_request.return_value = (
            self.valid_input
        )
        doorman_mocked.return_value.build_response.return_value = response
        geolocation_mocked.side_effect = Exception("Mocked")
        dao_mocked.return_value = None
        observed = create_order({"body": json.dumps(self.valid_input)}, None)
        expected = response

        self.assertEqual(observed, expected)
