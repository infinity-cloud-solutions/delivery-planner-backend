# Python's libraries
from typing import Dict
from typing import Any
# import json

# Own's modules
from order_modules.dao.order_dao import OrderDAO
from order_modules.data_access.geolocation_handler import Geolocation
from order_modules.data_mapper.order_mapper import OrderHelper
from order_modules.models.order import HIBerryOrder
from order_modules.utils.doorman import DoormanUtil
from order_modules.errors.auth_error import AuthError


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
        if validation_error._error_cache:
            error_details = str(validation_error._error_cache)
        return doorman.build_response(
            payload={"message": error_details}, status_code=400
        )

    except AuthError:
        error_details = f"user {username} was not auth to create a new order"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the order: {e}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )
