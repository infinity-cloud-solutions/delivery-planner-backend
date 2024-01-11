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
from order_modules.errors.business_error import BusinessError

from settings import ORDERS_PRIMARY_KEY

# Third-party libraries
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


def create_order(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
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
        lat_and_long = None
        if new_order_data.geolocation is None:
            logger.info("Input did not include geolocation data, invoking Geolocaction Service")
            location_service = Geolocation()
            lat_and_long = location_service.get_lat_and_long_from_street_address(
                str_address=new_order_data.delivery_address
            )
        else:
            logger.info("Reading geolocation data from input")
            lat_and_long = new_order_data.geolocation.__dict__
            # lat_and_long = None

        if lat_and_long is None:
            logger.info("Geolocation Data is missing, adding to the list of errors")
            order_errors.append(
                {
                    "code": "ADDRESS_NEEDS_GEO",
                    "value": "Order requires geolocation coordinates to be updated manually",
                }
            )
            lat_and_long = {}

        # ToDo validate Shopify order price vs owns price
        builder = OrderHelper()
        order_db_data = builder.build_order(
            order_data=new_order_data.__dict__,
            username=username,
            geolocation=lat_and_long,
            errors=order_errors,
        )
        dao = OrderDAO()
        order_created = dao.create_order(order_db_data)
        assigned_driver = order_created['payload']['driver']
        logger.info(f"Order received and created with status {order_db_data['status']} and for driver {assigned_driver}")
        output_data = {"status": order_db_data["status"], "assigned_driver": assigned_driver}
        return doorman.build_response(
            payload=output_data, status_code=201
        )

    except ValidationError as validation_error:
        error_details = f"Some fields failed validation: {validation_error.errors()}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=400
        )

    except BusinessError as business_error:
        error_details = f"Order could not be processed due: {business_error}"
        logger.error(error_details)
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


def retrieve_orders(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """This function is the entry point of this process that queries orders table and return all the elements for specific date.

    :param event: Custom object that can come from an APIGateway.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the reponse from the lambda, it could be a 200, if the resources were found
    or >= 400 if theras was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Get All Orders function")
    try:
        doorman = DoormanUtil(event, logger)
        username = doorman.get_username_from_token()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError("User is not allow to retrieve orders")

        filter_date = doorman.get_query_param_from_request(
            _query_param_name="date",
            _is_required=True
        )
        dao = OrderDAO()
        orders = dao.fetch_orders(
            primary_key=ORDERS_PRIMARY_KEY,
            query_value=filter_date
        )
        output_data = orders["payload"]
        return doorman.build_response(
            payload=output_data, status_code=200
        )

    except AuthError:
        error_details = f"user {username} was not auth to fetch orders"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(
            payload=output_data, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the request to fetch orders: {e}"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(
            payload=output_data, status_code=500
        )
