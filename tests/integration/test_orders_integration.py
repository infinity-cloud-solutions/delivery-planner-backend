import json
from datetime import datetime, timedelta
from unittest import TestCase

import boto3
from moto import mock_aws

from src.orders.app import create_order, delete_order, retrieve_orders, update_order


def _next_sunday() -> str:
    """Next Sunday (always future). Sunday lifts all zone/sector restrictions."""
    today = datetime.now().date()
    days_ahead = 6 - today.weekday()  # weekday(): Mon=0, Sun=6
    if days_ahead <= 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _base_order_body(date: str = None) -> dict:
    return {
        "client_name": "Integration Test",
        "delivery_date": date or _next_sunday(),
        "delivery_time": "9 AM - 1 PM",
        "delivery_address": "Av. Vallarta 1000, Guadalajara, Jalisco",
        "phone_number": "3312121212",
        "cart_items": [{"product": "HiBerry Box", "quantity": 2, "price": 50.0}],
        "total_amount": 100.0,
        "payment_method": "cash",
        # Provide coords directly to skip the AWS Location Service call
        "geolocation": {"latitude": 20.721722843875, "longitude": -103.370054309085},
    }


def _api_event(body: dict = None, query_params: dict = None) -> dict:
    event = {}
    if body is not None:
        event["body"] = json.dumps(body)
    if query_params is not None:
        event["queryStringParameters"] = query_params
    return event


