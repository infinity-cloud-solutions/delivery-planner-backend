import os
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from order_modules.errors.business_error import BusinessError

from src.orders.order_modules.data_mapper.order_mapper import OrderHelper
from src.orders.order_modules.utils.source import OrderSource
from src.orders.order_modules.utils.status import OrderStatus


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _base_order_data(geolocation=None):
    data = {
        "client_name": "Test User",
        "delivery_date": _today(),
        "delivery_time": "9 AM - 1 PM",
        "delivery_address": "Test Address 123",
        "phone_number": "3312121212",
        "cart_items": [{"product": "Berry", "quantity": 2, "price": 50.0}],
        "total_amount": 100.0,
        "payment_method": "cash",
        "source": OrderSource.HIBERRYAPP,
        "notes": None,
        "discount": None,
        "status": OrderStatus.CREATED,
        "cooler": None,
        "delivery_sequence": None,
    }
    if geolocation:
        data["geolocation"] = geolocation
    return data


class TestOrderHelperFetchGeolocation(TestCase):

    def test_returns_provided_geolocation_without_calling_service(self):
        geo = {"latitude": 20.7, "longitude": -103.3}
        order_data = _base_order_data(geolocation=geo)
        helper = OrderHelper(order_data)

        result = helper.fetch_geolocation()

        self.assertEqual(result, geo)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_calls_geolocation_service_when_not_provided(self):
        order_data = _base_order_data()
        mock_service = MagicMock()
        mock_service.get_lat_and_long_from_street_address.return_value = {
            "latitude": 20.72,
            "longitude": -103.37,
        }
        helper = OrderHelper(order_data, location_service=mock_service)

        result = helper.fetch_geolocation()

        mock_service.get_lat_and_long_from_street_address.assert_called_once()
        self.assertEqual(result["latitude"], 20.72)


class TestOrderHelperGetAvailableDriver(TestCase):

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.order_modules.data_mapper.order_mapper.OrderDAO")
    @patch("src.orders.order_modules.data_mapper.order_mapper.DeliveryScheduler")
    def test_returns_driver_when_available(self, mock_scheduler_cls, mock_dao_cls):
        mock_dao = MagicMock()
        mock_dao.fetch_orders.return_value = {"payload": []}
        mock_dao_cls.return_value = mock_dao

        mock_scheduler = MagicMock()
        mock_scheduler.assign_driver_for_delivery.return_value = 1
        mock_scheduler_cls.return_value = mock_scheduler

        helper = OrderHelper(_base_order_data())
        result = helper.get_available_driver(
            {"latitude": 20.7, "longitude": -103.3},
            "9 AM - 1 PM",
            _today(),
            OrderSource.HIBERRYAPP,
        )

        self.assertEqual(result, 1)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.order_modules.data_mapper.order_mapper.OrderDAO")
    @patch("src.orders.order_modules.data_mapper.order_mapper.DeliveryScheduler")
    def test_raises_business_error_when_no_drivers(
        self, mock_scheduler_cls, mock_dao_cls
    ):
        mock_dao = MagicMock()
        mock_dao.fetch_orders.return_value = {"payload": []}
        mock_dao_cls.return_value = mock_dao

        mock_scheduler = MagicMock()
        mock_scheduler.assign_driver_for_delivery.return_value = 0
        mock_scheduler_cls.return_value = mock_scheduler

        helper = OrderHelper(_base_order_data())
        with self.assertRaises(BusinessError):
            helper.get_available_driver(
                {"latitude": 20.7, "longitude": -103.3},
                "9 AM - 1 PM",
                _today(),
                OrderSource.HIBERRYAPP,
            )


