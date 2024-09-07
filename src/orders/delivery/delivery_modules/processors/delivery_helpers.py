# Python's libraries

# Own's modules
from location_router import TravelPlanner
from delivery_modules.processors.order_helpers import OrderProcessor

# Third-party libraries
from aws_lambda_powertools import Logger

import time


class DeliveryProcessor:

    def process_records_for_driver(self, driver_number, orders_for_today, dao):
        logger = Logger()
        processor = OrderProcessor()
        planner = TravelPlanner()
        logger.info(f"Processing records for driver {driver_number}")
        morning_records = processor.select_orders_by_delivery_range_time(
            order_records=orders_for_today,
            delivery_time_to_match="9 AM - 1 PM",
            driver_to_match=driver_number,
        )
        if len(morning_records) > 0:
            logger.info(
                f"Records to schedule for 9 AM - 1 PM delivery for Driver {driver_number}: {len(morning_records)}"
            )
            morning_starting_point = {
                "latitude": 20.7257943,
                "longitude": -103.3792193,
            }  # HiBerry offices geolocation
            start_time = time.time()
            logger.info(
                f"started shrotes path at {start_time}"
            )
            morning_ordered_locations = planner.find_shortest_path(
                morning_records, morning_starting_point
            )
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Execution time: {execution_time} seconds")
            afternoon_starting_point = {
                "latitude": morning_ordered_locations[-1]["latitude"],
                "longitude": morning_ordered_locations[-1]["longitude"],
            }
            dao.bulk_update(morning_ordered_locations)
            logger.info(f"Driver {driver_number} records scheduled for morning shift")
        else:
            afternoon_starting_point = {
                "latitude": 20.7257943,
                "longitude": -103.3792193,
            }  # HiBerry offices geolocation

        afternoon_records = processor.select_orders_by_delivery_range_time(
            order_records=orders_for_today,
            delivery_time_to_match="1 PM - 5 PM",
            driver_to_match=driver_number,
        )
        if len(afternoon_records) > 0:
            logger.info(
                f"Records to schedule for 1 PM - 5 PM delivery for Driver {driver_number}: {len(afternoon_records)}"
            )
            afternoon_ordered_locations = planner.find_shortest_path(
                afternoon_records, afternoon_starting_point
            )
            dao.bulk_update(afternoon_ordered_locations)
            logger.info(f"Driver {driver_number} records scheduled for afternoon shift")
