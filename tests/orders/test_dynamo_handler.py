from unittest import TestCase
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from src.orders.order_modules.data_access.dynamo_handler import DynamoDBHandler


def _make_handler(mock_aws):
    mock_table = MagicMock()
    mock_aws.return_value.dynamodb.Table.return_value = mock_table
    handler = DynamoDBHandler("Orders", "delivery_date")
    return handler, mock_table


def _client_error(code="500", message="AWS Error"):
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": 500},
        },
        "Operation",
    )


class TestDynamoDBHandlerInsert(TestCase):

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_insert_success_returns_201(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        result = handler.insert_record({"id": "1", "total": 10.5})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 201)

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_insert_client_error_returns_error(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.put_item.side_effect = _client_error()

        result = handler.insert_record({"id": "1"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_insert_generic_exception_returns_500(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.put_item.side_effect = Exception("Generic failure")

        result = handler.insert_record({"id": "1"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)


class TestDynamoDBHandlerRetrieve(TestCase):

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_retrieve_success_returns_items(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        items = [{"id": "1", "delivery_date": "2024-01-08"}]
        mock_table.query.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "Items": items,
        }
        from boto3.dynamodb.conditions import Key

        key_expr = Key("delivery_date").eq("2024-01-08")

        result = handler.retrieve_records(key_expr)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], items)

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_retrieve_client_error_returns_error(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.query.side_effect = _client_error()
        from boto3.dynamodb.conditions import Key

        result = handler.retrieve_records(Key("delivery_date").eq("2024-01-08"))

        self.assertEqual(result["status"], "error")

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_retrieve_generic_exception_returns_500(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.query.side_effect = Exception("Connection lost")
        from boto3.dynamodb.conditions import Key

        result = handler.retrieve_records(Key("delivery_date").eq("2024-01-08"))

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)


class TestDynamoDBHandlerUpdate(TestCase):

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_update_success_returns_200(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        result = handler.update_record({"id": "1", "status": "Programada"})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_update_client_error_returns_error(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.put_item.side_effect = _client_error()

        result = handler.update_record({"id": "1"})

        self.assertEqual(result["status"], "error")

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_update_generic_exception_returns_500(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.put_item.side_effect = Exception("Unexpected")

        result = handler.update_record({"id": "1"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)


class TestDynamoDBHandlerDelete(TestCase):

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_delete_success_returns_200(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.delete_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        result = handler.delete_record("2024-01-08", "order-1")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_delete_client_error_returns_error(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.delete_item.side_effect = _client_error()

        result = handler.delete_record("2024-01-08", "order-1")

        self.assertEqual(result["status"], "error")

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_delete_generic_exception_returns_500(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.delete_item.side_effect = Exception("Timeout")

        result = handler.delete_record("2024-01-08", "order-1")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)


class TestDynamoDBHandlerBuildResponse(TestCase):

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_build_response_without_payload(self, mock_aws):
        handler, _ = _make_handler(mock_aws)
        result = handler.build_response_object("success", 200, "All good")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["message"], "All good")
        self.assertIsNone(result["payload"])

    @patch("src.orders.order_modules.data_access.dynamo_handler.AWSClientManager")
    def test_build_response_with_payload(self, mock_aws):
        handler, _ = _make_handler(mock_aws)
        payload = [{"id": "1"}]
        result = handler.build_response_object("success", 200, "Found", payload)

        self.assertEqual(result["payload"], payload)
