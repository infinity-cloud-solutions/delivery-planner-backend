from typing import Any, Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from bonus_report_modules.dao.report_dao import ReportDAO
from bonus_report_modules.email_sender import EmailSender
from bonus_report_modules.report_generator import (
    build_detail_csv,
    build_summary_csv,
    get_report_period,
)
from bonus_report_config import (
    BONUS_REPORT_GSI_NAME,
    ORDERS_TABLE_NAME,
    REPORT_FROM_EMAIL,
    REPORT_RECIPIENTS,
)


def generate_bonus_report(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Entry point triggered by EventBridge Scheduler on the 1st and 16th of each month.

    Queries orders created in the preceding period, builds two CSVs (detail + summary),
    and emails them to the configured recipients via SES.
    """
    logger = Logger()
    logger.info("Starting bonus report generation")

    try:
        created_month, start_date, end_date, period_label = get_report_period()
        logger.info(f"Generating report for period: {period_label}")

        dao = ReportDAO(
            table_name=ORDERS_TABLE_NAME,
            index_name=BONUS_REPORT_GSI_NAME,
        )
        orders = dao.query_orders_by_creation_period(
            created_month=created_month,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Found {len(orders)} orders for the period")

        detail_csv = build_detail_csv(orders)
        summary_csv = build_summary_csv(orders)

        sender = EmailSender(from_email=REPORT_FROM_EMAIL)
        sender.send_report(
            recipients=REPORT_RECIPIENTS,
            period_label=period_label,
            detail_csv=detail_csv,
            summary_csv=summary_csv,
        )

        return {
            "status": "success",
            "period": period_label,
            "order_count": len(orders),
        }

    except Exception as exc:
        logger.error(f"Failed to generate bonus report: {exc}", exc_info=True)
        raise
