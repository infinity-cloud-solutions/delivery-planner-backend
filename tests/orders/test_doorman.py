import json
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from order_modules.errors.auth_error import AuthError
from order_modules.errors.util_error import UtilError

from src.orders.order_modules.utils.doorman import DoormanUtil


class TestDoormanGetBodyFromRequest(TestCase):

    def test_raises_when_no_body_key(self):
        doorman = DoormanUtil({})
        with self.assertRaises(UtilError):
            doorman.get_body_from_request()

    def test_raises_when_body_is_none(self):
        doorman = DoormanUtil({"body": None})
        with self.assertRaises(UtilError):
            doorman.get_body_from_request()

    def test_returns_dict_body_directly(self):
        body = {"key": "value"}
        doorman = DoormanUtil({"body": body})
        result = doorman.get_body_from_request()
        self.assertEqual(result, body)

    def test_parses_json_string_body(self):
        body = {"key": "value"}
        doorman = DoormanUtil({"body": json.dumps(body)})
        result = doorman.get_body_from_request()
        self.assertEqual(result, body)

    def test_raises_on_invalid_json_string(self):
        doorman = DoormanUtil({"body": "not-json"})
        with self.assertRaises(UtilError):
            doorman.get_body_from_request()


class TestDoormanGetQueryParam(TestCase):

    def test_raises_when_no_querystring_and_required(self):
        doorman = DoormanUtil({})
        with self.assertRaises(UtilError):
            doorman.get_query_param_from_request("date", _is_required=True)

    def test_returns_none_when_no_querystring_and_not_required(self):
        doorman = DoormanUtil({})
        result = doorman.get_query_param_from_request("date", _is_required=False)
        self.assertIsNone(result)

    def test_raises_when_param_missing_and_required(self):
        doorman = DoormanUtil({"queryStringParameters": {}})
        with self.assertRaises(UtilError):
            doorman.get_query_param_from_request("date", _is_required=True)

    def test_returns_none_when_param_missing_and_not_required(self):
        doorman = DoormanUtil({"queryStringParameters": {}})
        result = doorman.get_query_param_from_request("date", _is_required=False)
        self.assertIsNone(result)

    def test_raises_when_empty_value_and_required(self):
        doorman = DoormanUtil({"queryStringParameters": {"date": ""}})
        with self.assertRaises(UtilError):
            doorman.get_query_param_from_request("date", _is_required=True)

    def test_returns_value_when_present(self):
        doorman = DoormanUtil({"queryStringParameters": {"date": "2024-01-08"}})
        result = doorman.get_query_param_from_request("date", _is_required=True)
        self.assertEqual(result, "2024-01-08")

    def test_returns_none_for_none_value_and_not_required(self):
        doorman = DoormanUtil({"queryStringParameters": {"date": None}})
        result = doorman.get_query_param_from_request("date", _is_required=False)
        self.assertIsNone(result)


class TestDoormanBuildResponse(TestCase):

    def test_builds_correct_response_structure(self):
        doorman = DoormanUtil({})
        response = doorman.build_response({"message": "ok"}, 200)

        self.assertEqual(response["statusCode"], 200)
        self.assertFalse(response["isBase64Encoded"])
        self.assertEqual(response["headers"]["Content-Type"], "application/json")
        self.assertIn("Access-Control-Allow-Origin", response["headers"])
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "ok")

    def test_builds_response_with_different_status_codes(self):
        doorman = DoormanUtil({})
        for code in [200, 201, 400, 403, 500]:
            response = doorman.build_response({}, code)
            self.assertEqual(response["statusCode"], code)


class TestDoormanGetUsername(TestCase):

    @patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)
    def test_returns_admin_in_local_env(self):
        doorman = DoormanUtil({})
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "local"
        try:
            result = doorman.get_username_from_context()
            self.assertEqual(result, "Admin")
        finally:
            doorman_module.environment = original

    def test_returns_email_from_cognito_context(self):
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {"email": "user@example.com", "cognito:groups": "Admin"}
                }
            }
        }
        doorman = DoormanUtil(event)
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            result = doorman.get_username_from_context()
            self.assertEqual(result, "user@example.com")
        finally:
            doorman_module.environment = original

    def test_raises_auth_error_on_missing_context(self):
        doorman = DoormanUtil({})
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            with self.assertRaises(AuthError):
                doorman.get_username_from_context()
        finally:
            doorman_module.environment = original


class TestDoormanAuthUser(TestCase):

    def test_returns_true_in_local_env(self):
        doorman = DoormanUtil({})
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "local"
        try:
            self.assertTrue(doorman.auth_user())
        finally:
            doorman_module.environment = original

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "CreateOrderFunction"})
    def test_returns_true_for_authorized_group(self):
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "user@test.com",
                        "cognito:groups": "Admin",
                    }
                }
            }
        }
        doorman = DoormanUtil(event)
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            result = doorman.auth_user()
            self.assertTrue(result)
        finally:
            doorman_module.environment = original

    def test_returns_false_when_cognito_groups_missing(self):
        event = {"requestContext": {"authorizer": {"claims": {"email": "u@t.com"}}}}
        doorman = DoormanUtil(event)
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            result = doorman.auth_user()
            self.assertFalse(result)
        finally:
            doorman_module.environment = original

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "CreateOrderFunction"})
    def test_returns_false_for_unauthorized_group(self):
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "repartidor@test.com",
                        "cognito:groups": "Repartidor",
                    }
                }
            }
        }
        doorman = DoormanUtil(event)
        from src.orders.order_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            result = doorman.auth_user()
            self.assertFalse(result)
        finally:
            doorman_module.environment = original
