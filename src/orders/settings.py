# Python's Libraries
import os

# Third-party Libraries
from dotenv import load_dotenv
from aws_lambda_powertools import Logger


load_dotenv()
logger = Logger()
environment = os.environ.get('APP_ENVIRONMENT')
if environment is None:
    environment = "local"

logger.info(f"Starting with environment: {environment}")

if environment.lower() == "prod":
    ORDERS_TABLE_NAME = "Orders"

elif environment.lower() == "development":
    ORDERS_TABLE_NAME = "Orders"


elif environment.lower() == "uat":
    ORDERS_TABLE_NAME = "Orders"


elif environment.lower() == "qa":
    ORDERS_TABLE_NAME = "Orders"


elif environment.lower() == "local":
    ORDERS_TABLE_NAME = "Orders"


else:
    raise NameError("There is no environment configured!")
