# Python's Libraries
import os

# Third-party Libraries
from aws_lambda_powertools import Logger


logger = Logger()
environment = os.environ.get('APP_ENVIRONMENT')
if environment is None:
    environment = "local"

logger.info(f"Starting with environment: {environment}")
ORDERS_PRIMARY_KEY = "delivery_date"

if environment.lower() == "prod":
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"

elif environment.lower() == "development":
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


elif environment.lower() == "uat":
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


elif environment.lower() == "qa":
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


elif environment.lower() == "local":
    ORDERS_TABLE_NAME = "Orders"


else:
    raise NameError("There is no environment configured!")
