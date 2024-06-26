# Python's libraries
from typing import Dict
from typing import Any

# Own's modules
from client_modules.dao.client_dao import ClientDAO
from client_modules.models.client import HIBerryClient, HIBerryClientUpdate
from client_modules.utils.doorman import DoormanUtil
from client_modules.errors.auth_error import AuthError
from client_modules.data_mapper.client_mapper import ClientHelper
import settings


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

        if (
            updated_client_data.original_phone_number != updated_client_data.phone_number
        ) and (updated_client_data.delete_old_record):
            delete_response = dao.delete_client(
                phone_number=updated_client_data.original_phone_number
            )
            if delete_response["status"] != "success":
                logger.error(f"Error deleting client: {delete_response['message']}")
                return doorman.build_response(
                    payload={"message": delete_response["message"]},
                    status_code=delete_response.get("status_code", 500),
                )

            logger.info(
                f"Client with phone number {updated_client_data.original_phone_number} was delete"
            )

        logger.info(
            f"Updating client for: {updated_client_data.phone_number} phone_number"
        )
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


def retrieve_client(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """This function is the entry point of this process that queries clients table and return the data related to the phone number.

    :param event: Custom object that can come from an APIGateway.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the reponse from the lambda, it could be a 200, if the resources were found
    or >= 400 if theras was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Get Clients By Id function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError(f"User {username} is not authorized to retrieve clients")

        phone_number = doorman.get_query_param_from_request(
            _query_param_name="phone_number", _is_required=True
        )

        logger.debug(f"Incoming data is {phone_number} and {username}")

        dao = ClientDAO()
        client = dao.fetch_client(
            primary_key=settings.CLIENTS_PRIMARY_KEY, query_value=phone_number
        )
        output_data = client["payload"]
        logger.debug(f"Outgoing data is {output_data}")

        return doorman.build_response(payload=output_data, status_code=200)

    except AuthError as auth_error:
        error_details = f"Not authorized. {auth_error}"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=403)

    except Exception as e:
        error_details = f"Error processing the request to fetch client: {e}"
        logger.error(error_details, exc_info=True)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=500)


def delete_client(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    This function is the entry point of the process that will receive an order ID and delivery date
    as input and will attempt to delete the corresponding entry in the DynamoDB table.
    :param event: Custom object that can come from an API Gateway.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the response from the lambda, it could be a 200 if the deletion was successful
    or >= 400 if there was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Delete Client function")
    try:
        doorman = DoormanUtil(event, logger)
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if not is_auth:
            raise AuthError("User is not allowed to delete client")

        phone_number = doorman.get_query_param_from_request(
            _query_param_name="phone_number", _is_required=True
        )

        logger.debug(f"Incoming data is {phone_number} and {username=}")

        dao = ClientDAO()
        delete_response = dao.delete_client(phone_number=phone_number)

        if delete_response["status"] == "success":
            logger.info(f"Client with phone number {phone_number} was delete")
            return doorman.build_response(
                payload={"message": delete_response["message"]}, status_code=204
            )
        else:
            logger.error(f"Error deleting client: {delete_response['message']}")
            return doorman.build_response(
                payload={"message": delete_response["message"]},
                status_code=delete_response.get("status_code", 500),
            )

    except ValidationError as validation_error:
        error_details = f"Some fields failed validation: {validation_error.errors()}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=400
        )
    except AuthError:
        error_details = f"user {username} was not authorized to delete clients"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the request to delete client: {e}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )
