import os
import requests

from exceptions import ConfigurationError, StorePickupNotAllowed
from data_mapper import ShopifyDataMapper
from models import ShopifyPayload

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.parser.envelopes import EventBridgeEnvelope


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

        # Extract Shopify event data
        shopify_payload: ShopifyPayload = parse(
            event=event, model=ShopifyPayload, envelope=EventBridgeEnvelope)

        # Map order fields
        shopify_mapper = ShopifyDataMapper()
        order_data = shopify_mapper.map_order_data(shopify_payload.payload)

        # Send data to the CreateOrderFunction API
        logger.info(
            f"Calling create order api with payload: {order_data}")

        response = requests.post(CREATE_ORDER_API_URL, json=order_data)
        response.raise_for_status()

        logger.info(f"Successful create order api response : {response.status_code}")

    except StorePickupNotAllowed as e:
        logger.error(f"Store pickup not allowed for this app: {str(e)}")

    except ValidationError as e:
        logger.error(f"Validation error ocurred: {e.errors()}")
        
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP error occurred: {str(e)}"
        logger.error(error_message)
        logger.error(f"Response Body: {e.response.text}")
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {str(e)}")
        raise
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error occurred: {str(e)}")
        raise
    
    except requests.exceptions.RequestException as e:
        error_message = f"Error while sending request to create order: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f"; Response Body: {e.response.text}"
        logger.error(error_message)

    except Exception as e:
        logger.error(f"Error processing the event: {str(e)}")
        raise
