from unittest import TestCase

from src.orders.delivery.delivery_modules.processors.order_helpers import OrderProcessor


class TestOrderProcessor(TestCase):

    def setUp(self):
        self.processor = OrderProcessor()
        self.orders = [
            {"id": "1", "delivery_time": "9 AM - 1 PM", "driver": 1},
            {"id": "2", "delivery_time": "9 AM - 1 PM", "driver": 2},
            {"id": "3", "delivery_time": "1 PM - 5 PM", "driver": 1},
            {"id": "4", "delivery_time": "1 PM - 5 PM", "driver": 2},
        ]

    def test_selects_orders_matching_time_and_driver(self):
        result = self.processor.select_orders_by_delivery_range_time(
            self.orders, "9 AM - 1 PM", 1
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")

    def test_returns_empty_when_no_match(self):
        result = self.processor.select_orders_by_delivery_range_time(
            self.orders, "9 AM - 1 PM", 99
        )
        self.assertEqual(result, [])

    def test_filters_by_driver_correctly(self):
        result = self.processor.select_orders_by_delivery_range_time(
            self.orders, "1 PM - 5 PM", 2
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "4")

    def test_empty_orders_returns_empty(self):
        result = self.processor.select_orders_by_delivery_range_time(
            [], "9 AM - 1 PM", 1
        )
        self.assertEqual(result, [])

    def test_skips_orders_missing_delivery_time_key(self):
        orders = [{"id": "x", "driver": 1}]
        result = self.processor.select_orders_by_delivery_range_time(
            orders, "9 AM - 1 PM", 1
        )
        self.assertEqual(result, [])

    def test_skips_orders_missing_driver_key(self):
        orders = [{"id": "x", "delivery_time": "9 AM - 1 PM"}]
        result = self.processor.select_orders_by_delivery_range_time(
            orders, "9 AM - 1 PM", 1
        )
        self.assertEqual(result, [])

    def test_multiple_matches_returned(self):
        orders = [
            {"id": "a", "delivery_time": "9 AM - 1 PM", "driver": 1},
            {"id": "b", "delivery_time": "9 AM - 1 PM", "driver": 1},
            {"id": "c", "delivery_time": "9 AM - 1 PM", "driver": 2},
        ]
        result = self.processor.select_orders_by_delivery_range_time(
            orders, "9 AM - 1 PM", 1
        )
        self.assertEqual(len(result), 2)
