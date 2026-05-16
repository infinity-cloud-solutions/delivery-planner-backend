import json
import os
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from src.orders.app import create_order


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _valid_body():
    return {
        "client_name": "Test User",
        "delivery_date": _today(),
        "delivery_time": "9 AM - 1 PM",
        "delivery_address": "Test Address 123",
        "phone_number": "3312121212",
        "cart_items": [{"product": "Berry", "quantity": 2, "price": 50.0}],
        "total_amount": 100.0,
        "payment_method": "cash",
    }


class TestCreateOrderExtra(TestCase):

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.create_order")
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_dao_returns_non_201_returns_error_response(
        self, mock_body, mock_build, mock_dao
    ):
        body = _valid_body()
        mock_body.return_value = body
        mock_build.return_value = {
            "id": "x",
            "delivery_date": _today(),
            "latitude": 20.6,
            "longitude": -103.3,
            "status": "Creada",
            "driver": 1,
            "errors": [],
        }
        mock_dao.return_value = {
            "status": "error",
            "status_code": 500,
            "message": "DynamoDB write failed",
        }

        response = create_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_business_error_returns_400(self, mock_body, mock_build):
        from order_modules.errors.business_error import BusinessError

        body = _valid_body()
        mock_body.return_value = body
        mock_build.side_effect = BusinessError("No drivers available")

        response = create_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("No drivers available", json.loads(response["body"])["message"])

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderHelper")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_generic_exception_returns_500(self, mock_body, mock_helper):
        body = _valid_body()
        mock_body.return_value = body
        mock_helper.side_effect = Exception("Unexpected failure")

        response = create_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 500)
