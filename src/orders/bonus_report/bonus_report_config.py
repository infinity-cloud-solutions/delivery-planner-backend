import os

from dotenv import load_dotenv

load_dotenv()

environment = os.environ.get("APP_ENVIRONMENT", "local")

if environment.lower() in ("prod", "development", "uat", "qa", "local"):
    ORDERS_TABLE_NAME = "Orders"
else:
    raise NameError(f"No environment configured for: {environment}")

BONUS_REPORT_GSI_NAME = "CreatedMonthIndex"
REPORT_FROM_EMAIL = os.environ.get("REPORT_FROM_EMAIL", "noreply@hiberry.mx")
REPORT_RECIPIENTS = [
    r.strip()
    for r in os.environ.get(
        "REPORT_RECIPIENTS", "Evelyn@hiberry.mx,Omar@hiberry.mx"
    ).split(",")
    if r.strip()
]
