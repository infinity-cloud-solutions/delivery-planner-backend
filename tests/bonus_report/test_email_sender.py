from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.orders.bonus_report.bonus_report_modules.email_sender import EmailSender


class TestEmailSender(TestCase):

    def _make_sender(self):
        ses_mock = MagicMock()
        sender = EmailSender(from_email="noreply@hiberry.mx", ses_client=ses_mock)
        return sender, ses_mock

    def test_send_report_calls_ses_send_raw_email(self):
        sender, ses_mock = self._make_sender()
        sender.send_report(
            recipients=["Evelyn@hiberry.mx"],
            period_label="2026-08-01_to_2026-08-15",
            detail_csv="col1,col2\nval1,val2\n",
            summary_csv="col1,col2\nval1,val2\n",
        )
        ses_mock.send_raw_email.assert_called_once()

    def test_send_report_uses_correct_from_address(self):
        sender, ses_mock = self._make_sender()
        sender.send_report(
            recipients=["test@hiberry.mx"],
            period_label="2026-08-01_to_2026-08-15",
            detail_csv="",
            summary_csv="",
        )
        call_kwargs = ses_mock.send_raw_email.call_args[1]
        self.assertEqual(call_kwargs["Source"], "noreply@hiberry.mx")

    def test_send_report_includes_all_recipients_as_destinations(self):
        sender, ses_mock = self._make_sender()
        recipients = ["Evelyn@hiberry.mx", "Omar@hiberry.mx"]
        sender.send_report(
            recipients=recipients,
            period_label="2026-08-01_to_2026-08-15",
            detail_csv="",
            summary_csv="",
        )
        call_kwargs = ses_mock.send_raw_email.call_args[1]
        self.assertEqual(call_kwargs["Destinations"], recipients)

    def test_send_report_attaches_both_csv_files(self):
        sender, ses_mock = self._make_sender()
        sender.send_report(
            recipients=["test@hiberry.mx"],
            period_label="2026-08-01_to_2026-08-15",
            detail_csv="detail content",
            summary_csv="summary content",
        )
        call_kwargs = ses_mock.send_raw_email.call_args[1]
        raw_email = call_kwargs["RawMessage"]["Data"]
        self.assertIn("detalle_2026-08-01_to_2026-08-15.csv", raw_email)
        self.assertIn("resumen_2026-08-01_to_2026-08-15.csv", raw_email)

    def test_send_report_email_subject_contains_period(self):
        sender, ses_mock = self._make_sender()
        sender.send_report(
            recipients=["test@hiberry.mx"],
            period_label="2026-08-01_to_2026-08-15",
            detail_csv="",
            summary_csv="",
        )
        call_kwargs = ses_mock.send_raw_email.call_args[1]
        raw_email = call_kwargs["RawMessage"]["Data"]
        self.assertIn("2026-08-01", raw_email)
        self.assertIn("2026-08-15", raw_email)

    def test_send_report_propagates_ses_exception(self):
        sender, ses_mock = self._make_sender()
        ses_mock.send_raw_email.side_effect = Exception("SES error")
        with self.assertRaises(Exception) as ctx:
            sender.send_report(
                recipients=["test@hiberry.mx"],
                period_label="2026-08-01_to_2026-08-15",
                detail_csv="",
                summary_csv="",
            )
        self.assertIn("SES error", str(ctx.exception))
