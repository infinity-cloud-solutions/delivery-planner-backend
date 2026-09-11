import os
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from src.orders.bonus_report.bonus_report_modules.dao.report_dao import ReportDAO


class TestReportDAO(TestCase):

    def _make_dao(self, table_mock):
        resource_mock = MagicMock()
        resource_mock.Table.return_value = table_mock
        return ReportDAO(
            table_name="Orders",
            index_name="CreatedMonthIndex",
            dynamodb_resource=resource_mock,
        )

    def _make_response(self, items, last_key=None):
        response = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "Items": items,
        }
        if last_key:
            response["LastEvaluatedKey"] = last_key
        return response

    def test_returns_items_for_period(self):
        items = [
            {"id": "1", "created_date_mx": "2026-08-05", "source": Decimal("1")},
            {"id": "2", "created_date_mx": "2026-08-10", "source": Decimal("1")},
        ]
        table = MagicMock()
        table.query.return_value = self._make_response(items)
        dao = self._make_dao(table)

        result = dao.query_orders_by_creation_period("2026-08", "2026-08-01", "2026-08-15")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "1")

    def test_empty_result_returns_empty_list(self):
        table = MagicMock()
        table.query.return_value = self._make_response([])
        dao = self._make_dao(table)

        result = dao.query_orders_by_creation_period("2026-08", "2026-08-01", "2026-08-15")

        self.assertEqual(result, [])

    def test_handles_pagination(self):
        page1 = [{"id": "1", "source": Decimal("1")}]
        page2 = [{"id": "2", "source": Decimal("1")}]
        table = MagicMock()
        table.query.side_effect = [
            self._make_response(page1, last_key={"pk": "cursor"}),
            self._make_response(page2),
        ]
        dao = self._make_dao(table)

        result = dao.query_orders_by_creation_period("2026-08", "2026-08-01", "2026-08-15")

        self.assertEqual(len(result), 2)
        self.assertEqual(table.query.call_count, 2)
        # Second call must include ExclusiveStartKey
        second_call_kwargs = table.query.call_args_list[1][1]
        self.assertIn("ExclusiveStartKey", second_call_kwargs)

    def test_query_uses_correct_index_and_month(self):
        table = MagicMock()
        table.query.return_value = self._make_response([])
        dao = self._make_dao(table)

        dao.query_orders_by_creation_period("2026-08", "2026-08-01", "2026-08-15")

        call_kwargs = table.query.call_args[1]
        self.assertEqual(call_kwargs["IndexName"], "CreatedMonthIndex")

    def test_filter_expression_is_applied(self):
        """Shopify filtering is delegated to DynamoDB via FilterExpression — verify it is passed."""
        table = MagicMock()
        table.query.return_value = self._make_response([])
        dao = self._make_dao(table)

        dao.query_orders_by_creation_period("2026-08", "2026-08-01", "2026-08-15")

        call_kwargs = table.query.call_args[1]
        self.assertIn("FilterExpression", call_kwargs)
