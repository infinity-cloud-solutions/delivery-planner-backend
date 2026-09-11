"""
Runs the bonus report pipeline locally against the real deployed dev resources
(Orders table + SES), without waiting for the actual 1st/16th-of-month schedule.

generate_bonus_report() in bonus_report/app.py calls get_report_period() with no
args, which raises ValueError unless the real server date is day 1 or 16
(see report_generator.py:29-32). This script reproduces the same steps but calls
get_report_period(today=...) directly with an overridden date, so you can validate
today. Seed data first with seed_bonus_report_orders.py (period: 2026-09-01..15).

Usage:
    python scripts/local_invoke_bonus_report.py --profile default
    python scripts/local_invoke_bonus_report.py --profile default --day 2026-10-01  # tests the other half
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

MX_OFFSET = timezone(timedelta(hours=-6))

parser = argparse.ArgumentParser()
parser.add_argument("--profile", default="default")
parser.add_argument(
    "--day",
    default="2026-09-16",
    help="Date to pretend 'today' is (must be the 1st or 16th). Default reports Sept 1-15.",
)
args = parser.parse_args()

# Point boto3 at the right AWS account before any client gets constructed.
os.environ["AWS_PROFILE"] = args.profile

# Match the verified sandbox identities from samconfig.toml's default stage.
os.environ.setdefault("REPORT_FROM_EMAIL", "mailbot.marcoburgos@gmail.com")
os.environ.setdefault("REPORT_RECIPIENTS", "marko.burgos@gmail.com")
os.environ.setdefault("APP_ENVIRONMENT", "local")

BONUS_REPORT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "orders", "bonus_report"
)
sys.path.insert(0, os.path.abspath(BONUS_REPORT_DIR))

from bonus_report_config import BONUS_REPORT_GSI_NAME  # noqa: E402
from bonus_report_config import (  # noqa: E402
    ORDERS_TABLE_NAME, REPORT_FROM_EMAIL, REPORT_RECIPIENTS)
from bonus_report_modules.dao.report_dao import ReportDAO  # noqa: E402
from bonus_report_modules.email_sender import EmailSender  # noqa: E402
from bonus_report_modules.report_generator import (  # noqa: E402
    build_detail_csv, build_summary_csv, get_report_period)

fake_today = datetime.strptime(args.day, "%Y-%m-%d").replace(tzinfo=MX_OFFSET)

created_month, start_date, end_date, period_label = get_report_period(today=fake_today)
print(f"Simulated 'today': {args.day}")
print(f"Report period: {period_label} (created_month={created_month})")

dao = ReportDAO(table_name=ORDERS_TABLE_NAME, index_name=BONUS_REPORT_GSI_NAME)
orders = dao.query_orders_by_creation_period(
    created_month=created_month,
    start_date=start_date,
    end_date=end_date,
)
print(f"Found {len(orders)} orders for the period")

detail_csv = build_detail_csv(orders)
summary_csv = build_summary_csv(orders)

print("\n--- detail.csv ---")
print(detail_csv)
print("--- summary.csv ---")
print(summary_csv)

sender = EmailSender(from_email=REPORT_FROM_EMAIL)
sender.send_report(
    recipients=REPORT_RECIPIENTS,
    period_label=period_label,
    detail_csv=detail_csv,
    summary_csv=summary_csv,
)
print(f"\nEmail sent from {REPORT_FROM_EMAIL} to {REPORT_RECIPIENTS}")
