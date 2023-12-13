import json
from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).parent.parent.parent)) 
from src.integration.shopify_processor.processor import process_shopify_event


class TestShopifyOrderProcessingFunction(unittest.TestCase):

    def load_test_event(self, test_event_file_name: str) -> dict:
        try:
            with open(f"tests/events/{test_event_file_name}.json", "r") as file_name:
                event = json.load(file_name)
                return event
        except json.decoder.JSONDecodeError:
            print("Invalid JSON data", event)

    def test_happy_path_process_shopify_event(self):

        shopify_event = self.load_test_event("shopify_event")

        mock_shopify_data = shopify_event['detail']['payload']

        expected_output = {
            "client_name": "Fulano Segundo",
            "phone_number": "+528886700157",
            "address": "Av. Ignacio L Vallarta 5145",
            "latitude": 20.6770496,
            "longitude": -103.4136557,
            "delivery_date": None,
            "delivery_time": None,
            "cart_items": [
                {
                    "name": "Chaqueta",
                    "price": "1500.00",
                    "quantity": 1
                },
                {
                    "name": "Red Snowboard",
                    "price": "50.88",
                    "quantity": 1
                }
            ],
            "total_amount": 1799.02,
            "payment_method": "manual",
            "created_by": 0,
            "created_at": "2023-12-12T19:50:52-05:00",
            "updated_by": 0,
            "updated_at": "2023-12-12T19:50:53-05:00",
            "notes": "a note"
        }

        result = process_shopify_event(mock_shopify_data)

        self.assertEqual(result, expected_output)
