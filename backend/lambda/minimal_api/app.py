import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from decimal import Decimal

import boto3


dynamodb = boto3.resource("dynamodb")

POLICIES_TABLE = dynamodb.Table(os.environ["POLICIES_TABLE_NAME"])
DEVICES_TABLE = dynamodb.Table(os.environ["DEVICES_TABLE_NAME"])
PAIRING_CODES_TABLE = dynamodb.Table(os.environ["PAIRING_CODES_TABLE_NAME"])
USAGE_EVENTS_TABLE = dynamodb.Table(os.environ["USAGE_EVENTS_TABLE_NAME"])

DEV_PARENT_TOKEN = os.environ.get("DEV_PARENT_TOKEN", "")
DEFAULT_SYNC_INTERVAL_SECONDS = int(os.environ.get("DEFAULT_SYNC_INTERVAL_SECONDS", "60"))
PAIRING_CODE_TTL_SECONDS = int(os.environ.get("PAIRING_CODE_TTL_SECONDS", "900"))


DEFAULT_POLICY_RULES = {
    "dailyLimitMinutes": 120,
    "allowedSchedule": [
        {"days": ["mon", "tue", "wed", "thu"], "start": "16:00", "end": "20:00"},
        {"days": ["fri"], "start": "16:00", "end": "21:30"},
        {"days": ["sat", "sun"], "start": "09:00", "end": "21:30"},
    ],
    "warningThresholdMinutes": 10,
    "bonusMinutes": 0,
    "manualLock": {"enabled": False, "reason": None, "expiresAt": None},
}


def handler(event, _context):
    try:
        route_key = event.get("routeKey", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path_params = event.get("pathParameters") or {}

        if method == "OPTIONS":
            return response(204, None)

        if route_key == "POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes":
            require_dev_parent(event)
            return create_pairing_code(path_params)

        if route_key == "PUT /v1/parent/families/{familyId}/children/{childId}/policy":
            require_dev_parent(event)
            return put_policy(path_params, parse_body(event))

        if route_key == "POST /v1/device/enroll":
            return enroll_device(parse_body(event))

        if route_key == "POST /v1/device/heartbeat":
            device = require_device(event)
            return heartbeat_device(device, parse_body(event))

        if route_key == "POST /v1/device/usage-events":
            device = require_device(event)
            return submit_usage_events(device, parse_body(event))

        if route_key == "GET /v1/device/policy":
            device = require_device(event)
            return get_device_policy(device)

        return error_response(404, "not_found", "Route is not implemented.")
    except HttpError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except Exception:
        return error_response(500, "internal_error", "Unexpected server error.")


def create_pairing_code(path_params):
    now = epoch_seconds()
    family_id = require_path_param(path_params, "familyId")
    child_id = require_path_param(path_params, "childId")
    code = format_pairing_code(secrets.randbelow(1_000_000))
    code_hash = hash_secret(code)
    expires_at = now + PAIRING_CODE_TTL_SECONDS

    PAIRING_CODES_TABLE.put_item(
        Item={
            "codeHash": code_hash,
            "pairingCodeId": f"pc_{uuid.uuid4().hex}",
            "familyId": family_id,
            "childId": child_id,
            "createdAt": iso_time(now),
            "expiresAt": expires_at,
            "status": "active",
        },
        ConditionExpression="attribute_not_exists(codeHash)",
    )

    return response(201, {"pairingCode": code, "expiresAt": iso_time(expires_at)})


def put_policy(path_params, body):
    now = epoch_seconds()
    family_id = require_path_param(path_params, "familyId")
    child_id = require_path_param(path_params, "childId")
    rules = body.get("rules")

    if not isinstance(rules, dict):
        raise HttpError(400, "invalid_policy", "Policy body must include a rules object.")

    version = int(body.get("version") or now)
    existing = POLICIES_TABLE.get_item(Key={"childId": child_id}).get("Item")
    policy = {
        "policyId": body.get("policyId") or f"policy_{child_id}",
        "familyId": family_id,
        "childId": child_id,
        "version": version,
        "rules": rules,
        "createdAt": existing.get("createdAt") if existing else iso_time(now),
        "updatedAt": iso_time(now),
        "createdByParentId": body.get("createdByParentId") or "dev-parent",
    }

    POLICIES_TABLE.put_item(Item=policy)
    return response(200, {"policy": policy})


def enroll_device(body):
    now = epoch_seconds()
    pairing_code = require_body_string(body, "pairingCode")
    code_hash = hash_secret(pairing_code)

    pairing = PAIRING_CODES_TABLE.get_item(Key={"codeHash": code_hash}).get("Item")
    if not pairing:
        raise HttpError(401, "invalid_pairing_code", "Pairing code is invalid.")
    if pairing.get("status") != "active":
        raise HttpError(409, "pairing_code_consumed", "Pairing code is no longer active.")
    if int(pairing.get("expiresAt", 0)) < now:
        raise HttpError(410, "pairing_code_expired", "Pairing code has expired.")

    device_id = f"dev_{uuid.uuid4().hex}"
    credential = f"skd_{secrets.token_urlsafe(32)}"
    family_id = pairing["familyId"]
    child_id = pairing["childId"]

    device = {
        "deviceId": device_id,
        "familyId": family_id,
        "childId": child_id,
        "platform": body.get("platform", "windows"),
        "name": body.get("deviceName") or body.get("name") or "Windows device",
        "agentVersion": body.get("agentVersion", "unknown"),
        "credentialHash": hash_secret(credential),
        "lastSeenAt": iso_time(now),
        "enrollmentStatus": "enrolled",
        "policyVersion": 0,
        "status": "active",
        "createdAt": iso_time(now),
        "revokedAt": None,
    }

    DEVICES_TABLE.put_item(Item=device)
    PAIRING_CODES_TABLE.update_item(
        Key={"codeHash": code_hash},
        UpdateExpression="SET #status = :status, consumedAt = :consumedAt, consumedByDeviceId = :deviceId",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": "consumed",
            ":consumedAt": iso_time(now),
            ":deviceId": device_id,
        },
    )

    policy = get_or_create_default_policy(family_id, child_id)
    return response(
        201,
        {
            "deviceId": device_id,
            "deviceCredential": credential,
            "initialPolicy": policy,
            "syncIntervalSeconds": DEFAULT_SYNC_INTERVAL_SECONDS,
        },
    )


