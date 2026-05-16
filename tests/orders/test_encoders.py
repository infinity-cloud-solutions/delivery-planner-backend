import json
from decimal import Decimal
from unittest import TestCase

from src.orders.order_modules.utils.encoders import DecimalEncoder


class TestDecimalEncoder(TestCase):

    def test_encodes_decimal_as_string(self):
        data = {"amount": Decimal("10.50")}
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        self.assertEqual(parsed["amount"], "10.50")

    def test_encodes_nested_decimal(self):
        data = {"items": [{"price": Decimal("99.99")}]}
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        self.assertEqual(parsed["items"][0]["price"], "99.99")

    def test_passes_through_non_decimal_types(self):
        data = {"name": "Berry", "qty": 2, "active": True}
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        self.assertEqual(parsed["name"], "Berry")
        self.assertEqual(parsed["qty"], 2)
        self.assertTrue(parsed["active"])

    def test_raises_for_non_serializable_type(self):
        data = {"obj": object()}
        with self.assertRaises(TypeError):
            json.dumps(data, cls=DecimalEncoder)
