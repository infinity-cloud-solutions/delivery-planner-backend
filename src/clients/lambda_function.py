# Python's libraries
from typing import Dict
from typing import Any

# Own's modules
from client_modules.dao.client_dao import ClientDAO
from client_modules.models.client import HIBerryClient
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

        logger.info(
            f"Processing client with phone: {new_client_data.phone_number} and address {new_client_data.address}"
        )

        builder = ClientHelper(new_client_data.model_dump())
        client_db_data = builder.build_client(username=username)

        dao = ClientDAO()
        create_response = dao.create_client(client_db_data)

        if create_response["status"] == "success":
            logger.info("Client data received and created")
            output_data = {
                "latitude": client_db_data["latitude"],
                "longitude": client_db_data["longitude"],
                "errors": client_db_data["errors"]
            }

            logger.debug(f"Outgoing data is {output_data=}")
            return doorman.build_response(payload=output_data, status_code=201)
        else:
            return doorman.build_response(
                payload={"message": create_response["message"]},
                status_code=create_response.get("status_code", 500),
            )
    except ValidationError as validation_error:
        error_details = "Some fields failed validation"
        if validation_error._error_cache:
            error_details = str(validation_error._error_cache)
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
