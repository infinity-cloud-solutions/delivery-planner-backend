import os
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from botocore.exceptions import ClientError


def _client_error(code="ValidationException", message="Test error"):
    return ClientError(
        {"Error": {"Code": code, "Message": message}, "ResponseMetadata": {"HTTPStatusCode": 400}},
        "operation",
    )


# Import via order_modules.* so patches and the imported class share the same module instance.
@patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
@patch("order_modules.data_access.dynamo_handler.AWSClientManager")
class TestDynamoDBHandlerGetItem(TestCase):

    def _make_handler(self, mock_aws_cls):
        from order_modules.data_access.dynamo_handler import DynamoDBHandler
        mock_table = MagicMock()
        mock_aws_cls.return_value.dynamodb.Table.return_value = mock_table
        handler = DynamoDBHandler(
            table_name="Orders",
            partition_key="delivery_date",
            sort_key="id",
        )
        return handler, mock_table

    def test_get_item_success_returns_item(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        expected_item = {"delivery_date": "2026-08-01", "id": "abc", "client_name": "Test"}
        mock_table.get_item.return_value = {
            "Item": expected_item,
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        result = handler.get_item("2026-08-01", "abc")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["payload"], expected_item)

    def test_get_item_not_found_returns_none_payload(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.get_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        result = handler.get_item("2026-08-01", "nonexistent")

        self.assertEqual(result["status"], "success")
        self.assertIsNone(result["payload"])

    def test_get_item_client_error_returns_error(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.get_item.side_effect = _client_error()

        result = handler.get_item("2026-08-01", "abc")

        self.assertEqual(result["status"], "error")

    def test_get_item_unexpected_error_returns_500(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.get_item.side_effect = Exception("boom")

        result = handler.get_item("2026-08-01", "abc")

        self.assertEqual(result["status_code"], 500)


@patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
@patch("order_modules.data_access.dynamo_handler.AWSClientManager")
class TestDynamoDBHandlerUpdateItemFields(TestCase):

    def _make_handler(self, mock_aws_cls):
        from order_modules.data_access.dynamo_handler import DynamoDBHandler
        mock_table = MagicMock()
        mock_aws_cls.return_value.dynamodb.Table.return_value = mock_table
        handler = DynamoDBHandler(
            table_name="Orders",
            partition_key="delivery_date",
            sort_key="id",
        )
        return handler, mock_table

    def _sample_item(self):
        return {
            "delivery_date": "2026-08-01",
            "id": "abc123",
            "client_name": "Test Client",
            "status": "Programada",
            "updated_by": "admin",
            "updated_at": "2026-08-01T12:00:00",
        }

    def test_update_item_fields_success(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.update_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        result = handler.update_item_fields(self._sample_item())

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)

    def test_update_item_fields_client_error(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.update_item.side_effect = _client_error()

        result = handler.update_item_fields(self._sample_item())

        self.assertEqual(result["status"], "error")

    def test_update_item_fields_unexpected_error(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.update_item.side_effect = Exception("unexpected")

        result = handler.update_item_fields(self._sample_item())

        self.assertEqual(result["status_code"], 500)

    def test_update_item_fields_excludes_keys_from_expression(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.update_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        handler.update_item_fields(self._sample_item())

        call_kwargs = mock_table.update_item.call_args[1]

        # Key must contain only the table key fields
        self.assertIn("delivery_date", call_kwargs["Key"])
        self.assertIn("id", call_kwargs["Key"])
        self.assertEqual(set(call_kwargs["Key"].keys()), {"delivery_date", "id"})

        # ExpressionAttributeNames must not reference key fields
        expr_attr_names = call_kwargs.get("ExpressionAttributeNames", {})
        mapped_fields = set(expr_attr_names.values())
        self.assertNotIn("delivery_date", mapped_fields)
        self.assertNotIn("id", mapped_fields)
