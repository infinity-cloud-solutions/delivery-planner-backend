import json
import os

from exceptions import ConfigurationError, StorePickupNotAllowed
from data_mapper import ShopifyDataMapper
from models import ShopifyPayload

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.parser.envelopes import EventBridgeEnvelope
from botocore.exceptions import ClientError


# Initialize logging
logger = Logger()

def lambda_handler(event: dict, context: LambdaContext):
    """
    Handler function for AWS Lambda to process Shopify order/create events.

    This function is triggered by an AWS EventBridge rule that listens for specific
    events from Shopify (e.g., order creation). It processes these events and sends
    the relevant order information to the 'CreateOrderFunction' for further handling.

    Returns: 
    No specific return. Because of async invoke, the value is discarded.

    """
    CREATE_ORDER_FUNCTION_NAME = os.getenv('CREATE_ORDER_FUNCTION_NAME')
    if CREATE_ORDER_FUNCTION_NAME is None:
        error_message = "Environment variable not configured: CREATE_ORDER_FUNCTION_NAME"
        logger.error(error_message)
        raise ConfigurationError(error_message)
        
    try:
        logger.info("Initializing Shopify Order Integration function")

        # Extract Shopify event data
        shopify_payload: ShopifyPayload = parse(
            event=event, model=ShopifyPayload, envelope=EventBridgeEnvelope)

        # Map order fields
        shopify_mapper = ShopifyDataMapper(shopify_payload.payload)
        order_data = shopify_mapper.map_order_data()

        # Send data to the CreateOrderFunction API
        logger.info(
            f"Calling {CREATE_ORDER_FUNCTION_NAME} with payload: {order_data}")

        # Invoke the CreateOrderFunction directly
        lambda_client = boto3.client('lambda')

        response = lambda_client.invoke(
            FunctionName=CREATE_ORDER_FUNCTION_NAME,
            InvocationType='RequestResponse',  # Use 'Event' for async
            Payload=json.dumps(order_data),
        )

        response_payload = json.loads(
            response['Payload'].read().decode("utf-8"))

        status_code = response_payload.get("statusCode")
        body_str = response_payload.get("body")
        body = json.loads(body_str) if body_str else {}
        message = body.get("message", "No message provided")

        if status_code >= 400:
            logger.error(
                f"Create order function returned error {status_code=}, {message=} ")
        else:
            logger.info(f"Order created.")

    except StorePickupNotAllowed as order_error:
        logger.error(f"Store pickup not allowed for this app: {str(order_error)}")

    except ValidationError as validation_error:
        logger.error(f"Validation error ocurred: {validation_error.errors()}")

    except ClientError as boto_error:
        logger.error(f"Boto3 Client Error: {str(boto_error)}")
        raise
        
    except Exception as e:
        logger.error(f"Error processing the event: {str(e)}")
        raise
