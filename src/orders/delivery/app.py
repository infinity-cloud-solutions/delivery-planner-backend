# Python's libraries
from typing import Dict
from typing import Any
from datetime import datetime

# import json

# Own's modules
from delivery_modules.dao.order_dao import OrderDAO
from delivery_modules.processors.delivery_helpers import DeliveryProcessor
from delivery_modules.utils.doorman import DoormanUtil
from delivery_modules.errors.auth_error import AuthError
from delivery_modules.models.delivery import ScheduleRequestModel
from settings import ORDERS_PRIMARY_KEY

# Third-party libraries
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError


def set_delivery_schedule_order(
    event: Dict[str, Any], context: LambdaContext
) -> Dict[str, Any]:
    """This function will retrieve todays orders to generate an optimized path.

    :param event: Custom object that can come from an APIGateway, containing date field for delivery orders.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the reponse from the lambda, it could be a 200, if the resources were found
    or >= 400 if theras was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing set_delivery_schedule_order function")
    try:
        doorman = DoormanUtil(event, logger)
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError(f"User {username} is not authorized to schedule orders")
        body = doorman.get_body_from_request()

        logger.debug(f"Incoming data is {body=} and {username=}")

        schedule_orders = ScheduleRequestModel(**body)
        schedule_for_date = schedule_orders.date
        available_drivers = schedule_orders.available_drivers

        logger.info(f"Date to process: {schedule_for_date}")
        logger.info(
            f"Available drivers to process: {', '.join(map(str, available_drivers))}"
        )

        dao = OrderDAO()
        orders_for_today = dao.fetch_orders(
            primary_key=ORDERS_PRIMARY_KEY, query_value=schedule_for_date
        )
        orders_for_today = orders_for_today.get("payload", [])

        if len(orders_for_today) > 0:

            if len(available_drivers) == 1:
                available_driver = available_drivers[0]
                for order in orders_for_today:
                    order["driver"] = available_driver
                logger.info(
                    f"All orders have been assigned to the available driver: {available_driver}"
                )

            logger.info(
                f"Orders for today {schedule_for_date}: {len(orders_for_today)}"
            )
            scheduler = DeliveryProcessor()
            for driver_number in available_drivers:
                scheduler.process_records_for_driver(
                    driver_number, orders_for_today, dao
                )
        else:
            logger.warning("No orders to process today, check DB if this is ok")
        return doorman.build_response(
            payload={"message": "scheduling completed"}, status_code=200
        )

    except ValidationError as validation_error:
        error_details = f"Some fields failed validation: {validation_error.errors()}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=400
        )
    except AuthError as auth_error:
        error_details = f"Not authorized. {auth_error}"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=403)

    except Exception as e:
        error_details = f"Error processing the request to fetch orders: {e}"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=500)