def submit_usage_events(device, body):
    now = epoch_seconds()
    batch_id = require_body_string(body, "batchId")
    events = body.get("events")
    if not isinstance(events, list) or not events:
        raise HttpError(400, "invalid_usage_batch", "Usage batch must include a non-empty events array.")

    accepted_event_ids = []
    duplicate_event_ids = []
    rejected_events = []

    for index, event in enumerate(events):
        try:
            usage_event = build_usage_event(device, batch_id, event, now)
        except HttpError as exc:
            rejected_events.append({"index": index, "code": exc.code, "message": exc.message})
            continue

        event_id = usage_event["eventId"]
        if USAGE_EVENTS_TABLE.get_item(Key={"deviceEventId": usage_event["deviceEventId"]}).get("Item"):
            duplicate_event_ids.append(event_id)
            continue

        USAGE_EVENTS_TABLE.put_item(Item=usage_event)
        accepted_event_ids.append(event_id)

    return response(
        200,
        {
            "acceptedEventIds": accepted_event_ids,
            "duplicateEventIds": duplicate_event_ids,
            "rejectedEvents": rejected_events,
            "syncIntervalSeconds": DEFAULT_SYNC_INTERVAL_SECONDS,
        },
    )


def build_usage_event(device, batch_id, event, now):
    if not isinstance(event, dict):
        raise HttpError(400, "invalid_usage_event", "Usage event must be an object.")

    event_id = require_body_string(event, "eventId")
    started_at = require_body_string(event, "startedAt")
    ended_at = require_body_string(event, "endedAt")
    activity_type = require_body_string(event, "activityType")

    return {
        "deviceEventId": f"{device['deviceId']}#{event_id}",
        "eventId": event_id,
        "batchId": batch_id,
        "deviceId": device["deviceId"],
        "familyId": device["familyId"],
        "childId": device["childId"],
        "startedAt": started_at,
        "endedAt": ended_at,
        "activityType": activity_type,
        "appName": optional_string(event, "appName"),
        "appCategory": optional_string(event, "appCategory"),
        "source": optional_string(event, "source"),
        "receivedAt": iso_time(now),
    }


def heartbeat_device(device, body):
    now = epoch_seconds()
    policy = get_or_create_default_policy(device["familyId"], device["childId"])
    update_device_heartbeat(device["deviceId"], body, now)

    return response(
        200,
        {
            "serverTime": iso_time(now),
            "deviceId": device["deviceId"],
            "effectivePolicyVersion": policy["version"],
            "syncIntervalSeconds": DEFAULT_SYNC_INTERVAL_SECONDS,
            "pendingCommandCount": 0,
        },
    )


def get_device_policy(device):
    policy = get_or_create_default_policy(device["familyId"], device["childId"])
    return response(200, {"policy": policy, "syncIntervalSeconds": DEFAULT_SYNC_INTERVAL_SECONDS})


