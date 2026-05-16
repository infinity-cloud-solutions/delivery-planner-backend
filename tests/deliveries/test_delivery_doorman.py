import json
import os
from unittest import TestCase
from unittest.mock import patch

from delivery_modules.errors.auth_error import AuthError
from delivery_modules.errors.util_error import UtilError

from src.orders.delivery.delivery_modules.utils.doorman import DoormanUtil


class TestDeliveryDoormanGetBody(TestCase):

    def test_raises_when_no_body_key(self):
        doorman = DoormanUtil({})
        with self.assertRaises(UtilError):
            doorman.get_body_from_request()

    def test_raises_when_body_is_none(self):
        doorman = DoormanUtil({"body": None})
        with self.assertRaises(UtilError):
            doorman.get_body_from_request()

    def test_returns_dict_body_directly(self):
        body = {"date": "2024-01-08", "available_drivers": [1, 2]}
        doorman = DoormanUtil({"body": body})
        result = doorman.get_body_from_request()
        self.assertEqual(result, body)

    def test_parses_json_string_body(self):
        body = {"date": "2024-01-08"}
        doorman = DoormanUtil({"body": json.dumps(body)})
        result = doorman.get_body_from_request()
        self.assertEqual(result, body)

    def test_raises_on_invalid_json(self):
        doorman = DoormanUtil({"body": "not-json{{"})
        with self.assertRaises(UtilError):
            doorman.get_body_from_request()


class TestDeliveryDoormanBuildResponse(TestCase):

    def test_builds_correct_response_structure(self):
        doorman = DoormanUtil({})
        response = doorman.build_response({"message": "ok"}, 200)

        self.assertEqual(response["statusCode"], 200)
        self.assertFalse(response["isBase64Encoded"])
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "ok")


class TestDeliveryDoormanGetUsername(TestCase):

    def test_returns_admin_in_local_env(self):
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "local"
        try:
            doorman = DoormanUtil({})
            result = doorman.get_username_from_context()
            self.assertEqual(result, "Admin")
        finally:
            doorman_module.environment = original

    def test_returns_email_from_cognito_context(self):
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {"email": "admin@test.com", "cognito:groups": "Admin"}
                }
            }
        }
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            doorman = DoormanUtil(event)
            result = doorman.get_username_from_context()
            self.assertEqual(result, "admin@test.com")
        finally:
            doorman_module.environment = original

    def test_raises_auth_error_on_missing_context(self):
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            doorman = DoormanUtil({})
            with self.assertRaises(AuthError):
                doorman.get_username_from_context()
        finally:
            doorman_module.environment = original


class TestDeliveryDoormanAuthUser(TestCase):

    def test_returns_true_in_local_env(self):
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "local"
        try:
            doorman = DoormanUtil({})
            self.assertTrue(doorman.auth_user())
        finally:
            doorman_module.environment = original

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "ScheduleOrdersFunction"})
    def test_returns_true_for_authorized_group(self):
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "admin@test.com",
                        "cognito:groups": "Admin",
                    }
                }
            }
        }
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            doorman = DoormanUtil(event)
            self.assertTrue(doorman.auth_user())
        finally:
            doorman_module.environment = original

    def test_returns_false_when_cognito_groups_missing(self):
        event = {"requestContext": {"authorizer": {"claims": {"email": "u@t.com"}}}}
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            doorman = DoormanUtil(event)
            self.assertFalse(doorman.auth_user())
        finally:
            doorman_module.environment = original

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "ScheduleOrdersFunction"})
    def test_returns_false_for_unauthorized_group(self):
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "driver@test.com",
                        "cognito:groups": "Repartidor",
                    }
                }
            }
        }
        from src.orders.delivery.delivery_modules.utils import doorman as doorman_module

        original = doorman_module.environment
        doorman_module.environment = "development"
        try:
            doorman = DoormanUtil(event)
            self.assertFalse(doorman.auth_user())
        finally:
            doorman_module.environment = original
