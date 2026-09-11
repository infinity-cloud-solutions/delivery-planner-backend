import re
import os
from unittest import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import via order_modules.* (not src.orders.*) so that patches and enum comparisons
# operate on the same module instance that order_mapper.py itself uses at runtime.
from order_modules.data_mapper.order_mapper import OrderHelper
from order_modules.utils.status import OrderStatus


VALID_ORDER_DATA = {
    "client_name": "Test Client",
    "delivery_date": datetime.now().strftime("%Y-%m-%d"),
    "delivery_time": "9-1",
    "delivery_address": "Calle Falsa 123, Guadalajara",
    "phone_number": "3312121212",
    "cart_items": [{"product": "Fresa", "quantity": 2, "price": 10.0}],
    "total_amount": 20.0,
    "payment_method": "cash",
    "source": MagicMock(value=1),
    "notes": None,
    "discount": None,
    "geolocation": {"latitude": 20.67, "longitude": -103.35},
    "delivery_sequence": None,
    "cooler": None,
}


@patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
@patch("order_modules.data_mapper.order_mapper.OrderDAO")
@patch("order_modules.data_mapper.order_mapper.DeliveryScheduler")
@patch("order_modules.data_mapper.order_mapper.Geolocation")
class TestOrderHelperBuildOrder(TestCase):

    def _make_helper(self, data=None):
        if data is None:
            data = dict(VALID_ORDER_DATA)
        return OrderHelper(data)

    def test_creation_stores_created_metadata(self, mock_geo_cls, mock_scheduler_cls, mock_dao_cls):
        mock_geo_cls.return_value.get_lat_and_long_from_street_address.return_value = {
            "latitude": 20.67, "longitude": -103.35
        }
        helper = self._make_helper()
        result = helper.build_order(username="juan", status_on_success=OrderStatus.CREATED)

        self.assertIn("created_by", result)
        self.assertIn("created_at", result)
        self.assertIn("created_month", result)
        self.assertIn("created_date_mx", result)
        self.assertNotIn("updated_by", result)
        self.assertNotIn("updated_at", result)
        self.assertEqual(result["created_by"], "juan")

    def test_creation_with_geo_error_still_stores_created_metadata(
        self, mock_geo_cls, mock_scheduler_cls, mock_dao_cls
    ):
        # Geo service returns None → order gets ERROR status, but creation metadata must still be set
        mock_geo_cls.return_value.get_lat_and_long_from_street_address.return_value = None
        data = dict(VALID_ORDER_DATA)
        data.pop("geolocation", None)  # force the lookup path through location_service
        helper = self._make_helper(data)
        result = helper.build_order(username="maria", status_on_success=OrderStatus.CREATED)

        self.assertIn("created_by", result)
        self.assertIn("created_at", result)
        self.assertIn("created_month", result)
        self.assertIn("created_date_mx", result)
        self.assertNotIn("updated_by", result)
        self.assertNotIn("updated_at", result)

    def test_update_stores_updated_metadata(self, mock_geo_cls, mock_scheduler_cls, mock_dao_cls):
        mock_geo_cls.return_value.get_lat_and_long_from_street_address.return_value = {
            "latitude": 20.67, "longitude": -103.35
        }
        helper = self._make_helper()
        result = helper.build_order(username="admin", status_on_success=OrderStatus.PROGRAMMED)

        self.assertIn("updated_by", result)
        self.assertIn("updated_at", result)
        self.assertNotIn("created_by", result)
        self.assertNotIn("created_at", result)
        self.assertNotIn("created_month", result)
        self.assertNotIn("created_date_mx", result)

    def test_created_month_format(self, mock_geo_cls, mock_scheduler_cls, mock_dao_cls):
        mock_geo_cls.return_value.get_lat_and_long_from_street_address.return_value = {
            "latitude": 20.67, "longitude": -103.35
        }
        helper = self._make_helper()
        result = helper.build_order(username="juan", status_on_success=OrderStatus.CREATED)

        self.assertRegex(result["created_month"], r"^\d{4}-\d{2}$")

    def test_created_date_mx_format(self, mock_geo_cls, mock_scheduler_cls, mock_dao_cls):
        mock_geo_cls.return_value.get_lat_and_long_from_street_address.return_value = {
            "latitude": 20.67, "longitude": -103.35
        }
        helper = self._make_helper()
        result = helper.build_order(username="juan", status_on_success=OrderStatus.CREATED)

        self.assertRegex(result["created_date_mx"], r"^\d{4}-\d{2}-\d{2}$")
