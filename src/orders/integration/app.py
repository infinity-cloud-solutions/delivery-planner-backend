import json
import os
import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.parser.envelopes import EventBridgeEnvelope

from exceptions import ConfigurationError
from data_mapper import ShopifyDataMapper
from models import ShopifyPayload

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
        logger.info("Initializing Shopify Order Integration function")

        #logger.info(f"Shopify event:{json.dumps(event)}")

        # Extract Shopify event data
        shopify_payload : ShopifyPayload = parse(event=event, model=ShopifyPayload, envelope=EventBridgeEnvelope)

        # Map order fields
        shopify_mapper = ShopifyDataMapper()
        order_data = shopify_mapper.map_order_data(shopify_payload.payload)

        # # Send data to the CreateOrderFunction API
        logger.info(
             f"Calling create order api with payload: {order_data}")
        
        response = requests.post(CREATE_ORDER_API_URL, json=order_data)
        response.raise_for_status()

        logger.info(f"Create order api response : {response.status_code}")
        
    except ValidationError as e:
        logger.error(e)
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error while sending request to create order: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error processing the event: {str(e)}")
        raise