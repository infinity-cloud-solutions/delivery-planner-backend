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
ORDERS_PRIMARY_KEY = "delivery_date"

if environment.lower() == "prod":
    CREATE_ORDER_ENDPOINT = "TODO"
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"

elif environment.lower() == "development":
    CREATE_ORDER_ENDPOINT = "TODO"
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


elif environment.lower() == "uat":
    CREATE_ORDER_ENDPOINT = "TODO"
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


elif environment.lower() == "qa":
    CREATE_ORDER_ENDPOINT = "TODO"
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


elif environment.lower() == "local":
    CREATE_ORDER_ENDPOINT = "TODO"
    ORDERS_TABLE_NAME = "Orders"
    PRODUCTS_TABLE_NAME = "Products"


else:
    raise NameError("There is no environment configured!")
