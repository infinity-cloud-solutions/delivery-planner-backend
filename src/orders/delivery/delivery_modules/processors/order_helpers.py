from typing import Dict
from typing import List
from typing import Any


class OrderProcessor:

    def select_orders_by_delivery_range_time(self, order_records: List[Dict[str, Any]], delivery_time_to_match: str) -> List[Dict[str, Any]]:
        """
        Process a list of order records and select those that match the specified delivery_time.

        Parameters:
        - order_records (list): List of order records, each containing a 'delivery_time' field.
        - delivery_time_to_match (str): 'delivery_time' value.

        Returns:
        - list: List of selected order records.
        """
        selected_orders = []

        for order in order_records:
            if 'delivery_time' in order and order['delivery_time'] == delivery_time_to_match:
                selected_orders.append(order)

        return selected_orders
