import datetime
from typing import Tuple
from typing import List
from typing import Dict
from typing import Any

from order_modules.utils.source import OrderSource


class DeliveryScheduler:
    MORNING_DELIVERIES = "8 AM - 1 PM"
    AFTERNOON_DELIVERIES = "1 PM - 5 PM"
    AT_CAPACITY = 0
    INVALID_SECTOR = 0
    NORTH_WEST_SECTOR = 1
    SOUTH_WEST_SECTOR = 2
    NORTH_EAST_SECTOR = 3
    SOUTH_EAST_SECTOR = 4
    DRIVER_1 = 1
    DRIVER_2 = 2

    def __init__(self, origin=(20.6783825, -103.348088)):
        # Origin is at Hidalgo and Alcalde intersection in Guadalajara
        self.origin = origin

    def _get_day_of_week(self, order_date: str) -> int:
        """Return day of the week based on the order date.

        Returns:
            int: 0 for Monday, 1 for Tuesday, 2 for Wednesday, etc.
        """
        order_date_obj = datetime.datetime.strptime(order_date, "%Y-%m-%d")
        return order_date_obj.weekday()

    def _get_customer_sector(self, customer_location: Tuple[float, float]) -> int:
        """Aux function that will return customer location, based on the origin

        Arguments:
            customer_location -- Tuple that will be used to compare with the origin

        Returns:
            Integer, west sectors are 1 and 2 and east 3 and 4
        """
        if (
            customer_location[0] >= self.origin[0]
            and customer_location[1] <= self.origin[1]
        ):
            return self.NORTH_WEST_SECTOR  # Northwest
        elif (
            customer_location[0] < self.origin[0]
            and customer_location[1] <= self.origin[1]
        ):
            return self.SOUTH_WEST_SECTOR  # Southwest
        elif (
            customer_location[0] >= self.origin[0]
            and customer_location[1] > self.origin[1]
        ):
            return self.NORTH_EAST_SECTOR  # Northeast
        elif (
            customer_location[0] < self.origin[0]
            and customer_location[1] > self.origin[1]
        ):
            return self.SOUTH_EAST_SECTOR  # Southeast
        else:
            return self.INVALID_SECTOR  # Invalid sector

    def _check_capacity_and_assign_driver(
        self,
        orders: List[Dict[str, Any]],
        delivery_time_range: str,
        sector: int,
        source: OrderSource = OrderSource.HIBERRYAPP,
    ) -> int:
        """This function will check if the order can be assign to a delivery man in the delivery_time range

        Arguments:
            orders -- List of orders fetched from DynamoDB using a date as a filter
            delivery_time_range -- Could be for monday shift or afternoon shift
            sector -- Integer that will be used to assign the delivery man to the order, 1 or 2 for west and 3 or 4 for east
                        if we are at capacity for specific hours, we will use the other delivery man
            source -- OrderSource Enum . If Shopify , driver is assigned with no capacity check .
                    Shopify has priority and should be created based on sector only.
        int:
            - 0: If the delivery schedule is at full capacity and the order cannot be accommodated.
            - 1 or 2:  Number of the driver assigned.
        """
        # helper
        driver_sector_map = [
            self.INVALID_SECTOR,
            self.DRIVER_1,  # Northwest
            self.DRIVER_2,  # Southwest
            self.DRIVER_1,  # Northeast
            self.DRIVER_2,  # Southeast
            self.DRIVER_1,
        ]  # Northwest

        # Step 1: Check for max capacity
        total_orders_count = len(orders)

        # Case 1: Delivery Man for this sector has capacity, so we assign it directly to him
        if total_orders_count < 32 or source is OrderSource.SHOPIFY:
            return driver_sector_map[sector]

        # Case 2: We have full capacity for the date (32 deliveries for shift,
        # we have 2 drivers and 2 shifts each, so 32 * 4 = 128)
        if total_orders_count >= 128:
            return self.AT_CAPACITY

        # Step 2: Check Capacity Within Time Range
        time_range_orders = [
            order for order in orders if order["delivery_time"] == delivery_time_range
        ]
        time_range_orders_count = len(time_range_orders)
        # Case 3: Drivers dont have capacity for the range hours
        if time_range_orders_count >= 64:
            return self.AT_CAPACITY

        # Step 3: Assign Delivery Man and Sector
        # Check the nort sector first, if this one is at capacity, then we will assign the order to the second delivery man,
        # Dont need to check the south sector, because we already know that specified range hours contains less than 64 records (32 * 2)
        # So at least one sector has capacity so if its not the first, then its the second

        # driver_sector_map[1] -> DRIVER_1 . By definition, DRIVER_1 is assigned to North sectors.
        north_sector_orders = [
            order
            for order in time_range_orders
            if order["driver"] == driver_sector_map[1]
        ]

        if len(north_sector_orders) < 32:
            # Case 4 Driver has capacity for its own sector
            assigned_driver = driver_sector_map[sector]
        else:
            # Case 5 Driver does not has capacity for its own sector, assign to peer driver
            assigned_driver = driver_sector_map[sector + 1]

        return assigned_driver

    def assign_driver_for_delivery(
        self,
        customer_location: Tuple[float, float],
        delivery_time: str,
        order_date: str,
        orders: List[Dict[str, Any]],
        source: OrderSource = OrderSource.HIBERRYAPP,
    ) -> int:
        """This function will check if the order can be created for the date and time specified

        Arguments:
            customer_location -- Geolocation data, lat and long
            delivery_time -- Options can be '8 AM - 1 PM' or '1 PM - 5 PM'
            order_date -- string date with format YYYY-MM-DD
            orders -- list of orders for specific date, this will help us to check capacity
            source -- OrderSource Enum. Used to give priority to Shopify orders.
        Returns:
            int: Indicates the scheduling status or driver assigned of the delivery order:
                - 0: Order cannot be scheduled
                - 1 or 2:  Number of the driver assigned, indicating successful scheduling.

        Notes:
            Sector-Based Delivery Preferences:
            - West Sectors (1 and 2):
                - Deliveries are preferred on Mondays, Wednesdays, and Fridays (days 0, 2, 4) during the afternoon (1 PM - 5 PM).
                - No morning deliveries (8 AM - 1 PM) on these days in West Sectors.
            - East Sectors (3 and 4):
                - Deliveries are preferred on Tuesdays, Thursdays, and Saturdays (days 1, 3, 5) during the morning (8 AM - 1 PM).
                - No afternoon deliveries (1 PM - 5 PM) on these days in East Sectors.
        """
        day_of_week = self._get_day_of_week(order_date)
        customer_sector = self._get_customer_sector(customer_location)
        driver_assigned = self._check_capacity_and_assign_driver(
            orders=orders,
            delivery_time_range=delivery_time,
            sector=customer_sector,
            source=source,
        )
        if source is OrderSource.SHOPIFY:
            return driver_assigned

        if driver_assigned == 0:
            return 0

        west_sectors = [1, 2]
        east_sectors = [3, 4]

        if (
            day_of_week in [0, 2, 4]
            and delivery_time == self.MORNING_DELIVERIES
            and customer_sector not in west_sectors
        ):
            return 0
        elif (
            day_of_week in [1, 3, 5]
            and delivery_time == self.MORNING_DELIVERIES
            and customer_sector not in east_sectors
        ):
            return 0
        elif (
            day_of_week in [0, 2, 4]
            and delivery_time == self.AFTERNOON_DELIVERIES
            and customer_sector not in east_sectors
        ):
            return 0
        elif (
            day_of_week in [1, 3, 5]
            and delivery_time == self.AFTERNOON_DELIVERIES
            and customer_sector not in west_sectors
        ):
            return 0
        else:
            return driver_assigned
