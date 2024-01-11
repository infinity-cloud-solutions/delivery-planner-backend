import datetime
from typing import Tuple
from typing import List
from typing import Dict
from typing import Any


class DeliveryScheduler:
    def __init__(self, origin=(20.6783825, -103.348088)):
        # Origin is at Hidalgo and Alcalde intersection in Guadalajara
        self.origin = origin
        self.MORNING_DELIVERIES = "8 AM - 1 PM"
        self.AFTERNOON_DELIVERIES = "1 PM - 5 PM"

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
            return 1  # Northwest
        elif (
            customer_location[0] < self.origin[0]
            and customer_location[1] <= self.origin[1]
        ):
            return 2  # Southwest
        elif (
            customer_location[0] >= self.origin[0]
            and customer_location[1] > self.origin[1]
        ):
            return 3  # Northeast
        elif (
            customer_location[0] < self.origin[0]
            and customer_location[1] > self.origin[1]
        ):
            return 4  # Southeast
        else:
            return 0  # Invalid sector

    def _check_capacity_and_assign_sector(self, orders: List[Dict[str, Any]], delivery_time_range: str, sector: int) -> int:
        """This function will check if the order can be assign to a delivery man in the delivery_time range

        Arguments:
            orders -- List of orders fetched from DynamoDB using a date as a filter
            delivery_time_range -- Could be for monday shift or afternoon shift
            sector -- Integer that will be used to assign the delivery man to the order, 1 or 2 for west and 3 or 4 for east
                        if we are at capacity for specific hours, we will use the other delivery man


        Returns:
            Will return 1, 2, 3 or 4 if its possible to assign to any delivery man, 0 in case delivery are at capacity
        """
        # helper
        sectors_matrix = [0, 1, 2, 1, 2, 1]

        # Step 1: Check for max capacity
        total_orders_count = len(orders)

        # Case 1: Delivery Man for this sector has capacity, so we assign it directly to him
        if total_orders_count < 32:
            return sectors_matrix[sector]

        # Case 2: We have full capacity for the date (32 deliveries for shift,
        # we have 2 drivers and 2 shifts each, so 32 * 4 = 128)
        if total_orders_count >= 128:
            return 0

        # Step 2: Check Capacity Within Time Range
        time_range_orders = [order for order in orders if order['delivery_time'] == delivery_time_range]
        time_range_orders_count = len(time_range_orders)
        # Case 3: Drivers dont have capacity for the range hours
        if time_range_orders_count >= 64:
            return 0

        # Step 3: Assign Delivery Man and Sector
        # Check the north sector first, if this one is at capacity, then we will assign the order to the second delivery man,
        # Ee dont need to check the south sector, because we already know that specified range hours contains less than 64 records (32 * 2)
        # So at least one sector has capacity so if its not the first, then its the second
        north_sector_orders = [order for order in time_range_orders if order['driver'] == sectors_matrix[1]]

        if len(north_sector_orders) < 32:
            # Case 4 Driver has capacity for its own sector
            assigned_driver = sectors_matrix[sector]
        else:
            # Case 5 Driver does not has capacity for its own sector, assign to peer driver
            assigned_driver = sectors_matrix[sector + 1]

        return assigned_driver

    def is_delivery_possible(
        self,
        customer_location: Tuple[float, float],
        delivery_time: str,
        order_date: str,
        orders: List[Dict[str, Any]]
    ) -> bool:
        """This function will check if the order can be created for the date and time specified

        Arguments:
            customer_location -- Geolocation data, lat and long
            delivery_time -- Options can be '8 AM - 1 PM' or '1 PM - 5 PM'
            order_date -- string date with format YYYY-MM-DD
            orders -- list of orders for specific date, this will help us to check capacity

        Returns:
            A boolean that will serve to let the client know if we can proceed with the order creation or not
        """
        day_of_week = self._get_day_of_week(order_date)
        customer_sector = self._get_customer_sector(customer_location)
        driver_assigned = self._check_capacity_and_assign_sector(
            orders=orders,
            delivery_time_range=delivery_time,
            sector=customer_sector
        )
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
