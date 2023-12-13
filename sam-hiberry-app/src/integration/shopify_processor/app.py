import json
import os
import requests
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from processor import process_shopify_event
from exceptions import ConfigurationError

# Initialize logging
logger = Logger()

CREATE_ORDER_API_URL = os.getenv('CREATE_ORDER_API_URL', None)
if CREATE_ORDER_API_URL is None:
    error_message = "Environment variable not configured: CREATE_ORDER_API_URL"
    logger.error(error_message)
    raise ConfigurationError(error_message)

def lambda_handler(event: dict, context: LambdaContext):
    """
    Handler function for AWS Lambda to process Shopify order/create events.

    This function is triggered by an AWS EventBridge rule that listens for specific
    events from Shopify (e.g., order creation). It processes these events and sends
    the relevant order information to the 'CreateOrderFunction' for further handling.

    Returns: 
    No specific return. Because of async invoke, the value is discarded.

    """
    try:
        logger.info(f"Shopify event:{json.dumps(event)}")

        # Extract Shopify webhook data
        shopify_data = event['detail']['payload']

        order_data = process_shopify_event(shopify_data)

        # Send data to the CreateOrderFunction API
        logger.info(
            f"Calling create order api with payload: {json.dumps(order_data)}")
        
        response = requests.post(CREATE_ORDER_API_URL, json=order_data)
        response.raise_for_status()

        logger.info(f"Response : {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error while sending request to create order: {str(e)}")
        logger.error(f"Error event: {event}")
        raise
    except Exception as e:
        logger.error(f"Error processing the event: {str(e)}")
        logger.error(f"Error event: {event}")
        raise