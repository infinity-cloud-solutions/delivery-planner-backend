# Python's libraries
from typing import Dict
from typing import Any

# Own's modules
from product_modules.dao.product_dao import ProductDAO
from product_modules.models.product import HIBerryProduct, HIBerryProductUpdate
from product_modules.utils.doorman import DoormanUtil
from product_modules.errors.auth_error import AuthError
from product_modules.data_mapper.product_mapper import ProductHelper


# Third-party libraries
from pydantic.error_wrappers import ValidationError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


def create_product(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
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
    logger.info("Initializing Create Product function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError(f"User {username} is not authorized to create a product")

        body = doorman.get_body_from_request()

        logger.debug(f"Incoming data is {body=} and {username=}")

        new_product_data = HIBerryProduct(**body)

        logger.info(
            f"Processing product for: {new_product_data.name} with price {new_product_data.price}"
        )

        builder = ProductHelper()
        product_db_data = builder.build_product(
            product_data=new_product_data.__dict__, username=username
        )
        dao = ProductDAO()
        create_response = dao.create_product(product_db_data)

        if create_response["status"] == "success":
            logger.info("Product received and created")
            output_data = {"id": product_db_data["id"]}

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
        error_details = f"Error processing the product: {e}"
        logger.error(error_details, exc_info=True)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )


def get_all_products(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """This function is the entry point of this process that scan product table and return all the elements.

    :param event: Custom object that can come from an APIGateway.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the reponse from the lambda, it could be a 200, if the resources were found
    or >= 400 if theras was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Get All Products function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError(f"User {username} is not authorized to retrieve a product")

        logger.debug(f"Incoming data is {username=}")

        dao = ProductDAO()
        products = dao.fetch_products()
        output_data = products

        logger.debug(f"Outgoing data is {output_data=}")
        return doorman.build_response(payload=output_data, status_code=200)

    except AuthError as auth_error:
        error_details = f"Not authorized. {auth_error}"
        logger.error(error_details)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=403)

    except Exception as e:
        error_details = f"Error processing the request to fetch products: {e}"
        logger.error(error_details, exc_info=True)
        output_data = {"message": error_details}
        return doorman.build_response(payload=output_data, status_code=500)


def delete_product(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """This function is the entry point of this process that will receive a product name as an input
    and will attempt to delete the corresponding entry in DynamoDB.

    :param event: Custom object that can come from an APIGateway.
    :type event: Dict
    :param context: Regular lambda function context
    :type context: LambdaContext
    :return: Custom object with the response from the lambda, it could be a 200, if the product was deleted
    or >= 400 if there was an error
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Delete Product function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError(f"User {username} is not authorized to delete a product")

        product_name = doorman.get_query_param_from_request(
            _query_param_name="name", _is_required=True
        )

        logger.debug(f"Incoming data is {product_name=} and {username=}")

        dao = ProductDAO()
        delete_response = dao.delete_product(product_name)

        if delete_response["status"] == "success":
            return doorman.build_response(
                payload={"message": delete_response["message"]}, status_code=204
            )
        else:
            return doorman.build_response(
                payload={"message": delete_response["message"]},
                status_code=delete_response["status_code"],
            )

    except AuthError as auth_error:
        error_details = f"Not authorized. {auth_error}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the request to delete product: {e}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )


def update_product(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    This function is the entry point of the process that will receive a payload as an input
    and will attempt to update an existing product entry in DynamoDB.

    :param event: Custom object that can come from an APIGateway or EventBridge.
    :type event: Dict
    :param context: Regular lambda function context.
    :type context: LambdaContext
    :return: Custom object with the response from the lambda, it could be a 200 if the update was successful,
             or >= 400 if there was an error.
    :rtype: Dict
    """

    logger = Logger()
    logger.info("Initializing Update Product function")
    doorman = DoormanUtil(event, logger)

    try:
        username = doorman.get_username_from_context()
        is_auth = doorman.auth_user()
        if not is_auth:
            raise AuthError(f"User {username} is not authorized to update a product")

        body = doorman.get_body_from_request()

        logger.debug(f"Incoming data is {body=} and {username=}")

        updated_product_data = HIBerryProductUpdate(**body)
        builder = ProductHelper()
        product_db_data = builder.build_product(
            product_data=updated_product_data.__dict__, username=username
        )
        logger.info(f"Updating product: {updated_product_data.name}")

        dao = ProductDAO()
        update_response = dao.update_product(product_db_data)

        if update_response.get("status") == "success":
            return doorman.build_response(
                payload={"message": "Product updated successfully"},
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
        error_details = f"Error updating the product: {e}"
        logger.error(error_details, exc_info=True)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )
