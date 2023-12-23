from typing import Optional

from models import ShopifyNoteAttribute, ShopifyOrder, ShopifyAddress
from exceptions import StorePickupNotAllowed


class ShopifyDataMapper:
    SHOPIFY_ID = 0

    def _get_note_value(self, note_attributes: list[ShopifyNoteAttribute], attribute_name: str) -> Optional[str]:
        """
        Retrieves the value of a specific attribute from a list of Shopify note attributes.

        Parameters:
        note_attributes ([ShopifyNoteAttribute]): A list of ShopifyNoteAttribute objects
                                                  from a Shopify order.
        attribute_name (str): The name of the attribute for which the value is sought.

        Returns:
        Optional[str]: The value of the specified attribute, if found. Otherwise, None.
        """
        for attribute in note_attributes:
            if attribute.name == attribute_name:
                return attribute.value
        return None

    def map_order_data(self, order: ShopifyOrder) -> dict:
        """
        Map the Shopify order data into specific data format for the 'CreateOrderFunction'

        Parameters:
        order(ShopifyOrder): The ShopifyOrder from Shopify webhook event.

        Returns:
        dict: Prepared order data for the 'CreateOrderFunction'.
        """
        note_attributes = order.note_attributes
        fulfillment_type = self._get_note_value(
            note_attributes, 'Order Fulfillment Type')

        if fulfillment_type == 'Store Pickup':
            raise StorePickupNotAllowed()

        address: ShopifyAddress = order.shipping_address if order.shipping_address else order.billing_address

        delivery_date = self._get_note_value(
            note_attributes, 'Order Due Date')
        delivery_time = self._get_note_value(
            note_attributes, 'Order Due Time')

        order_data = {
            "client_name": f"{order.customer.first_name} {order.customer.last_name}",
            "phone_number": address.phone,
            "delivery_address": address.address1,
            "latitude": address.latitude,
            "longitude": address.longitude,
            "delivery_date": delivery_date,
            "delivery_time": delivery_time,
            "cart_items": order.line_items_to_dict(),
            "total_amount": order.total_price,
            "payment_method": ','.join(order.payment_gateway_names),
            "created_by": self.SHOPIFY_ID,
            "notes": order.note,
        }

        return order_data
