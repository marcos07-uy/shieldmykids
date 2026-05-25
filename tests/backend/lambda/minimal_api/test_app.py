import base64
import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


APP_PATH = Path(__file__).resolve().parents[4] / "backend" / "lambda" / "minimal_api" / "app.py"


class FakeTable:
    def __init__(self, key_name):
        self.key_name = key_name
        self.items = {}

    def get_item(self, Key):
        item = self.items.get(Key[self.key_name])
        return {"Item": item.copy()} if item else {}

    def put_item(self, Item, ConditionExpression=None):
        key = Item[self.key_name]
        if ConditionExpression == "attribute_not_exists(codeHash)" and key in self.items:
            raise AssertionError("duplicate key")
        self.items[key] = Item.copy()
        return {}

    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames=None):
        item = self.items[Key[self.key_name]]
        if "#status" in UpdateExpression:
            status_name = ExpressionAttributeNames["#status"]
            item[status_name] = ExpressionAttributeValues[":status"]
            item["consumedAt"] = ExpressionAttributeValues[":consumedAt"]
            item["consumedByDeviceId"] = ExpressionAttributeValues[":deviceId"]
            return {}

        if not UpdateExpression.startswith("SET "):
            raise AssertionError(f"unsupported update expression: {UpdateExpression}")

        for assignment in UpdateExpression.removeprefix("SET ").split(", "):
            name, value_key = assignment.split(" = ")
            item[name] = ExpressionAttributeValues[value_key]
        return {}


class FakeDynamoDb:
    def __init__(self):
        self.tables = {
            "policies": FakeTable("childId"),
            "devices": FakeTable("deviceId"),
            "pairing_codes": FakeTable("codeHash"),
        }

    def Table(self, name):
        return self.tables[name]


