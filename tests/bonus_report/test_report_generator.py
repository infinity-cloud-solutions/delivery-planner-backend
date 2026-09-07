import csv
import io
import re
from datetime import datetime, timezone, timedelta
from unittest import TestCase

from src.orders.bonus_report.bonus_report_modules.report_generator import (
    MX_OFFSET,
    build_detail_csv,
    build_summary_csv,
    get_report_period,
)

_MX_TZ = timezone(MX_OFFSET)


class TestGetReportPeriod(TestCase):

    def test_on_16th_returns_first_to_15th_of_current_month(self):
        today = datetime(2026, 8, 16, 9, 0, 0, tzinfo=_MX_TZ)
        month, start, end, label = get_report_period(today)
        self.assertEqual(month, "2026-08")
        self.assertEqual(start, "2026-08-01")
        self.assertEqual(end, "2026-08-15")
        self.assertEqual(label, "2026-08-01_to_2026-08-15")

    def test_on_1st_returns_16th_to_eom_of_previous_month(self):
        today = datetime(2026, 8, 1, 9, 0, 0, tzinfo=_MX_TZ)
        month, start, end, label = get_report_period(today)
        self.assertEqual(month, "2026-07")
        self.assertEqual(start, "2026-07-16")
        self.assertEqual(end, "2026-07-31")
        self.assertEqual(label, "2026-07-16_to_2026-07-31")

    def test_on_1st_of_march_handles_february_correctly(self):
        today = datetime(2026, 3, 1, 9, 0, 0, tzinfo=_MX_TZ)
        month, start, end, label = get_report_period(today)
        self.assertEqual(month, "2026-02")
        self.assertEqual(start, "2026-02-16")
        self.assertEqual(end, "2026-02-28")

    def test_on_1st_of_january_returns_december_of_previous_year(self):
        today = datetime(2026, 1, 1, 9, 0, 0, tzinfo=_MX_TZ)
        month, start, end, label = get_report_period(today)
        self.assertEqual(month, "2025-12")
        self.assertEqual(start, "2025-12-16")
        self.assertEqual(end, "2025-12-31")

    def test_on_unexpected_day_raises_value_error(self):
        today = datetime(2026, 8, 20, 9, 0, 0, tzinfo=_MX_TZ)
        with self.assertRaises(ValueError) as ctx:
            get_report_period(today)
        self.assertIn("20", str(ctx.exception))

    def test_period_label_uses_underscore_separator(self):
        today = datetime(2026, 8, 16, tzinfo=_MX_TZ)
        _, _, _, label = get_report_period(today)
        self.assertRegex(label, r"^\d{4}-\d{2}-\d{2}_to_\d{4}-\d{2}-\d{2}$")


class TestBuildDetailCsv(TestCase):

    def _parse_csv(self, content: str):
        reader = csv.reader(io.StringIO(content))
        return list(reader)

    def test_empty_orders_returns_only_header(self):
        result = build_detail_csv([])
        rows = self._parse_csv(result)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Fecha de creación")

    def test_single_order_produces_header_plus_one_row(self):
        orders = [
            {
                "created_date_mx": "2026-08-05",
                "created_by": "maria.g",
                "client_name": "Juan Pérez",
                "phone_number": "55-1234-5678",
                "cart_items": [
                    {"product": "Fresa", "quantity": 2, "price": 150},
                    {"product": "Mango", "quantity": 1, "price": 80},
                ],
                "id": "abc123",
            }
        ]
        result = build_detail_csv(orders)
        rows = self._parse_csv(result)
        self.assertEqual(len(rows), 2)
        data_row = rows[1]
        self.assertEqual(data_row[0], "2026-08-05")
        self.assertEqual(data_row[1], "maria.g")
        self.assertEqual(data_row[2], "Juan Pérez")
        self.assertEqual(data_row[3], "55-1234-5678")
        self.assertEqual(data_row[4], "3")   # 2 + 1
        self.assertIn("Fresa", data_row[5])
        self.assertIn("Mango", data_row[5])

    def test_article_count_sums_all_cart_items(self):
        orders = [
            {
                "cart_items": [
                    {"product": "A", "quantity": 5},
                    {"product": "B", "quantity": 3},
                    {"product": "C", "quantity": 10},
                ]
            }
        ]
        result = build_detail_csv(orders)
        rows = self._parse_csv(result)
        self.assertEqual(rows[1][4], "18")

    def test_multiple_orders_produce_correct_row_count(self):
        orders = [{"cart_items": [], "id": str(i)} for i in range(5)]
        result = build_detail_csv(orders)
        rows = self._parse_csv(result)
        self.assertEqual(len(rows), 6)  # header + 5

    def test_missing_optional_fields_default_to_empty_string(self):
        orders = [{"cart_items": []}]
        result = build_detail_csv(orders)
        rows = self._parse_csv(result)
        self.assertEqual(rows[1][0], "")   # created_date_mx
        self.assertEqual(rows[1][1], "")   # created_by


class TestBuildSummaryCsv(TestCase):

    def _parse_csv(self, content: str):
        reader = csv.reader(io.StringIO(content))
        return list(reader)

    def test_aggregates_orders_per_creator(self):
        orders = [
            {"created_by": "maria.g", "cart_items": []},
            {"created_by": "pedro.l", "cart_items": []},
            {"created_by": "maria.g", "cart_items": []},
        ]
        result = build_summary_csv(orders)
        self.assertIn("maria.g", result)
        self.assertIn("2", result)   # maria.g has 2 orders
        self.assertIn("pedro.l", result)

    def test_aggregates_product_totals(self):
        orders = [
            {"created_by": "u1", "cart_items": [
                {"product": "Fresa", "quantity": 3},
                {"product": "Mango", "quantity": 2},
            ]},
            {"created_by": "u2", "cart_items": [
                {"product": "Fresa", "quantity": 5},
            ]},
        ]
        result = build_summary_csv(orders)
        self.assertIn("Fresa", result)
        self.assertIn("8", result)   # 3 + 5
        self.assertIn("Mango", result)
        self.assertIn("2", result)

    def test_two_sections_separated_by_blank_row(self):
        orders = [{"created_by": "u1", "cart_items": [{"product": "P1", "quantity": 1}]}]
        result = build_summary_csv(orders)
        rows = self._parse_csv(result)
        blank_rows = [i for i, r in enumerate(rows) if r == [] or all(c == "" for c in r)]
        self.assertGreater(len(blank_rows), 0, "Expected a blank separator row")

    def test_empty_orders_produces_headers_only(self):
        result = build_summary_csv([])
        rows = self._parse_csv(result)
        texts = [cell for row in rows for cell in row if cell]
        self.assertIn("Creado por", texts)
        self.assertIn("Producto", texts)
        self.assertEqual(len([r for r in rows if any(r)]), 2)  # just the two header rows

    def test_unknown_creator_labelled_desconocido(self):
        orders = [{"cart_items": []}]  # no created_by key
        result = build_summary_csv(orders)
        self.assertIn("Desconocido", result)
