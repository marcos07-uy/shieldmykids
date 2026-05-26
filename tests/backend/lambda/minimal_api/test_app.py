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
            if ":consumedAt" in ExpressionAttributeValues:
                item["consumedAt"] = ExpressionAttributeValues[":consumedAt"]
            if ":deviceId" in ExpressionAttributeValues:
                item["consumedByDeviceId"] = ExpressionAttributeValues[":deviceId"]
            if ":acknowledgedAt" in ExpressionAttributeValues:
                item["acknowledgedAt"] = ExpressionAttributeValues[":acknowledgedAt"]
                item["acknowledgedByDeviceId"] = ExpressionAttributeValues[":acknowledgedByDeviceId"]
                item["errorCode"] = ExpressionAttributeValues[":errorCode"]
                item["diagnostics"] = ExpressionAttributeValues[":diagnostics"]
            return {}

        if not UpdateExpression.startswith("SET "):
            raise AssertionError(f"unsupported update expression: {UpdateExpression}")

        for assignment in UpdateExpression.removeprefix("SET ").split(", "):
            name, value_key = assignment.split(" = ")
            item[name] = ExpressionAttributeValues[value_key]
        return {}

    def query(self, IndexName, KeyConditionExpression, ExpressionAttributeValues):
        if IndexName == "childId-index" and KeyConditionExpression == "childId = :childId":
            child_id = ExpressionAttributeValues[":childId"]
            return {"Items": [item.copy() for item in self.items.values() if item.get("childId") == child_id]}
        if IndexName == "deviceId-index" and KeyConditionExpression == "deviceId = :deviceId":
            device_id = ExpressionAttributeValues[":deviceId"]
            return {"Items": [item.copy() for item in self.items.values() if item.get("deviceId") == device_id]}
        raise AssertionError("unsupported query")