def update_device_heartbeat(device_id, body, now):
    values = {
        ":lastSeenAt": iso_time(now),
        ":reportedAt": optional_string(body, "reportedAt"),
        ":agentVersion": optional_string(body, "agentVersion"),
        ":platformVersion": optional_string(body, "platformVersion"),
        ":policyVersion": optional_int(body, "policyVersion"),
        ":enforcementState": optional_string(body, "enforcementState"),
        ":queueDepth": optional_int(body, "queueDepth"),
    }
    DEVICES_TABLE.update_item(
        Key={"deviceId": device_id},
        UpdateExpression=(
            "SET lastSeenAt = :lastSeenAt, reportedAt = :reportedAt, "
            "agentVersion = :agentVersion, platformVersion = :platformVersion, "
            "policyVersion = :policyVersion, enforcementState = :enforcementState, "
            "queueDepth = :queueDepth"
        ),
        ExpressionAttributeValues=values,
    )


def get_or_create_default_policy(family_id, child_id):
    existing = POLICIES_TABLE.get_item(Key={"childId": child_id}).get("Item")
    if existing:
        return existing

    now = epoch_seconds()
    policy = {
        "policyId": f"policy_{child_id}",
        "familyId": family_id,
        "childId": child_id,
        "version": 1,
        "rules": DEFAULT_POLICY_RULES,
        "createdAt": iso_time(now),
        "updatedAt": iso_time(now),
        "createdByParentId": "system",
    }
    POLICIES_TABLE.put_item(Item=policy)
    return policy


def require_device(event):
    headers = normalize_headers(event.get("headers") or {})
    auth = headers.get("authorization", "")
    device_id = headers.get("x-device-id", "")

    if not auth.startswith("Device ") or not device_id:
        raise HttpError(401, "device_auth_required", "Device credentials are required.")

    token = auth.removeprefix("Device ").strip()
    device = DEVICES_TABLE.get_item(Key={"deviceId": device_id}).get("Item")
    if not device or device.get("status") != "active":
        raise HttpError(401, "invalid_device", "Device is not active.")
    if not constant_time_equals(device.get("credentialHash", ""), hash_secret(token)):
        raise HttpError(401, "invalid_device_credential", "Device credential is invalid.")

    DEVICES_TABLE.update_item(
        Key={"deviceId": device_id},
        UpdateExpression="SET lastSeenAt = :lastSeenAt",
        ExpressionAttributeValues={":lastSeenAt": iso_time(epoch_seconds())},
    )
    return device


def require_dev_parent(event):
    if not DEV_PARENT_TOKEN:
        return

    headers = normalize_headers(event.get("headers") or {})
    provided = headers.get("x-dev-parent-token", "")
    if not constant_time_equals(provided, DEV_PARENT_TOKEN):
        raise HttpError(401, "parent_auth_required", "Valid X-Dev-Parent-Token is required.")


def parse_body(event):
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HttpError(400, "invalid_json", "Request body must be valid JSON.")

    if not isinstance(body, dict):
        raise HttpError(400, "invalid_body", "Request body must be a JSON object.")
    return body


def require_path_param(path_params, name):
    value = path_params.get(name)
    if not value:
        raise HttpError(400, "missing_path_parameter", f"Missing path parameter: {name}.")
    return value


def require_body_string(body, name):
    value = body.get(name)
    if not isinstance(value, str) or not value.strip():
        raise HttpError(400, "missing_field", f"Missing required string field: {name}.")
    return value.strip()


def optional_string(body, name):
    value = body.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HttpError(400, "invalid_field", f"Field must be a string: {name}.")
    return value.strip() or None


def optional_int(body, name):
    value = body.get(name)
    if value is None:
        return None
    if isinstance(value, bool):
        raise HttpError(400, "invalid_field", f"Field must be an integer: {name}.")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HttpError(400, "invalid_field", f"Field must be an integer: {name}.")


def hash_secret(secret):
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def constant_time_equals(left, right):
    return hmac.compare_digest(str(left), str(right))


def format_pairing_code(number):
    return f"{number:06d}"


def epoch_seconds():
    return int(time.time())


def iso_time(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def normalize_headers(headers):
    return {str(key).lower(): value for key, value in headers.items()}


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Device-Id,X-Dev-Parent-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
        },
        "body": "" if body is None else json.dumps(body, default=json_default),
    }


def error_response(status_code, code, message):
    return response(status_code, {"error": {"code": code, "message": message}})


def json_default(value):
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


class HttpError(Exception):
    def __init__(self, status_code, code, message):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
