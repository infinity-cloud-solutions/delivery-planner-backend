import email.mime.base
import email.mime.multipart
import email.mime.text
from typing import List

import boto3
from aws_lambda_powertools import Logger


class EmailSender:
    """Sends the bonus report as two CSV attachments via Amazon SES."""

    def __init__(self, from_email: str, ses_client=None):
        self.from_email = from_email
        self.logger = Logger()
        self.ses_client = ses_client or boto3.client("ses", region_name="us-east-1")

    def send_report(
        self,
        recipients: List[str],
        period_label: str,
        detail_csv: str,
        summary_csv: str,
    ) -> None:
        readable_period = period_label.replace("_", " ")

        msg = email.mime.multipart.MIMEMultipart()
        msg["Subject"] = f"Reporte de Bonos — Periodo {readable_period}"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(recipients)

        body = (
            f"Estimado equipo,\n\n"
            f"Adjunto encontrarán el reporte de bonos del período {readable_period}.\n\n"
            f"  • detalle_{period_label}.csv — listado completo de órdenes creadas.\n"
            f"  • resumen_{period_label}.csv — totales por vendedor y por producto.\n\n"
            f"Saludos."
        )
        msg.attach(email.mime.text.MIMEText(body, "plain", "utf-8"))

        for content, filename in (
            (detail_csv, f"detalle_{period_label}.csv"),
            (summary_csv, f"resumen_{period_label}.csv"),
        ):
            attachment = email.mime.base.MIMEBase("text", "csv", charset="utf-8")
            attachment.set_payload(content.encode("utf-8"))
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            msg.attach(attachment)

        self.ses_client.send_raw_email(
            Source=self.from_email,
            Destinations=recipients,
            RawMessage={"Data": msg.as_string()},
        )
        self.logger.info(
            f"Bonus report email sent to {recipients} for period {period_label}"
        )
