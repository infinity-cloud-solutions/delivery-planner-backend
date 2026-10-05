from unittest import TestCase
from unittest.mock import patch, MagicMock

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def _client_error(code="ValidationException", message="Test error", http_status=400):
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": http_status},
        },
        "operation",
    )


@patch("client_modules.data_access.dynamo_handler.AWSClientManager")
class TestClientDynamoDBHandler(TestCase):

    def _make_handler(self, mock_aws_cls):
        from client_modules.data_access.dynamo_handler import DynamoDBHandler

        mock_table = MagicMock()
        mock_aws_cls.return_value.dynamodb.Table.return_value = mock_table
        handler = DynamoDBHandler(table_name="Clients", partition_key="phone_number")
        return handler, mock_table

    def test_retrieve_records_returns_first_item(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        item = {"phone_number": "5551234567", "name": "Juan"}
        mock_table.query.return_value = {
            "Items": [item],
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        result = handler.retrieve_records(Key("phone_number").eq("5551234567"))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["payload"], item)

    def test_retrieve_records_returns_404_when_no_items(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.query.return_value = {
            "Items": [],
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        result = handler.retrieve_records(Key("phone_number").eq("5550000000"))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 404)
        self.assertIsNone(result["payload"])

    def test_retrieve_records_returns_error_on_client_error(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.query.side_effect = _client_error(
            code="ProvisionedThroughputExceededException", http_status=500
        )

        result = handler.retrieve_records(Key("phone_number").eq("5551234567"))

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)

    def test_insert_record_uses_not_exists_condition(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        result = handler.insert_record({"phone_number": "5551234567", "name": "Juan"})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 201)
        _, kwargs = mock_table.put_item.call_args
        self.assertIn("ConditionExpression", kwargs)

    def test_insert_record_returns_409_when_client_exists(self, mock_aws_cls):
        handler, mock_table = self._make_handler(mock_aws_cls)
        mock_table.put_item.side_effect = _client_error(
            code="ConditionalCheckFailedException", message="The conditional request failed"
        )

        result = handler.insert_record({"phone_number": "5551234567", "name": "Juan"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 409)
