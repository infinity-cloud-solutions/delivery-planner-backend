# Python's libraries
from typing import Dict
from typing import Any

# Own's modules
from product_modules.dao.product_dao import ProductDAO
from product_modules.models.product import HIBerryProduct
from product_modules.utils.doorman import DoormanUtil
from product_modules.errors.auth_error import AuthError
from product_modules.data_mapper.product_mapper import ProductHelper


# Third-party libraries
from pydantic.error_wrappers import ValidationError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


def creat_product(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
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
    try:
        doorman = DoormanUtil(event, logger)
        username = doorman.get_username_from_token()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError("User is not allow to create a new product")

        body = doorman.get_body_from_request()
        new_product_data = HIBerryProduct(**body)

        logger.info(
            f"Processing product for: {new_product_data.name} with price {new_product_data.price}"
        )

        builder = ProductHelper()
        product_db_data = builder.build_product(
            product_data=new_product_data.__dict__,
            username=username
        )
        dao = ProductDAO()
        dao.create_product(product_db_data)
        logger.info("Product received and created")
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
        error_details = f"user {username} was not auth to create a new product"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the product: {e}"
        logger.error(error_details)
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
    try:
        doorman = DoormanUtil(event, logger)
        username = doorman.get_username_from_token()
        is_auth = doorman.auth_user()
        if is_auth is False:
            raise AuthError("User is not allow to retrieve products")

        dao = ProductDAO()
        products = dao.fetch_products()
        logger.info(f"{len(products)} products were fetched")
        return doorman.build_response(
            payload={"message": "Record was created", "data": products}, status_code=200
        )

    except AuthError:
        error_details = f"user {username} was not auth to create a fetch products"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=403
        )

    except Exception as e:
        error_details = f"Error processing the request to fetch products: {e}"
        logger.error(error_details)
        return doorman.build_response(
            payload={"message": error_details}, status_code=500
        )
