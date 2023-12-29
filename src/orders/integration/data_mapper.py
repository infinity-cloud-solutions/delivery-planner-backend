from datetime import datetime
from typing import Optional

from models import ShopifyOrder
from exceptions import StorePickupNotAllowed


class ShopifyDataMapper:
    SHOPIFY_ID = 0

    def __init__(self, order: ShopifyOrder):
        self.order = order

    def _format_delivery_date(self, date_str: str) -> str:
        """
        Converts a date string from "ddd, dd MMM yyyy " format to "yyyy-mm-dd" format. 
        Example: Wed, 20 Dec 2023  format to 2023-12-20

        Parameters:
        date_str (str): The date string in "ddd, dd MMM yyyy" format.

        Returns:
        str: The date string in "yyyy-mm-dd" format.
        """
        try:
            date_obj = datetime.strptime(date_str, "%a, %d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError as e:
            raise ValueError(
                f"Invalid date format: {date_str}. Expected 'ddd, dd MMM yyyy'. Error: {e}")

    def _get_note_value(self, attribute_name: str) -> Optional[str]:
        """
        Retrieves the value of a specific attribute from the order's note attributes.

        Parameters:
        attribute_name (str): The name of the attribute for which the value is sought.

        Returns:
        Optional[str]: The value of the specified attribute, if found. Otherwise, None.
        """
        for attribute in self.order.note_attributes:
            if attribute.name == attribute_name:
                return attribute.value
        return None

    def _get_coordinate(self, attribute_name: str) -> Optional[float]:
        """
        Retrieves the latitude or longitude from the shipping address, or falls back to the billing address if necessary.
        (There might be cases where coordinate isnot available from shipping address , but it might be included on billing address.)
        Parameters:
        attribute_name (str): The name of the attribute ('latitude' or 'longitude').

        Returns:
        Optional[float]: The value of the specified coordinate, if found. Otherwise, None.
        """
        shipping_address = self.order.shipping_address
        billing_address = self.order.billing_address

        shipping_coordinate_value = getattr(
            shipping_address, attribute_name, None)
        billing_coordinate_value = getattr(
            billing_address, attribute_name, None)

        if shipping_coordinate_value is not None:
            return shipping_coordinate_value
        elif shipping_address and billing_address and shipping_address.address1 == billing_address.address1:
            return billing_coordinate_value
        return None

    def _get_delivery_date(self) -> str:
        """
        Retrieves and formats the delivery date from the order's note attributes 'Order Due Date.

        Returns:
            str: The formatted delivery date in "yyyy-mm-dd" format.

        Raises:
            ValueError: If the 'Order Due Date' is not in the expected format or is missing.
        """
        delivery_date = self._get_note_value('Order Due Date')
        return self._format_delivery_date(delivery_date)

    def _check_order_is_allowed(self):
        """
        Verifies that the order is not for store pickup and that the shipping address is provided. If any conditions are not met, it 
        raises a StorePickupNotAllowed exception.

        Raises:
            StorePickupNotAllowed: If the order does not meet the required criteria.
        """
        # Check if the fulfillment type is for store pickup.
        fulfillment_type = self._get_note_value('Order Fulfillment Type')
        if fulfillment_type == 'Store Pickup':
            raise StorePickupNotAllowed(
                f"Fulfillment type: {fulfillment_type} is not allowed.")

        # Check if the shipping address is provided.
        if not self.order.shipping_address:
            raise StorePickupNotAllowed(
                "Shipping address information is missing.")

    def map_order_data(self) -> dict:
        """
        Map the Shopify order data into specific data format for the 'CreateOrderFunction'

        Returns:
        dict: Prepared order data for the 'CreateOrderFunction'.
        """

        self._check_order_is_allowed()

        delivery_time = self._get_note_value('Order Due Time')

        order_data = {
            "client_name": f"{self.order.customer.first_name} {self.order.customer.last_name}",
            "phone_number": self.order.shipping_address.phone,
            "delivery_address": self.order.shipping_address.address1,
            "latitude": self._get_coordinate("latitude"),
            "longitude": self._get_coordinate("longitude"),
            "delivery_date": self._get_delivery_date(),
            "delivery_time": delivery_time,
            "cart_items": self.order.line_items_to_dict(),
            # TODO Discuss order.total_price = products + shipping vs current_subtotal_price=products
            "total_amount": self.order.current_subtotal_price,
            "payment_method": ','.join(self.order.payment_gateway_names),
            "created_by": self.SHOPIFY_ID,
            "notes": self.order.note,
        }

        return {"body": order_data}
