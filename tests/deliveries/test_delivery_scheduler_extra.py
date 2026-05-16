from unittest import TestCase

from order_modules.utils.source import OrderSource

from src.orders.order_modules.utils.delivery import DeliveryScheduler


class TestDeliverySchedulerExtra(TestCase):

    def setUp(self):
        self.scheduler = DeliveryScheduler()
        self.saturday = "2024-01-13"
        self.northwest = (20.709747, -103.380421)
        self.southwest = (20.621087, -103.405140)
        self.northeast = (20.704608, -103.316906)
        self.southeast = (20.595247, -103.315226)
        self.morning = "9 AM - 1 PM"
        self.afternoon = "1 PM - 5 PM"

    def test_saturday_morning_northwest_order_is_created(self):
        orders = [{"delivery_time": self.morning, "driver": 1} for _ in range(5)]
        result = self.scheduler.assign_driver_for_delivery(
            self.northwest, self.morning, self.saturday, orders
        )
        self.assertGreater(result, 0)

    def test_saturday_afternoon_southeast_order_is_created(self):
        orders = [{"delivery_time": self.afternoon, "driver": 2} for _ in range(5)]
        result = self.scheduler.assign_driver_for_delivery(
            self.southeast, self.afternoon, self.saturday, orders
        )
        self.assertGreater(result, 0)

    def test_shopify_order_skips_sector_restriction(self):
        orders = [{"delivery_time": self.morning, "driver": 1} for _ in range(5)]
        # Northeast on a Monday morning would be rejected for HIBERRYAPP
        result = self.scheduler.assign_driver_for_delivery(
            self.northeast,
            self.morning,
            "2024-01-08",
            orders,
            source=OrderSource.SHOPIFY,
        )
        self.assertGreater(result, 0)

    def test_shopify_order_bypasses_capacity_limit(self):
        orders = [{"delivery_time": self.morning, "driver": 1} for _ in range(128)]
        result = self.scheduler.assign_driver_for_delivery(
            self.northwest,
            self.morning,
            "2024-01-08",
            orders,
            source=OrderSource.SHOPIFY,
        )
        self.assertGreater(result, 0)
