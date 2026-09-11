import os
from unittest import TestCase
from unittest.mock import MagicMock, patch


class TestGenerateBonusReport(TestCase):

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.bonus_report.app.EmailSender")
    @patch("src.orders.bonus_report.app.ReportDAO")
    @patch("src.orders.bonus_report.app.get_report_period")
    def test_success_returns_status_and_order_count(
        self, mock_period, mock_dao_cls, mock_sender_cls
    ):
        from src.orders.bonus_report.app import generate_bonus_report

        mock_period.return_value = (
            "2026-08", "2026-08-01", "2026-08-15", "2026-08-01_to_2026-08-15"
        )
        orders = [
            {"created_by": "u1", "cart_items": [], "id": "1", "created_date_mx": "2026-08-05"},
            {"created_by": "u2", "cart_items": [], "id": "2", "created_date_mx": "2026-08-10"},
        ]
        mock_dao_cls.return_value.query_orders_by_creation_period.return_value = orders
        mock_sender_cls.return_value.send_report.return_value = None

        result = generate_bonus_report({}, None)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order_count"], 2)
        self.assertEqual(result["period"], "2026-08-01_to_2026-08-15")

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.bonus_report.app.EmailSender")
    @patch("src.orders.bonus_report.app.ReportDAO")
    @patch("src.orders.bonus_report.app.get_report_period")
    def test_no_orders_returns_zero_count_and_still_sends_email(
        self, mock_period, mock_dao_cls, mock_sender_cls
    ):
        from src.orders.bonus_report.app import generate_bonus_report

        mock_period.return_value = (
            "2026-08", "2026-08-01", "2026-08-15", "2026-08-01_to_2026-08-15"
        )
        mock_dao_cls.return_value.query_orders_by_creation_period.return_value = []
        mock_sender_cls.return_value.send_report.return_value = None

        result = generate_bonus_report({}, None)

        self.assertEqual(result["order_count"], 0)
        mock_sender_cls.return_value.send_report.assert_called_once()

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.bonus_report.app.get_report_period")
    def test_invalid_trigger_day_raises_exception(self, mock_period):
        from src.orders.bonus_report.app import generate_bonus_report

        mock_period.side_effect = ValueError("Report scheduled for day 1 or 16 only; got day 20")

        with self.assertRaises(ValueError):
            generate_bonus_report({}, None)

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.bonus_report.app.EmailSender")
    @patch("src.orders.bonus_report.app.ReportDAO")
    @patch("src.orders.bonus_report.app.get_report_period")
    def test_dao_queried_with_correct_period_args(
        self, mock_period, mock_dao_cls, mock_sender_cls
    ):
        from src.orders.bonus_report.app import generate_bonus_report

        mock_period.return_value = (
            "2026-07", "2026-07-16", "2026-07-31", "2026-07-16_to_2026-07-31"
        )
        mock_dao_cls.return_value.query_orders_by_creation_period.return_value = []
        mock_sender_cls.return_value.send_report.return_value = None

        generate_bonus_report({}, None)

        mock_dao_cls.return_value.query_orders_by_creation_period.assert_called_once_with(
            created_month="2026-07",
            start_date="2026-07-16",
            end_date="2026-07-31",
        )

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    @patch("src.orders.bonus_report.app.EmailSender")
    @patch("src.orders.bonus_report.app.ReportDAO")
    @patch("src.orders.bonus_report.app.get_report_period")
    def test_ses_error_propagates_as_exception(
        self, mock_period, mock_dao_cls, mock_sender_cls
    ):
        from src.orders.bonus_report.app import generate_bonus_report

        mock_period.return_value = (
            "2026-08", "2026-08-01", "2026-08-15", "2026-08-01_to_2026-08-15"
        )
        mock_dao_cls.return_value.query_orders_by_creation_period.return_value = []
        mock_sender_cls.return_value.send_report.side_effect = Exception("SES failure")

        with self.assertRaises(Exception) as ctx:
            generate_bonus_report({}, None)
        self.assertIn("SES failure", str(ctx.exception))
