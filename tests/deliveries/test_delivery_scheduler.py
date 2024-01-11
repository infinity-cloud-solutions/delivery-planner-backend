from unittest import TestCase

from src.orders.order_modules.utils.delivery import DeliveryScheduler


class TestDeliveryScheduler(TestCase):

    def setUp(self):
        self.northwest_location = (20.709747, -103.380421)
        self.southwest_location = (20.621087, -103.405140)
        self.northeast_location = (20.704608, -103.316906)
        self.southeast_location = (20.595247, -103.315226)
        self.monday = "2024-01-08"
        self.tuesday = "2024-01-09"
        self.morning_time = "8 AM - 1 PM"
        self.afternoon_time = "1 PM - 5 PM"

    def test_give_a_request_for_northwest_sector_for_the_morning_route_on_a_monday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southwest_sector_for_the_morning_route_on_a_monday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 2} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northeast_sector_for_the_afternoon_route_on_a_monday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northeast_location
        order_date = self.monday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southeast_sector_for_the_afternoon_route_on_a_monday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southeast_location
        order_date = self.monday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 2} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northwest_sector_for_the_afternoon_route_on_a_monday_order_will_not_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.monday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southwest_sector_for_the_afternoon_route_on_a_monday_order_will_not_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southwest_location
        order_date = self.monday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northeast_sector_for_the_morning_route_on_a_monday_order_will_not_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northeast_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southeast_sector_for_the_morning_route_on_a_monday_order_will_not_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southeast_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northwest_sector_for_the_morning_route_on_a_tuesday_order_will_be_not_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.tuesday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southwest_sector_for_the_morning_route_on_a_tuesday_order_will_be_not_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southwest_location
        order_date = self.tuesday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northeast_sector_for_the_afternoon_route_on_a_tuesday_order_will_be_not_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northeast_location
        order_date = self.tuesday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southeast_sector_for_the_afternoon_route_on_a_tuesday_order_will_be_not_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southeast_location
        order_date = self.tuesday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northwest_sector_for_the_afternoon_route_on_a_tuesday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.tuesday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southwest_sector_for_the_afternoon_route_on_a_tuesday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southwest_location
        order_date = self.tuesday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_request_for_northeast_sector_for_the_morning_route_on_a_tuesday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northeast_location
        order_date = self.tuesday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_request_for_southeast_sector_for_the_morning_route_on_a_tuesday_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southeast_location
        order_date = self.tuesday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(10)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

# Test for capacity

    def test_give_a_request_with_max_capacity_for_one_driver_the_other_will_assist_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(32)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(8)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_request_with_max_capacity_for_the_day_the_order_will_not_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(32)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(32)]
        orders += [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(32)]
        orders += [{"delivery_time": self.afternoon_time, "driver": 2} for _ in range(32)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_request_with_max_capacity_for_morning_shift_the_order_will_not_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(32)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(32)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 0

        self.assertEqual(observed, expected)

    def test_give_a_monday_morning_request_for_northwest_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_monday_morning_request_for_southwest_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southwest_location
        order_date = self.monday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_monday_afternoon_request_for_northeast_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northeast_location
        order_date = self.monday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.afternoon_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_monday_afternoon_request_for_southeast_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southeast_location
        order_date = self.monday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.afternoon_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_tuesday_morning_request_for_northwest_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northeast_location
        order_date = self.tuesday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_tuesday_morning_request_for_southwest_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southeast_location
        order_date = self.tuesday
        delivery_time = self.morning_time
        orders = [{"delivery_time": self.morning_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.morning_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)

    def test_give_a_tuesday_afternoon_request_for_northeast_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.northwest_location
        order_date = self.tuesday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.afternoon_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 1

        self.assertEqual(observed, expected)

    def test_give_a_tuesday_afternoon_request_for_southeast_with_where_in_total_there_are_more_than_32_orders_driver_in_sector_is_able_to_deliver_and_order_will_be_created(
        self,
    ):

        scheduler = DeliveryScheduler()
        customer_location = self.southwest_location
        order_date = self.tuesday
        delivery_time = self.afternoon_time
        orders = [{"delivery_time": self.afternoon_time, "driver": 1} for _ in range(20)]
        orders += [{"delivery_time": self.afternoon_time, "driver": 2} for _ in range(20)]

        observed = scheduler.assign_driver_for_delivery(customer_location, delivery_time, order_date, orders)
        expected = 2

        self.assertEqual(observed, expected)