class TestOrderHelperBuildOrder(TestCase):

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.order_modules.data_mapper.order_mapper.DeliveryScheduler")
    @patch("src.orders.order_modules.data_mapper.order_mapper.OrderDAO")
    def test_new_order_sets_created_by_metadata(self, mock_dao_cls, mock_scheduler_cls):
        mock_dao = MagicMock()
        mock_dao.fetch_orders.return_value = {"payload": []}
        mock_dao_cls.return_value = mock_dao

        mock_scheduler = MagicMock()
        mock_scheduler.assign_driver_for_delivery.return_value = 1
        mock_scheduler_cls.return_value = mock_scheduler

        helper = OrderHelper(_base_order_data())
        result = helper.build_order(username="user@test.com", generate_driver=True)

        self.assertIn("created_by", result)
        self.assertIn("created_at", result)
        self.assertNotIn("updated_by", result)
        self.assertEqual(result["created_by"], "user@test.com")

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.order_modules.data_mapper.order_mapper.DeliveryScheduler")
    @patch("src.orders.order_modules.data_mapper.order_mapper.OrderDAO")
    def test_update_order_sets_updated_by_metadata(
        self, mock_dao_cls, mock_scheduler_cls
    ):
        mock_dao = MagicMock()
        mock_dao.fetch_orders.return_value = {"payload": []}
        mock_dao_cls.return_value = mock_dao

        mock_scheduler = MagicMock()
        mock_scheduler.assign_driver_for_delivery.return_value = 1
        mock_scheduler_cls.return_value = mock_scheduler

        helper = OrderHelper(_base_order_data())
        result = helper.build_order(
            username="editor@test.com",
            uid="existing-uid",
            generate_driver=True,
        )

        self.assertIn("updated_by", result)
        self.assertIn("updated_at", result)
        self.assertNotIn("created_by", result)
        self.assertEqual(result["updated_by"], "editor@test.com")

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_missing_geolocation_adds_error_and_sets_error_status(self):
        mock_service = MagicMock()
        mock_service.get_lat_and_long_from_street_address.return_value = None

        helper = OrderHelper(_base_order_data(), location_service=mock_service)
        result = helper.build_order(username="test", generate_driver=False)

        self.assertEqual(result["status"], OrderStatus.ERROR.value)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["code"], "ADDRESS_NEEDS_GEO")
        self.assertIsNone(result["latitude"])

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.order_modules.data_mapper.order_mapper.DeliveryScheduler")
    @patch("src.orders.order_modules.data_mapper.order_mapper.OrderDAO")
    def test_uses_provided_uid_when_given(self, mock_dao_cls, mock_scheduler_cls):
        mock_dao = MagicMock()
        mock_dao.fetch_orders.return_value = {"payload": []}
        mock_dao_cls.return_value = mock_dao
        mock_scheduler_cls.return_value = MagicMock()
        mock_scheduler_cls.return_value.assign_driver_for_delivery.return_value = 1

        helper = OrderHelper(_base_order_data())
        result = helper.build_order(username="test", uid="my-uid", generate_driver=True)

        self.assertEqual(result["id"], "my-uid")

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.order_modules.data_mapper.order_mapper.DeliveryScheduler")
    @patch("src.orders.order_modules.data_mapper.order_mapper.OrderDAO")
    def test_generates_uuid_when_no_uid(self, mock_dao_cls, mock_scheduler_cls):
        mock_dao = MagicMock()
        mock_dao.fetch_orders.return_value = {"payload": []}
        mock_dao_cls.return_value = mock_dao
        mock_scheduler_cls.return_value = MagicMock()
        mock_scheduler_cls.return_value.assign_driver_for_delivery.return_value = 1

        helper = OrderHelper(_base_order_data())
        result = helper.build_order(username="test", generate_driver=True)

        self.assertIsNotNone(result["id"])
        self.assertNotEqual(result["id"], "")

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_geolocation_provided_in_data_skips_service(self):
        geo = {"latitude": 20.71, "longitude": -103.37}
        order_data = _base_order_data(geolocation=geo)
        mock_service = MagicMock()
        helper = OrderHelper(order_data, location_service=mock_service)
        result = helper.build_order(username="test", generate_driver=False, driver=1)

        mock_service.get_lat_and_long_from_street_address.assert_not_called()
        self.assertEqual(result["latitude"], 20.71)
