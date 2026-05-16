from unittest import TestCase
from unittest.mock import MagicMock

from src.orders.delivery.delivery_modules.processors.delivery_helpers import (
    DeliveryProcessor,
)


def _make_orders(
    morning_driver1=0, morning_driver2=0, afternoon_driver1=0, afternoon_driver2=0
):
    orders = []
    orders += [
        {
            "id": f"m1-{i}",
            "delivery_time": "9 AM - 1 PM",
            "driver": 1,
            "latitude": 20.70 + i * 0.001,
            "longitude": -103.37,
            "delivery_date": "2024-01-08",
        }
        for i in range(morning_driver1)
    ]
    orders += [
        {
            "id": f"m2-{i}",
            "delivery_time": "9 AM - 1 PM",
            "driver": 2,
            "latitude": 20.60 + i * 0.001,
            "longitude": -103.40,
            "delivery_date": "2024-01-08",
        }
        for i in range(morning_driver2)
    ]
    orders += [
        {
            "id": f"a1-{i}",
            "delivery_time": "1 PM - 5 PM",
            "driver": 1,
            "latitude": 20.70 + i * 0.001,
            "longitude": -103.37,
            "delivery_date": "2024-01-08",
        }
        for i in range(afternoon_driver1)
    ]
    orders += [
        {
            "id": f"a2-{i}",
            "delivery_time": "1 PM - 5 PM",
            "driver": 2,
            "latitude": 20.60 + i * 0.001,
            "longitude": -103.40,
            "delivery_date": "2024-01-08",
        }
        for i in range(afternoon_driver2)
    ]
    return orders


class TestDeliveryProcessor(TestCase):

    def setUp(self):
        self.processor = DeliveryProcessor()

    def test_processes_morning_records_for_driver(self):
        orders = _make_orders(morning_driver1=2)
        dao = MagicMock()

        self.processor.process_records_for_driver(1, orders, dao)

        dao.bulk_update.assert_called()

    def test_processes_afternoon_records_for_driver(self):
        orders = _make_orders(afternoon_driver1=2)
        dao = MagicMock()

        self.processor.process_records_for_driver(1, orders, dao)

        dao.bulk_update.assert_called()

    def test_processes_both_morning_and_afternoon(self):
        orders = _make_orders(morning_driver1=2, afternoon_driver1=2)
        dao = MagicMock()

        self.processor.process_records_for_driver(1, orders, dao)

        self.assertEqual(dao.bulk_update.call_count, 2)

    def test_skips_morning_update_when_no_morning_records(self):
        orders = _make_orders(afternoon_driver1=2)
        dao = MagicMock()

        self.processor.process_records_for_driver(1, orders, dao)

        dao.bulk_update.assert_called_once()

    def test_no_records_for_driver_calls_no_updates(self):
        orders = _make_orders(morning_driver2=2, afternoon_driver2=2)
        dao = MagicMock()

        self.processor.process_records_for_driver(1, orders, dao)

        dao.bulk_update.assert_not_called()