class FakeDynamoDb:
    def __init__(self):
        self.tables = {
            "policies": FakeTable("childId"),
            "devices": FakeTable("deviceId"),
            "pairing_codes": FakeTable("codeHash"),
            "usage_events": FakeTable("deviceEventId"),
            "device_commands": FakeTable("commandId"),
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
                "USAGE_EVENTS_TABLE_NAME": "usage_events",
                "DEVICE_COMMANDS_TABLE_NAME": "device_commands",
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

    def request(self, route_key, method, body=None, headers=None, path_params=None, query_params=None, encoded=False):
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
            "queryStringParameters": query_params or {},
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

    def test_usage_events_accepts_valid_batch(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/usage-events",
            "POST",
            body={
                "batchId": "batch_001",
                "events": [
                    {
                        "eventId": "evt_001",
                        "startedAt": "2026-05-25T16:00:00Z",
                        "endedAt": "2026-05-25T16:15:00Z",
                        "activityType": "screen",
                        "appName": "Browser",
                    }
                ],
            },
            headers={
                "Authorization": f"Device {enrollment['deviceCredential']}",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual(["evt_001"], payload["acceptedEventIds"])
        self.assertEqual([], payload["duplicateEventIds"])
        self.assertEqual([], payload["rejectedEvents"])
        self.assertEqual(60, payload["syncIntervalSeconds"])

        device_event_id = f"{enrollment['deviceId']}#evt_001"
        stored = self.fake_dynamodb.tables["usage_events"].items[device_event_id]
        self.assertEqual(device_event_id, stored["deviceEventId"])
        self.assertEqual("evt_001", stored["eventId"])
        self.assertEqual("batch_001", stored["batchId"])
        self.assertEqual(enrollment["deviceId"], stored["deviceId"])
        self.assertEqual("fam_1", stored["familyId"])
        self.assertEqual("child_1", stored["childId"])
        self.assertEqual("screen", stored["activityType"])
        self.assertEqual("Browser", stored["appName"])
        self.assertIn("receivedAt", stored)

    def test_usage_events_reports_duplicate_event_ids_idempotently(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)
        headers = {
            "Authorization": f"Device {enrollment['deviceCredential']}",
            "X-Device-Id": enrollment["deviceId"],
        }
        body = {
            "batchId": "batch_001",
            "events": [
                {
                    "eventId": "evt_duplicate",
                    "startedAt": "2026-05-25T16:00:00Z",
                    "endedAt": "2026-05-25T16:15:00Z",
                    "activityType": "screen",
                }
            ],
        }

        first_response = self.app.handler(
            self.request("POST /v1/device/usage-events", "POST", body=body, headers=headers), None
        )
        second_response = self.app.handler(
            self.request("POST /v1/device/usage-events", "POST", body=body, headers=headers), None
        )

        self.assertEqual(200, first_response["statusCode"])
        self.assertEqual(["evt_duplicate"], self.body(first_response)["acceptedEventIds"])
        self.assertEqual(200, second_response["statusCode"])
        second_payload = self.body(second_response)
        self.assertEqual([], second_payload["acceptedEventIds"])
        self.assertEqual(["evt_duplicate"], second_payload["duplicateEventIds"])

    def test_usage_events_reports_invalid_event_fields(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/usage-events",
            "POST",
            body={
                "batchId": "batch_001",
                "events": [
                    {
                        "eventId": "evt_missing_end",
                        "startedAt": "2026-05-25T16:00:00Z",
                        "activityType": "screen",
                    }
                ],
            },
            headers={
                "Authorization": f"Device {enrollment['deviceCredential']}",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual([], payload["acceptedEventIds"])
        self.assertEqual("missing_field", payload["rejectedEvents"][0]["code"])
        self.assertEqual(0, payload["rejectedEvents"][0]["index"])

    def test_usage_events_rejects_invalid_device_credential(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/usage-events",
            "POST",
            body={"batchId": "batch_001", "events": []},
            headers={
                "Authorization": "Device wrong-token",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("invalid_device_credential", self.body(response)["error"]["code"])

    def test_usage_events_requires_non_empty_events_array(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        event = self.request(
            "POST /v1/device/usage-events",
            "POST",
            body={"batchId": "batch_001", "events": []},
            headers={
                "Authorization": f"Device {enrollment['deviceCredential']}",
                "X-Device-Id": enrollment["deviceId"],
            },
        )
        response = self.app.handler(event, None)

        self.assertEqual(400, response["statusCode"])
        self.assertEqual("invalid_usage_batch", self.body(response)["error"]["code"])

    def test_device_commands_returns_empty_command_list(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        response = self.app.handler(
            self.request(
                "GET /v1/device/commands",
                "GET",
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
            ),
            None,
        )

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual(enrollment["deviceId"], payload["deviceId"])
        self.assertEqual([], payload["commands"])
        self.assertEqual(60, payload["syncIntervalSeconds"])

    def test_parent_lock_command_is_returned_to_device_poll(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        lock_response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={"reason": "Homework time", "expiresAt": "2026-05-25T18:00:00Z"},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )
        commands_response = self.app.handler(
            self.request(
                "GET /v1/device/commands",
                "GET",
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
            ),
            None,
        )

        self.assertEqual(201, lock_response["statusCode"])
        command = self.body(lock_response)["command"]
        self.assertEqual("lock", command["type"])
        self.assertEqual("queued", command["status"])
        self.assertEqual("Homework time", command["reason"])
        self.assertEqual("2026-05-25T18:00:00Z", command["expiresAt"])

        self.assertEqual(200, commands_response["statusCode"])
        commands = self.body(commands_response)["commands"]
        self.assertEqual([command], commands)

    def test_parent_unlock_command_is_queued(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/unlock",
                "POST",
                body={"reason": "Parent override"},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )

        self.assertEqual(201, response["statusCode"])
        command = self.body(response)["command"]
        self.assertEqual("unlock", command["type"])
        self.assertEqual("queued", command["status"])
        self.assertEqual("Parent override", command["reason"])
        self.assertIsNone(command["expiresAt"])

    def test_parent_command_requires_dev_parent_token(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={},
                headers={"X-Dev-Parent-Token": "wrong"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("parent_auth_required", self.body(response)["error"]["code"])

    def test_parent_command_rejects_device_from_other_family(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_2", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )

        self.assertEqual(404, response["statusCode"])
        self.assertEqual("device_not_found", self.body(response)["error"]["code"])

    def test_device_command_acknowledgement_updates_command_status(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)
        lock_response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={"reason": "Homework time"},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )
        command_id = self.body(lock_response)["command"]["commandId"]

        ack_response = self.app.handler(
            self.request(
                "POST /v1/device/commands/{commandId}/ack",
                "POST",
                body={"status": "applied"},
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
                path_params={"commandId": command_id},
            ),
            None,
        )
        poll_response = self.app.handler(
            self.request(
                "GET /v1/device/commands",
                "GET",
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
            ),
            None,
        )

        self.assertEqual(200, ack_response["statusCode"])
        command = self.body(ack_response)["command"]
        self.assertEqual(command_id, command["commandId"])
        self.assertEqual("applied", command["status"])
        self.assertEqual(enrollment["deviceId"], command["acknowledgedByDeviceId"])
        self.assertIn("acknowledgedAt", command)
        self.assertEqual([], self.body(poll_response)["commands"])

    def test_device_command_acknowledgement_defaults_to_acknowledged(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)
        lock_response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )
        command_id = self.body(lock_response)["command"]["commandId"]

        response = self.app.handler(
            self.request(
                "POST /v1/device/commands/{commandId}/ack",
                "POST",
                body={},
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
                path_params={"commandId": command_id},
            ),
            None,
        )

        self.assertEqual(200, response["statusCode"])
        self.assertEqual("acknowledged", self.body(response)["command"]["status"])

    def test_device_command_acknowledgement_records_failure_details(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)
        lock_response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )
        command_id = self.body(lock_response)["command"]["commandId"]

        response = self.app.handler(
            self.request(
                "POST /v1/device/commands/{commandId}/ack",
                "POST",
                body={
                    "status": "failed",
                    "errorCode": "lock_failed",
                    "diagnostics": "session already ending",
                },
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
                path_params={"commandId": command_id},
            ),
            None,
        )

        self.assertEqual(200, response["statusCode"])
        command = self.body(response)["command"]
        self.assertEqual("failed", command["status"])
        self.assertEqual("lock_failed", command["errorCode"])
        self.assertEqual("session already ending", command["diagnostics"])

    def test_device_command_acknowledgement_rejects_invalid_status(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)
        lock_response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": enrollment["deviceId"]},
            ),
            None,
        )
        command_id = self.body(lock_response)["command"]["commandId"]

        response = self.app.handler(
            self.request(
                "POST /v1/device/commands/{commandId}/ack",
                "POST",
                body={"status": "done"},
                headers={
                    "Authorization": f"Device {enrollment['deviceCredential']}",
                    "X-Device-Id": enrollment["deviceId"],
                },
                path_params={"commandId": command_id},
            ),
            None,
        )

        self.assertEqual(400, response["statusCode"])
        self.assertEqual("invalid_command_status", self.body(response)["error"]["code"])

    def test_device_command_acknowledgement_rejects_wrong_device(self):
        first_pairing_code = self.create_pairing_code()
        first_enrollment = self.enroll_device(first_pairing_code)
        second_pairing_code = self.create_pairing_code()
        second_enrollment = self.enroll_device(second_pairing_code)
        lock_response = self.app.handler(
            self.request(
                "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock",
                "POST",
                body={},
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "deviceId": first_enrollment["deviceId"]},
            ),
            None,
        )
        command_id = self.body(lock_response)["command"]["commandId"]

        response = self.app.handler(
            self.request(
                "POST /v1/device/commands/{commandId}/ack",
                "POST",
                body={"status": "applied"},
                headers={
                    "Authorization": f"Device {second_enrollment['deviceCredential']}",
                    "X-Device-Id": second_enrollment["deviceId"],
                },
                path_params={"commandId": command_id},
            ),
            None,
        )

        self.assertEqual(404, response["statusCode"])
        self.assertEqual("command_not_found", self.body(response)["error"]["code"])

    def test_device_command_acknowledgement_requires_device_auth(self):
        response = self.app.handler(
            self.request(
                "POST /v1/device/commands/{commandId}/ack",
                "POST",
                body={"status": "applied"},
                path_params={"commandId": "cmd_missing"},
            ),
            None,
        )

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("device_auth_required", self.body(response)["error"]["code"])

    def test_device_commands_requires_device_auth(self):
        response = self.app.handler(self.request("GET /v1/device/commands", "GET"), None)

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("device_auth_required", self.body(response)["error"]["code"])

    def test_device_commands_rejects_invalid_credential(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)

        response = self.app.handler(
            self.request(
                "GET /v1/device/commands",
                "GET",
                headers={
                    "Authorization": "Device wrong-token",
                    "X-Device-Id": enrollment["deviceId"],
                },
            ),
            None,
        )

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("invalid_device_credential", self.body(response)["error"]["code"])

    def test_parent_usage_summary_returns_totals_for_child_and_date(self):
        pairing_code = self.create_pairing_code()
        enrollment = self.enroll_device(pairing_code)
        headers = {
            "Authorization": f"Device {enrollment['deviceCredential']}",
            "X-Device-Id": enrollment["deviceId"],
        }
        self.app.handler(
            self.request(
                "POST /v1/device/usage-events",
                "POST",
                body={
                    "batchId": "batch_001",
                    "events": [
                        {
                            "eventId": "evt_browser",
                            "startedAt": "2026-05-25T16:00:00Z",
                            "endedAt": "2026-05-25T16:15:00Z",
                            "activityType": "screen",
                            "appName": "Browser",
                        },
                        {
                            "eventId": "evt_game",
                            "startedAt": "2026-05-25T17:00:00Z",
                            "endedAt": "2026-05-25T17:30:00Z",
                            "activityType": "game",
                            "appName": "Chess",
                        },
                        {
                            "eventId": "evt_other_date",
                            "startedAt": "2026-05-24T17:00:00Z",
                            "endedAt": "2026-05-24T18:00:00Z",
                            "activityType": "screen",
                            "appName": "Browser",
                        },
                    ],
                },
                headers=headers,
            ),
            None,
        )
        self.fake_dynamodb.tables["usage_events"].put_item(
            Item={
                "deviceEventId": "other-device#evt_other_child",
                "eventId": "evt_other_child",
                "batchId": "batch_other",
                "deviceId": "other-device",
                "familyId": "fam_1",
                "childId": "child_2",
                "startedAt": "2026-05-25T16:00:00Z",
                "endedAt": "2026-05-25T17:00:00Z",
                "activityType": "screen",
                "appName": "Browser",
            }
        )
        self.fake_dynamodb.tables["usage_events"].put_item(
            Item={
                "deviceEventId": "other-family#evt_other_family",
                "eventId": "evt_other_family",
                "batchId": "batch_other",
                "deviceId": "other-family",
                "familyId": "fam_2",
                "childId": "child_1",
                "startedAt": "2026-05-25T16:00:00Z",
                "endedAt": "2026-05-25T17:00:00Z",
                "activityType": "screen",
                "appName": "Browser",
            }
        )

        response = self.app.handler(
            self.request(
                "GET /v1/parent/families/{familyId}/children/{childId}/usage",
                "GET",
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "childId": "child_1"},
                query_params={"date": "2026-05-25"},
            ),
            None,
        )

        self.assertEqual(200, response["statusCode"])
        payload = self.body(response)
        self.assertEqual("fam_1", payload["familyId"])
        self.assertEqual("child_1", payload["childId"])
        self.assertEqual("2026-05-25", payload["date"])
        self.assertEqual(45, payload["totalMinutes"])
        self.assertEqual(2, payload["eventCount"])
        self.assertEqual({enrollment["deviceId"]: 45}, payload["deviceTotals"])
        self.assertEqual({"screen": 15, "game": 30}, payload["activityTotals"])
        self.assertEqual({"Browser": 15, "Chess": 30}, payload["appTotals"])

    def test_parent_usage_summary_requires_dev_parent_token(self):
        response = self.app.handler(
            self.request(
                "GET /v1/parent/families/{familyId}/children/{childId}/usage",
                "GET",
                headers={"X-Dev-Parent-Token": "wrong"},
                path_params={"familyId": "fam_1", "childId": "child_1"},
                query_params={"date": "2026-05-25"},
            ),
            None,
        )

        self.assertEqual(401, response["statusCode"])
        self.assertEqual("parent_auth_required", self.body(response)["error"]["code"])

    def test_parent_usage_summary_requires_valid_date(self):
        missing_response = self.app.handler(
            self.request(
                "GET /v1/parent/families/{familyId}/children/{childId}/usage",
                "GET",
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "childId": "child_1"},
            ),
            None,
        )
        invalid_response = self.app.handler(
            self.request(
                "GET /v1/parent/families/{familyId}/children/{childId}/usage",
                "GET",
                headers={"X-Dev-Parent-Token": "parent-token"},
                path_params={"familyId": "fam_1", "childId": "child_1"},
                query_params={"date": "05-25-2026"},
            ),
            None,
        )

        self.assertEqual(400, missing_response["statusCode"])
        self.assertEqual("missing_query_parameter", self.body(missing_response)["error"]["code"])
        self.assertEqual(400, invalid_response["statusCode"])
        self.assertEqual("invalid_date", self.body(invalid_response)["error"]["code"])

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
