import os
from unittest import TestCase
from unittest.mock import patch

from src.orders.app import delete_order


class TestDeleteOrder(TestCase):
    def setUp(self):
        self.valid_event = {
            "queryStringParameters": {
                "id": "test-order-id",
                "delivery_date": "2024-01-08",
            }
        }

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.delete_order")
    def test_success_returns_204(self, mock_delete):
        mock_delete.return_value = {
            "status": "success",
            "status_code": 200,
            "message": "Record deleted",
        }

        response = delete_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 204)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.DoormanUtil.auth_user")
    def test_unauthorized_user_returns_403(self, mock_auth):
        mock_auth.return_value = False

        response = delete_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 403)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.delete_order")
    def test_dao_error_returns_500(self, mock_delete):
        mock_delete.return_value = {
            "status": "error",
            "status_code": 500,
            "message": "DynamoDB error",
        }

        response = delete_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_invalid_date_format_returns_400(self):
        event = {
            "queryStringParameters": {
                "id": "test-id",
                "delivery_date": "not-a-date",
            }
        }

        response = delete_order(event, None)

        self.assertEqual(response["statusCode"], 400)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.delete_order")
    def test_generic_exception_returns_500(self, mock_delete):
        mock_delete.side_effect = Exception("Unexpected DB failure")

        response = delete_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_missing_id_param_returns_500(self):
        event = {"queryStringParameters": {"delivery_date": "2024-01-08"}}

        response = delete_order(event, None)

        self.assertEqual(response["statusCode"], 500)