class MinimalApiTest(unittest.TestCase):
    def setUp(self):
        self.fake_dynamodb = FakeDynamoDb()
        fake_boto3 = types.SimpleNamespace(resource=lambda _service: self.fake_dynamodb)

        self.env = mock.patch.dict(
            os.environ,
            {
                "POLICIES_TABLE_NAME": "policies",
                "DEVICES_TABLE_NAME": "devices",
                "PAIRING_CODES_TABLE_NAME": "pairing_codes",
                "DEV_PARENT_TOKEN": "parent-token",
                "DEFAULT_SYNC_INTERVAL_SECONDS": "60",
                "PAIRING_CODE_TTL_SECONDS": "900",
            },
            clear=False,
        )
        self.modules = mock.patch.dict(sys.modules, {"boto3": fake_boto3})
        self.env.start()
        self.modules.start()
        self.app = self.load_app()

    def tearDown(self):
        self.modules.stop()
        self.env.stop()
        sys.modules.pop("minimal_api_app_under_test", None)

    def load_app(self):
        spec = importlib.util.spec_from_file_location("minimal_api_app_under_test", APP_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def request(self, route_key, method, body=None, headers=None, path_params=None, encoded=False):
        raw_body = body
        if body is not None and not isinstance(body, str):
            raw_body = json.dumps(body)
        if encoded and raw_body is not None:
            raw_body = base64.b64encode(raw_body.encode("utf-8")).decode("ascii")
        return {
            "routeKey": route_key,
            "requestContext": {"http": {"method": method}},
            "headers": headers or {},
            "pathParameters": path_params or {},
            "body": raw_body,
            "isBase64Encoded": encoded,
        }

    def body(self, response):
        return json.loads(response["body"])

    def create_pairing_code(self):
        event = self.request(
            "POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes",
            "POST",
            headers={"X-Dev-Parent-Token": "parent-token"},
            path_params={"familyId": "fam_1", "childId": "child_1"},
        )
        response = self.app.handler(event, None)
        self.assertEqual(201, response["statusCode"])
        return self.body(response)["pairingCode"]

    def enroll_device(self, pairing_code):
        event = self.request(
            "POST /v1/device/enroll",
            "POST",
            body={"pairingCode": pairing_code, "platform": "windows", "deviceName": "Kid laptop"},
        )
        response = self.app.handler(event, None)
        self.assertEqual(201, response["statusCode"])
        return self.body(response)

    def test_pairing_enrollment_and_policy_fetch_flow(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "GET /v1/device/policy",
            "GET",
            headers={
                "Authorization": f"Device {enrollment['deviceCredential']}",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual("child_1", payload["policy"]["childId"])
        self.assertEqual("fam_1", payload["policy"]["familyId"])
        self.assertEqual(60, payload["syncIntervalSeconds"])

    def test_invalid_device_credential_is_rejected(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "GET /v1/device/policy",
            "GET",
            headers={
                "Authorization": "Device wrong-token",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("invalid_device_credential", self.body(response)["error"]["code"])

    def test_pairing_code_is_single_use(self):
        pairing_code = self.create_pairing_code()
        self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/enroll",
            "POST",
            body={"pairingCode": pairing_code, "platform": "windows"},
        )
        response = self.app.handler(event, None)

        self.assertEqual(409, response["statusCode"])
        self.assertEqual("pairing_code_consumed", self.body(response)["error"]["code"])

    def test_parent_routes_require_dev_parent_token(self):
        event = self.request(
            "POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes",
            "POST",
            headers={"X-Dev-Parent-Token": "wrong"},
            path_params={"familyId": "fam_1", "childId": "child_1"},
        )
        response = self.app.handler(event, None)

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("parent_auth_required", self.body(response)["error"]["code"])

    def test_device_heartbeat_updates_status_and_returns_policy_metadata(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/heartbeat",
            "POST",
            body={
                "reportedAt": "2026-05-25T16:20:00Z",
                "agentVersion": "0.1.0",
                "platformVersion": "Windows 11",
                "policyVersion": 1,
                "enforcementState": "allowed",
                "queueDepth": 2,
            },
            headers={
                "Authorization": f"Device {enrollment['deviceCredential']}",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual(enrollment["deviceId"], payload["deviceId"])
        self.assertEqual(1, payload["effectivePolicyVersion"])
        self.assertEqual(60, payload["syncIntervalSeconds"])
        self.assertEqual(0, payload["pendingCommandCount"])
        self.assertIn("serverTime", payload)

        device = self.fake_dynamodb.tables["devices"].items[enrollment["deviceId"]]
        self.assertEqual("2026-05-25T16:20:00Z", device["reportedAt"])
        self.assertEqual("0.1.0", device["agentVersion"])
        self.assertEqual("Windows 11", device["platformVersion"])
        self.assertEqual(1, device["policyVersion"])
        self.assertEqual("allowed", device["enforcementState"])
        self.assertEqual(2, device["queueDepth"])

    def test_device_heartbeat_requires_device_auth(self):
        event = self.request("POST /v1/device/heartbeat", "POST", body={})
        response = self.app.handler(event, None)

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("device_auth_required", self.body(response)["error"]["code"])


    def test_device_heartbeat_rejects_invalid_credential(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/heartbeat",
            "POST",
            body={},
            headers={
                "Authorization": "Device wrong-token",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("invalid_device_credential", self.body(response)["error"]["code"])

    def test_device_heartbeat_rejects_invalid_field_types(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/heartbeat",
            "POST",
            body={"queueDepth": "not-a-number"},
            headers={
                "Authorization": f"Device {enrollment['deviceCredential']}",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(400, response["statusCode"])
        self.assertEqual("invalid_field", self.body(response)["error"]["code"])

    def test_base64_json_body_is_accepted_for_policy_update(self):
        event = self.request(
            "PUT /v1/parent/families/{familyId}/children/{childId}/policy",
            "PUT",
            body={"rules": {"dailyLimitMinutes": 90}, "version": 7},
            headers={"X-Dev-Parent-Token": "parent-token"},
            path_params={"familyId": "fam_1", "childId": "child_1"},
            encoded=True,
        )
        response = self.app.handler(event, None)

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual(7, payload["policy"]["version"])
        self.assertEqual(90, payload["policy"]["rules"]["dailyLimitMinutes"])


if __name__ == "__main__":
    unittest.main()
