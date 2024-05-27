# Python's Libraries
import os

environment = os.environ.get("APP_ENVIRONMENT", "local")
CLIENTS_TABLE_NAME = "Clients"
CLIENTS_PRIMARY_KEY = "phone_number"
