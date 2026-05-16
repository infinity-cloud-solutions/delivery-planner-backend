import json
import os
from unittest import TestCase
from unittest.mock import patch

from src.orders.app import retrieve_orders


class TestRetrieveOrders(TestCase):
    def setUp(self):
        self.valid_event = {"queryStringParameters": {"date": "2024-01-08"}}

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.fetch_orders")
    def test_success_returns_200_with_orders(self, mock_fetch):
        orders = [{"id": "abc", "delivery_date": "2024-01-08"}]
        mock_fetch.return_value = {"payload": orders}

        response = retrieve_orders(self.valid_event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), orders)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.DoormanUtil.auth_user")
    def test_unauthorized_user_returns_403(self, mock_auth):
        mock_auth.return_value = False

        response = retrieve_orders(self.valid_event, None)

        self.assertEqual(response["statusCode"], 403)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.fetch_orders")
    def test_dao_exception_returns_500(self, mock_fetch):
        mock_fetch.side_effect = Exception("DB connection failed")

        response = retrieve_orders(self.valid_event, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_missing_date_param_returns_500(self):
        response = retrieve_orders({"queryStringParameters": {}}, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.fetch_orders")
    def test_returns_empty_list_when_no_orders(self, mock_fetch):
        mock_fetch.return_value = {"payload": []}

        response = retrieve_orders(self.valid_event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), [])
