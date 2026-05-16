import json
import os
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch

from src.orders.app import update_order


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _yesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def _valid_body(delivery_date=None, original_date=None, driver=1, original_driver=1):
    date = delivery_date or _today()
    orig = original_date or _today()
    return {
        "id": "test-order-id",
        "client_name": "Test User",
        "delivery_date": date,
        "original_date": orig,
        "delivery_time": "9 AM - 1 PM",
        "delivery_address": "Test Address 123, Guadalajara",
        "phone_number": "3312121212",
        "cart_items": [{"product": "Berry", "quantity": 2, "price": 50.0}],
        "total_amount": 100.0,
        "payment_method": "cash",
        "driver": driver,
        "original_driver": original_driver,
    }


def _dao_update_success():
    return {
        "status": "success",
        "status_code": 200,
        "message": "Updated",
        "payload": None,
    }


def _dao_delete_success():
    return {
        "status": "success",
        "status_code": 200,
        "message": "Deleted",
        "payload": None,
    }


def _order_db_data(date=None):
    return {
        "id": "test-order-id",
        "delivery_date": date or _today(),
        "latitude": 20.67,
        "longitude": -103.35,
        "status": "Creada",
        "driver": 1,
        "errors": [],
        "updated_by": "test",
        "updated_at": "2024-01-08T10:00:00",
    }


class TestUpdateOrder(TestCase):

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.update_order")
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_success_same_date_returns_200(self, mock_body, mock_build, mock_update):
        body = _valid_body()
        mock_body.return_value = body
        mock_build.return_value = _order_db_data()
        mock_update.return_value = _dao_update_success()

        response = update_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 200)
        payload = json.loads(response["body"])
        self.assertEqual(payload["id"], "test-order-id")
        self.assertEqual(payload["assigned_driver"], 1)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.update_order")
    @patch("src.orders.app.OrderDAO.delete_order")
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_success_date_change_deletes_old_then_creates_new(
        self, mock_body, mock_build, mock_delete, mock_update
    ):
        body = _valid_body(delivery_date=_today(), original_date=_yesterday())
        mock_body.return_value = body
        mock_build.return_value = _order_db_data()
        mock_delete.return_value = _dao_delete_success()
        mock_update.return_value = _dao_update_success()

        response = update_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 200)
        mock_delete.assert_called_once()

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.delete_order")
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_delete_failure_on_date_change_returns_500(
        self, mock_body, mock_build, mock_delete
    ):
        body = _valid_body(delivery_date=_today(), original_date=_yesterday())
        mock_body.return_value = body
        mock_build.return_value = _order_db_data()
        mock_delete.return_value = {
            "status": "error",
            "status_code": 500,
            "message": "Delete failed",
        }

        response = update_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_invalid_body_returns_400(self, mock_body):
        mock_body.return_value = {"id": "x", "delivery_date": 12345}

        response = update_order({"body": "{}"}, None)

        self.assertEqual(response["statusCode"], 400)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_business_error_returns_400(self, mock_body, mock_build):
        from order_modules.errors.business_error import BusinessError

        body = _valid_body()
        mock_body.return_value = body
        mock_build.side_effect = BusinessError("No drivers available")

        response = update_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 400)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.DoormanUtil.auth_user")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_unauthorized_user_returns_403(self, mock_body, mock_auth):
        mock_body.return_value = _valid_body()
        mock_auth.return_value = False

        response = update_order({"body": "{}"}, None)

        self.assertEqual(response["statusCode"], 403)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_generic_exception_returns_500(self, mock_body, mock_build):
        body = _valid_body()
        mock_body.return_value = body
        mock_build.side_effect = Exception("Unexpected error")

        response = update_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 500)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.app.OrderDAO.update_order")
    @patch("src.orders.app.OrderHelper.build_order")
    @patch("src.orders.app.DoormanUtil.get_body_from_request")
    def test_dao_update_failure_returns_error(self, mock_body, mock_build, mock_update):
        body = _valid_body()
        mock_body.return_value = body
        mock_build.return_value = _order_db_data()
        mock_update.return_value = {
            "status": "error",
            "status_code": 500,
            "message": "DynamoDB error",
        }

        response = update_order({"body": json.dumps(body)}, None)

        self.assertEqual(response["statusCode"], 500)
