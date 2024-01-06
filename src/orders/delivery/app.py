# Python's libraries
from typing import Dict
from typing import Any
from datetime import datetime

# import json

# Own's modules
from location_router import TravelPlanner
from delivery_modules.dao.order_dao import OrderDAO
from delivery_modules.processors.order_helpers import OrderProcessor
from delivery_modules.utils.doorman import DoormanUtil
from delivery_modules.errors.auth_error import AuthError

from settings import ORDERS_PRIMARY_KEY

# Third-party libraries
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


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
        username = doorman.get_username_from_token()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError("User is not allow to retrieve orders")
        body = doorman.get_body_from_request()
        schedule_for_date = body["date"]
        try:
            datetime.strptime(schedule_for_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Date format is not valid")
        logger.info(f"Date to process: {schedule_for_date}")

        dao = OrderDAO()
        orders_for_today = dao.fetch_orders(
            primary_key=ORDERS_PRIMARY_KEY, query_value=schedule_for_date
        )
        orders_for_today = orders_for_today.get("payload", [])

        if len(orders_for_today) > 0:
            logger.info(f"Orders for today {schedule_for_date}: {len(orders_for_today)}")
            processor = OrderProcessor()
            planner = TravelPlanner()

            morning_records = processor.select_orders_by_delivery_range_time(
                order_records=orders_for_today, delivery_time_to_match="8 AM - 1 PM"
            )
            if len(morning_records) > 0:
                logger.info(f"Records to schedule for 8 AM - 1 PM delivery: {len(morning_records)}")
                morning_starting_point = {
                    "latitude": 20.7257943,
                    "longitude": -103.3792193,
                }  # HiBerry offices geolocation
                morning_ordered_locations = planner.find_shortest_path(
                    morning_records, morning_starting_point
                )
                afternoon_starting_point = {
                    "latitude": morning_ordered_locations[-1]["latitude"],
                    "longitude": morning_ordered_locations[-1]["longitude"],
                }
                dao.bulk_update(morning_ordered_locations)

            else:
                afternoon_starting_point = {
                    "latitude": 20.7257943,
                    "longitude": -103.3792193,
                }  # HiBerry offices geolocation

            afternoon_records = processor.select_orders_by_delivery_range_time(
                order_records=orders_for_today, delivery_time_to_match="1 PM - 5 PM"
            )
            if len(afternoon_records) > 0:
                logger.info(f"Records to schedule for 1 PM - 5 PM delivery: {len(afternoon_records)}")
                afternoon_ordered_locations = planner.find_shortest_path(
                    afternoon_records, afternoon_starting_point
                )
                dao.bulk_update(afternoon_ordered_locations)
            output_data = {"message": "Records updated"}
        else:
            logger.warning("No orders to process today, check DB if this is ok")
        return doorman.build_response(payload=output_data, status_code=200)

    except AuthError:
        error_details = f"user {username} was not auth to fetch orders"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=403)

    except Exception as e:
        error_details = f"Error processing the request to fetch orders: {e}"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=500)
