from unittest import TestCase
from models import ShopifyOrder, ShopifyNoteAttribute, ShopifyAddress, ShopifyCustomer, ShopifyLineItem
from data_mapper import ShopifyDataMapper
from exceptions import StorePickupNotAllowed


class TestShopifyDataMapper(TestCase):

    def setUp(self):
        customer = ShopifyCustomer(first_name="John", last_name="Doe")
        shipping_address = ShopifyAddress(address1="123 Happy St", phone="1234567890", latitude=20.0, longitude=-105.0)
        line_items = [ShopifyLineItem(name="Product 1", price=100.0, quantity=2)]
        
        self.valid_order = ShopifyOrder(customer=customer,
                                        shipping_address=shipping_address,
                                        note_attributes=[ShopifyNoteAttribute(name='Order Due Date', value='Wed, 20 Dec 2023')],
                                        payment_gateway_names=['Conekta'],
                                        line_items=line_items,
                                        current_subtotal_price=200.0)

        self.invalid_order = ShopifyOrder(customer=customer,
                                          shipping_address=shipping_address,
                                          note_attributes=[ShopifyNoteAttribute(name='Order Due Date', value='"Wednesday, 20 December 2023"'),
                                                           ShopifyNoteAttribute(name='Order Fulfillment Type', value='Store Pickup')],
                                          line_items=line_items,
                                          current_subtotal_price=200.0)

        self.valid_order_with_paypal = self.valid_order.copy(
            update={"payment_gateway_names": ['paypal']})
        
        self.valid_order_with_multiple_methods = self.valid_order.copy(
                    update={"payment_gateway_names": ['paypal', 'Conekta']})
        
        self.invalid_order_with_other_method = self.valid_order.copy(
            update={"payment_gateway_names": ['abc']})
        
    def test_format_delivery_date_valid(self):
        mapper = ShopifyDataMapper(self.valid_order)
        formatted_date = mapper._get_delivery_date()
        self.assertEqual(formatted_date, "2023-12-20")

    def test_format_delivery_date_invalid(self):
        mapper = ShopifyDataMapper(self.invalid_order)
        with self.assertRaises(ValueError):
            mapper._get_delivery_date()

    def test_get_note_value(self):
        mapper = ShopifyDataMapper(self.valid_order)
        value = mapper._get_note_value("Order Due Date")
        self.assertEqual(value, "Wed, 20 Dec 2023")

    def test_get_coordinate(self):
        mapper = ShopifyDataMapper(self.valid_order)
        latitude = mapper._get_coordinate("latitude")
        longitude = mapper._get_coordinate("longitude")

        self.assertEqual(latitude, 20.0)
        self.assertEqual(longitude, -105.0)

    def test_check_order_is_allowed_valid(self):
        try:
            mapper = ShopifyDataMapper(self.valid_order)
            mapper._check_order_is_allowed()  # Should pass without raising an exception
        except StorePickupNotAllowed:
            self.fail("StorePickupNotAllowed raised unexpectedly!")

    def test_check_order_is_allowed_invalid(self):
        mapper = ShopifyDataMapper(self.invalid_order)
        with self.assertRaises(StorePickupNotAllowed):
            mapper._check_order_is_allowed()

    def test_determine_payment_method_empty(self):
        mapper = ShopifyDataMapper(self.invalid_order)
        self.assertIsNone(mapper._determine_payment_status())

    def test_determine_payment_method_single_conekta(self):
        mapper = ShopifyDataMapper(self.valid_order)
        self.assertEqual(mapper._determine_payment_status(), "PAID")

    def test_determine_payment_method_single_paypal(self):
        mapper = ShopifyDataMapper(self.valid_order_with_paypal)
        self.assertEqual(mapper._determine_payment_status(), "PAID")
        
    def test_determine_payment_method_multiple(self):
        mapper = ShopifyDataMapper(self.valid_order_with_multiple_methods)
        self.assertEqual(mapper._determine_payment_status(), "PAID")
        
    def test_determine_payment_other_method(self):
        mapper = ShopifyDataMapper(self.invalid_order_with_other_method)
        self.assertEqual(mapper._determine_payment_status(), "PAID")
        
    def test_map_order_data(self):
        mapper = ShopifyDataMapper(self.valid_order)
        result = mapper.map_order_data()
        self.assertIsInstance(result, dict)
        self.assertIn("body", result)
        body = result["body"]
        self.assertIn("client_name", body)
        self.assertIn("latitude", body)
        self.assertIn("longitude", body)
        self.assertIn("delivery_date", body)
        self.assertEqual(body["delivery_date"], "2023-12-20")