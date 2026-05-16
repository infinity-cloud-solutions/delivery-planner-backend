from unittest import TestCase
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from src.orders.delivery.delivery_modules.data_access.dynamo_handler import (
    DynamoDBHandler,
)


def _make_handler(mock_aws):
    mock_table = MagicMock()
    mock_aws.return_value.dynamodb.Table.return_value = mock_table
    handler = DynamoDBHandler("Orders", "delivery_date")
    return handler, mock_table


def _client_error():
    return ClientError(
        {
            "Error": {"Code": "500", "Message": "AWS Error"},
            "ResponseMetadata": {"HTTPStatusCode": 500},
        },
        "Operation",
    )


class TestDeliveryDynamoDBHandlerUpdateRecords(TestCase):

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
    def test_update_records_success(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        records = [
            {
                "id": "1",
                "delivery_date": "2024-01-08",
                "status": "Programada",
                "delivery_sequence": 1,
                "driver": 1,
            }
        ]

        result = handler.update_records(records)

        self.assertEqual(result["status"], "success")
        mock_table.update_item.assert_called_once()

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
    def test_update_multiple_records(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        records = [
            {
                "id": str(i),
                "delivery_date": "2024-01-08",
                "status": "Programada",
                "delivery_sequence": i,
                "driver": 1,
            }
            for i in range(3)
        ]

        result = handler.update_records(records)

        self.assertEqual(result["status"], "success")
        self.assertEqual(mock_table.update_item.call_count, 3)

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
    def test_update_records_client_error_returns_error(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.update_item.side_effect = _client_error()
        records = [{"id": "1", "delivery_date": "2024-01-08", "status": "Programada"}]

        result = handler.update_records(records)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
    def test_update_records_generic_exception_returns_500(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.update_item.side_effect = Exception("Timeout")
        records = [{"id": "1", "delivery_date": "2024-01-08", "status": "Programada"}]

        result = handler.update_records(records)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)


class TestDeliveryDynamoDBHandlerRetrieve(TestCase):

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
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

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
    def test_retrieve_client_error_returns_error(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.query.side_effect = _client_error()
        from boto3.dynamodb.conditions import Key

        result = handler.retrieve_records(Key("delivery_date").eq("2024-01-08"))

        self.assertEqual(result["status"], "error")

    @patch(
        "src.orders.delivery.delivery_modules.data_access.dynamo_handler.AWSClientManager"
    )
    def test_retrieve_generic_exception_returns_500(self, mock_aws):
        handler, mock_table = _make_handler(mock_aws)
        mock_table.query.side_effect = Exception("Connection lost")
        from boto3.dynamodb.conditions import Key

        result = handler.retrieve_records(Key("delivery_date").eq("2024-01-08"))

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 500)
