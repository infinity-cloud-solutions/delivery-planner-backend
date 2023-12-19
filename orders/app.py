# Python's libraries
from typing import Dict
from typing import Any
import json

# Own's modules
from src.dao.order_dao import OrderDAO
from src.data_access.geolocation_handler import Geolocation
from src.data_mapper.order_mapper import OrderHelper
from src.models.order import HIBerryOrder
from src.utils.doorman import DoormanUtil
from src.errors.auth_error import AuthError


# Third-party libraries
from pydantic.error_wrappers import ValidationError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """This function is the entry point of this process that wil receive a payload as an input
    an will attempt to create an entry in DynamoDB.

    :param event: Custom object that can come from an APIGateway or EventBridge, depending if its
    used by the frontend or the Shopify integration.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the reponse from the lambda, it could be a 201, if the resource was created
    or >= 400 if theras was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Create Order function")
    try:
        doorman = DoormanUtil(event, logger)
        username = doorman.get_username_from_token()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError("User is not allow to create a new order")
        order_errors = []

        body = doorman.get_body_from_request()
        new_order_data = HIBerryOrder(**body)

        logger.info(
            f"Processing order for: {new_order_data.client_name} at {new_order_data.delivery_address}"
        )
        location_service = Geolocation()
        lat_and_long = location_service.get_lat_and_long_from_street_address(
            str_address=new_order_data.delivery_address
        )

        if lat_and_long is None:
            order_errors.append(
                {
                    "code": "ADDRESS_NEEDS_GEO",
                    "value": "Order requires geolocation coordinates to be updated manually",
                }
            )

        # ToDo validate Shopify order price vs owns price
        builder = OrderHelper()
        order_db_data = builder.build_order(
            order_data=new_order_data.__dict__,
            username=username,
            geolocation=lat_and_long,
            errors=order_errors,
        )
        dao = OrderDAO()
        dao.create_order(order_db_data)
        logger.info("Order received and created")
        return doorman.build_response(
            payload={"message": "Record was created"}, status_code=201
        )

    except ValidationError as validation_error:
        error_details = "Some fields failed validation"
        if validation_error.error_cache:
            error_details = str(validation_error._error_cache)
        return doorman.build_response(
            payload={"message": error_details}, status_code=400
        )

    except AuthError:
        logger.error(f"user {username} was not auth to create a new order")
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        logger.error(f"Error processing the order: {str(e)}")
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )


data = {
    "client_name": "Test User",
    "delivery_date": "2023-12-20",
    "delivery_time": "9-1",
    "delivery_address": "Aurelio Ortega 2699-A, Colonia Jardines Seattle, Zapopan, Jalisco, 45150",
    "phone_number": "3312721289",
    "cart_items": [{"name": "Berry", "quantity": 2, "price": 10}, {"name": "Mango", "quantity": 5, "price": 20}],
    "total_amount": 150.00,
    "payment_method": "cash"
}

lambda_handler({"body": json.dumps(data)}, None)
