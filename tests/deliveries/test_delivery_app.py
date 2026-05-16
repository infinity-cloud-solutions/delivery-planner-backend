import json
import os
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.orders.delivery.app import (
    set_delivery_schedule_order,
    update_delivery_schedule_order,
)


def _today():
    return datetime.now().strftime("%Y-%m-%d")


class TestSetDeliveryScheduleOrder(TestCase):
    def setUp(self):
        self.valid_event = {
            "body": json.dumps({"date": _today(), "available_drivers": [1, 2]})
        }
        self.single_driver_event = {
            "body": json.dumps({"date": _today(), "available_drivers": [1]})
        }

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.DeliveryProcessor")
    @patch("src.orders.delivery.app.OrderDAO.fetch_orders")
    def test_success_with_orders_returns_200(self, mock_fetch, mock_processor_cls):
        orders = [
            {
                "id": "1",
                "delivery_time": "9 AM - 1 PM",
                "driver": 1,
                "latitude": 20.70,
                "longitude": -103.37,
                "delivery_date": _today(),
            }
        ]
        mock_fetch.return_value = {"payload": orders}
        mock_processor = MagicMock()
        mock_processor_cls.return_value = mock_processor

        response = set_delivery_schedule_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 200)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.OrderDAO.fetch_orders")
    def test_no_orders_returns_200_with_warning(self, mock_fetch):
        mock_fetch.return_value = {"payload": []}

        response = set_delivery_schedule_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 200)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.DeliveryProcessor")
    @patch("src.orders.delivery.app.OrderDAO.fetch_orders")
    def test_single_driver_assigns_all_orders_to_that_driver(
        self, mock_fetch, mock_processor_cls
    ):
        orders = [
            {
                "id": "1",
                "delivery_time": "9 AM - 1 PM",
                "driver": 2,
                "latitude": 20.70,
                "longitude": -103.37,
                "delivery_date": _today(),
            }
        ]
        mock_fetch.return_value = {"payload": orders}
        mock_processor = MagicMock()
        mock_processor_cls.return_value = mock_processor

        response = set_delivery_schedule_order(self.single_driver_event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(orders[0]["driver"], 1)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.DoormanUtil.auth_user")
    def test_unauthorized_returns_403(self, mock_auth):
        mock_auth.return_value = False

        response = set_delivery_schedule_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 403)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_invalid_body_returns_400(self):
        event = {"body": json.dumps({"date": "not-a-date", "available_drivers": [1]})}

        response = set_delivery_schedule_order(event, None)

        self.assertEqual(response["statusCode"], 400)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.OrderDAO.fetch_orders")
    def test_generic_exception_returns_500(self, mock_fetch):
        mock_fetch.side_effect = Exception("DB failure")

        response = set_delivery_schedule_order(self.valid_event, None)

        self.assertEqual(response["statusCode"], 500)


class TestUpdateDeliveryScheduleOrder(TestCase):
    def setUp(self):
        self.valid_orders = [
            {
                "id": "order-1",
                "delivery_date": _today(),
                "delivery_sequence": 1,
                "driver": 1,
                "status": "Programada",
            }
        ]

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.OrderDAO.bulk_update")
    def test_success_returns_200(self, mock_bulk):
        mock_bulk.return_value = {"status": "success"}
        event = {"body": json.dumps(self.valid_orders)}

        response = update_delivery_schedule_order(event, None)

        self.assertEqual(response["statusCode"], 200)
        mock_bulk.assert_called_once()

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.DoormanUtil.auth_user")
    def test_unauthorized_returns_403(self, mock_auth):
        mock_auth.return_value = False
        event = {"body": json.dumps(self.valid_orders)}

        response = update_delivery_schedule_order(event, None)

        self.assertEqual(response["statusCode"], 403)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_invalid_body_returns_400(self):
        event = {"body": json.dumps([{"invalid": "data"}])}

        response = update_delivery_schedule_order(event, None)

        self.assertEqual(response["statusCode"], 400)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.delivery.app.OrderDAO.bulk_update")
    def test_generic_exception_returns_500(self, mock_bulk):
        mock_bulk.side_effect = Exception("DB failure")
        event = {"body": json.dumps(self.valid_orders)}

        response = update_delivery_schedule_order(event, None)

        self.assertEqual(response["statusCode"], 500)