def _create_orders_table():
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    return dynamodb.create_table(
        TableName="Orders",
        KeySchema=[
            {"AttributeName": "delivery_date", "KeyType": "HASH"},
            {"AttributeName": "id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "delivery_date", "AttributeType": "S"},
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


class _OrdersIntegrationBase(TestCase):
    """Shared setUp/tearDown: moto DynamoDB + local auth bypass."""

    def setUp(self):
        self._moto = mock_aws()
        self._moto.start()
        self.table = _create_orders_table()
        self.delivery_date = _next_sunday()
        from src.orders.order_modules.utils import doorman as dm
        self._orig_dm_env = dm.environment
        dm.environment = "local"

    def tearDown(self):
        from src.orders.order_modules.utils import doorman as dm
        dm.environment = self._orig_dm_env
        self._moto.stop()


class TestCreateOrderIntegration(_OrdersIntegrationBase):

    def test_creates_order_in_dynamodb(self):
        event = _api_event(body=_base_order_body(self.delivery_date))
        response = create_order(event, None)

        self.assertEqual(response["statusCode"], 201)
        order_id = json.loads(response["body"])["id"]

        item = self.table.get_item(
            Key={"delivery_date": self.delivery_date, "id": order_id}
        ).get("Item")
        self.assertIsNotNone(item)
        self.assertEqual(item["client_name"], "Integration Test")

    def test_create_assigns_driver(self):
        response = create_order(_api_event(body=_base_order_body(self.delivery_date)), None)
        body = json.loads(response["body"])
        self.assertGreater(body["assigned_driver"], 0)

    def test_create_stores_geolocation(self):
        response = create_order(_api_event(body=_base_order_body(self.delivery_date)), None)
        body = json.loads(response["body"])
        self.assertAlmostEqual(body["latitude"], 20.721722843875, places=4)
        self.assertAlmostEqual(body["longitude"], -103.370054309085, places=4)

    def test_create_sets_created_by_not_updated_by(self):
        response = create_order(_api_event(body=_base_order_body(self.delivery_date)), None)
        order_id = json.loads(response["body"])["id"]

        item = self.table.get_item(
            Key={"delivery_date": self.delivery_date, "id": order_id}
        ).get("Item")
        self.assertIn("created_by", item)
        self.assertNotIn("updated_by", item)

    def test_multiple_orders_same_date_each_get_unique_id(self):
        r1 = create_order(_api_event(body=_base_order_body(self.delivery_date)), None)
        r2 = create_order(_api_event(body=_base_order_body(self.delivery_date)), None)

        id1 = json.loads(r1["body"])["id"]
        id2 = json.loads(r2["body"])["id"]
        self.assertNotEqual(id1, id2)

    def test_missing_client_name_returns_400(self):
        body = _base_order_body(self.delivery_date)
        del body["client_name"]
        response = create_order(_api_event(body=body), None)
        self.assertEqual(response["statusCode"], 400)

    def test_invalid_date_format_returns_400(self):
        body = _base_order_body(self.delivery_date)
        body["delivery_date"] = "13-01-2024"
        response = create_order(_api_event(body=body), None)
        self.assertEqual(response["statusCode"], 400)

    def test_mismatched_total_amount_returns_400(self):
        body = _base_order_body(self.delivery_date)
        body["total_amount"] = 999.0
        response = create_order(_api_event(body=body), None)
        self.assertEqual(response["statusCode"], 400)


class TestRetrieveOrdersIntegration(_OrdersIntegrationBase):

    def test_returns_orders_for_date(self):
        create_order(_api_event(body=_base_order_body(self.delivery_date)), None)
        create_order(_api_event(body=_base_order_body(self.delivery_date)), None)

        response = retrieve_orders(
            _api_event(query_params={"date": self.delivery_date}), None
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(len(json.loads(response["body"])), 2)

    def test_returns_empty_list_when_no_orders(self):
        response = retrieve_orders(
            _api_event(query_params={"date": self.delivery_date}), None
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), [])

    def test_does_not_return_orders_from_other_dates(self):
        other_date = (
            datetime.strptime(self.delivery_date, "%Y-%m-%d") + timedelta(days=7)
        ).strftime("%Y-%m-%d")
        create_order(_api_event(body=_base_order_body(other_date)), None)

        response = retrieve_orders(
            _api_event(query_params={"date": self.delivery_date}), None
        )

        self.assertEqual(json.loads(response["body"]), [])

    def test_missing_date_param_returns_error(self):
        response = retrieve_orders(_api_event(), None)
        self.assertGreaterEqual(response["statusCode"], 400)


class TestUpdateOrderIntegration(_OrdersIntegrationBase):

    def setUp(self):
        super().setUp()
        create_response = create_order(
            _api_event(body=_base_order_body(self.delivery_date)), None
        )
        body = json.loads(create_response["body"])
        self.order_id = body["id"]
        self.driver = body["assigned_driver"]

    def _update_body(self, delivery_date: str = None, original_date: str = None) -> dict:
        body = _base_order_body(delivery_date or self.delivery_date)
        body.update({
            "id": self.order_id,
            "original_date": original_date or self.delivery_date,
            "driver": self.driver,
            "original_driver": self.driver,
            "status": "Creada",
        })
        return body

    def test_update_same_date_returns_200(self):
        response = update_order(_api_event(body=self._update_body()), None)
        self.assertEqual(response["statusCode"], 200)

    def test_update_sets_updated_by_not_created_by(self):
        update_order(_api_event(body=self._update_body()), None)

        item = self.table.get_item(
            Key={"delivery_date": self.delivery_date, "id": self.order_id}
        ).get("Item")
        self.assertIn("updated_by", item)
        self.assertNotIn("created_by", item)

    def test_update_persists_new_client_name(self):
        body = self._update_body()
        body["client_name"] = "Updated Client"
        update_order(_api_event(body=body), None)

        item = self.table.get_item(
            Key={"delivery_date": self.delivery_date, "id": self.order_id}
        ).get("Item")
        self.assertEqual(item["client_name"], "Updated Client")

    def test_date_change_removes_old_record(self):
        new_date = (
            datetime.strptime(self.delivery_date, "%Y-%m-%d") + timedelta(days=7)
        ).strftime("%Y-%m-%d")
        response = update_order(_api_event(body=self._update_body(delivery_date=new_date)), None)

        self.assertEqual(response["statusCode"], 200)
        old_item = self.table.get_item(
            Key={"delivery_date": self.delivery_date, "id": self.order_id}
        ).get("Item")
        self.assertIsNone(old_item)

    def test_date_change_creates_record_on_new_date(self):
        new_date = (
            datetime.strptime(self.delivery_date, "%Y-%m-%d") + timedelta(days=7)
        ).strftime("%Y-%m-%d")
        update_order(_api_event(body=self._update_body(delivery_date=new_date)), None)

        new_item = self.table.get_item(
            Key={"delivery_date": new_date, "id": self.order_id}
        ).get("Item")
        self.assertIsNotNone(new_item)

    def test_update_missing_required_fields_returns_400(self):
        body = self._update_body()
        del body["client_name"]
        response = update_order(_api_event(body=body), None)
        self.assertEqual(response["statusCode"], 400)


class TestDeleteOrderIntegration(_OrdersIntegrationBase):

    def setUp(self):
        super().setUp()
        create_response = create_order(
            _api_event(body=_base_order_body(self.delivery_date)), None
        )
        self.order_id = json.loads(create_response["body"])["id"]

    def test_delete_returns_204(self):
        response = delete_order(
            _api_event(query_params={"id": self.order_id, "delivery_date": self.delivery_date}),
            None,
        )
        self.assertEqual(response["statusCode"], 204)

    def test_delete_removes_record_from_dynamodb(self):
        delete_order(
            _api_event(query_params={"id": self.order_id, "delivery_date": self.delivery_date}),
            None,
        )

        item = self.table.get_item(
            Key={"delivery_date": self.delivery_date, "id": self.order_id}
        ).get("Item")
        self.assertIsNone(item)

    def test_delete_nonexistent_order_is_idempotent(self):
        response = delete_order(
            _api_event(query_params={"id": "ghost-id", "delivery_date": self.delivery_date}),
            None,
        )
        self.assertEqual(response["statusCode"], 204)

    def test_create_then_retrieve_then_delete_full_lifecycle(self):
        # Retrieve — confirm it's there
        items = json.loads(
            retrieve_orders(
                _api_event(query_params={"date": self.delivery_date}), None
            )["body"]
        )
        self.assertEqual(len(items), 1)

        # Delete
        delete_order(
            _api_event(query_params={"id": self.order_id, "delivery_date": self.delivery_date}),
            None,
        )

        # Retrieve again — should be empty
        items_after = json.loads(
            retrieve_orders(
                _api_event(query_params={"date": self.delivery_date}), None
            )["body"]
        )
        self.assertEqual(items_after, [])

    def test_missing_params_returns_error(self):
        response = delete_order(_api_event(), None)
        self.assertGreaterEqual(response["statusCode"], 400)
