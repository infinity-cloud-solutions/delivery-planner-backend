# Python's libraries
from typing import Dict
from typing import Any

# Own's modules
from client_modules.dao.client_dao import ClientDAO
from client_modules.models.client import HIBerryClient, HIBerryClientUpdate
from client_modules.utils.doorman import DoormanUtil
from client_modules.errors.auth_error import AuthError
from client_modules.data_mapper.client_mapper import ClientHelper


# Third-party libraries
from pydantic.error_wrappers import ValidationError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


def create_client(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """This function is the entry point of this process that wil receive a payload as an input
    an will attempt to create an entry in DynamoDB.

    :param event: Custom object that can come from an APIGateway
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the reponse from the lambda, it could be a 201, if the resource was created
    or >= 400 if theras was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Create Client function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError(f"User {username} is not authorized to create a client")

        body = doorman.get_body_from_request()

        logger.debug(f"Incoming data is {body=} and {username=}")

        new_client_data = HIBerryClient(**body)

        logger.info(f"Processing client with phone: {new_client_data.phone_number}")

        builder = ClientHelper(new_client_data.model_dump())
        client_db_data = builder.build_client(username=username)

        dao = ClientDAO()
        create_response = dao.create_client(client_db_data)

        if create_response["status"] == "success":
            logger.info("Client data received and created")
            output_data = {
                "address_latitude": client_db_data["address_latitude"],
                "address_longitude": client_db_data["address_longitude"],
                "second_address_latitude": client_db_data["second_address_latitude"],
                "second_address_longitude": client_db_data["second_address_longitude"],
                "errors": client_db_data["errors"],
            }

            logger.debug(f"Outgoing data is {output_data=}")
            return doorman.build_response(payload=output_data, status_code=201)
        else:
            return doorman.build_response(
                payload={"message": create_response["message"]},
                status_code=create_response.get("status_code", 500),
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
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the client: {e}"
        logger.error(error_details, exc_info=True)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )


def update_client(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    This function is the entry point of the process that will receive a payload as an input
    and will attempt to update an existing client entry in DynamoDB.

    :param event: Custom object that can come from an APIGateway or EventBridge.
    :type event: Dict
    :param context: Regular lambda function context.
    :type context: LambdaContext
    :return: Custom object with the response from the lambda, it could be a 200 if the update was successful,
             or >= 400 if there was an error.
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Update Client function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if not is_auth:
            raise AuthError(f"User {username} is not authorized to update a client")

        body = doorman.get_body_from_request()

        logger.debug(f"Incoming data is {body=} and {username=}")

        updated_client_data = HIBerryClientUpdate(**body)
        builder = ClientHelper(updated_client_data.model_dump())
        client_db_data = builder.build_client(username=username)
        logger.info(f"Updating client with phone: {updated_client_data.phone_number}")

        dao = ClientDAO()
        update_response = dao.update_client(client_db_data)

        if update_response.get("status") == "success":
            logger.info("Client data received and updated")
            output_data = {
                "address_latitude": client_db_data["address_latitude"],
                "address_longitude": client_db_data["address_longitude"],
                "second_address_latitude": client_db_data["second_address_latitude"],
                "second_address_longitude": client_db_data["second_address_longitude"],
                "errors": client_db_data["errors"],
            }

            logger.debug(f"Outgoing data is {output_data=}")
            return doorman.build_response(
                payload=output_data,
                status_code=update_response["status_code"],
            )
        else:
            return doorman.build_response(
                payload={"message": update_response.get("message", "Update failed")},
                status_code=update_response.get("status_code", 500),
            )

    except ValidationError as validation_error:
        error_details = "Some fields failed validation: " + str(validation_error)
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=400
        )

    except AuthError as auth_error:
        error_details = str(auth_error)
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error updating the client: {e}"
        logger.error(error_details, exc_info=True)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )
