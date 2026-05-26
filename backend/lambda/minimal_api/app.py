import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from datetime import datetime
from decimal import Decimal

import boto3


dynamodb = boto3.resource("dynamodb")

POLICIES_TABLE = dynamodb.Table(os.environ["POLICIES_TABLE_NAME"])
DEVICES_TABLE = dynamodb.Table(os.environ["DEVICES_TABLE_NAME"])
PAIRING_CODES_TABLE = dynamodb.Table(os.environ["PAIRING_CODES_TABLE_NAME"])
USAGE_EVENTS_TABLE = dynamodb.Table(os.environ["USAGE_EVENTS_TABLE_NAME"])
DEVICE_COMMANDS_TABLE = dynamodb.Table(os.environ["DEVICE_COMMANDS_TABLE_NAME"])
AUDIT_EVENTS_TABLE = dynamodb.Table(os.environ["AUDIT_EVENTS_TABLE_NAME"])

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

        if route_key == "GET /v1/parent/families/{familyId}/children/{childId}/usage":
            require_dev_parent(event)
            return get_usage_summary(path_params, event.get("queryStringParameters") or {})

        if route_key == "GET /v1/parent/families/{familyId}/audit-events":
            require_dev_parent(event)
            return list_audit_events(path_params)

        if route_key == "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock":
            require_dev_parent(event)
            return queue_device_command(path_params, parse_body(event), "lock")

        if route_key == "POST /v1/parent/families/{familyId}/devices/{deviceId}/unlock":
            require_dev_parent(event)
            return queue_device_command(path_params, parse_body(event), "unlock")

        if route_key == "POST /v1/device/enroll":
            return enroll_device(parse_body(event))

        if route_key == "POST /v1/device/heartbeat":
            device = require_device(event)
            return heartbeat_device(device, parse_body(event))

        if route_key == "POST /v1/device/usage-events":
            device = require_device(event)
            return submit_usage_events(device, parse_body(event))

        if route_key == "GET /v1/device/commands":
            device = require_device(event)
            return get_device_commands(device)

        if route_key == "POST /v1/device/commands/{commandId}/ack":
            device = require_device(event)
            return acknowledge_device_command(device, path_params, parse_body(event))

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
    record_audit_event(
        family_id=family_id,
        actor_type="parent",
        actor_id=policy["createdByParentId"],
        action="policy.updated",
        target_type="policy",
        target_id=policy["policyId"],
        metadata={"childId": child_id, "version": version},
        now=now,
    )
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
    record_audit_event(
        family_id=family_id,
        actor_type="device",
        actor_id=device_id,
        action="device.enrolled",
        target_type="device",
        target_id=device_id,
        metadata={
            "childId": child_id,
            "platform": device["platform"],
            "deviceName": device["name"],
            "agentVersion": device["agentVersion"],
        },
        now=now,
    )
    return response(
        201,
        {
            "deviceId": device_id,
            "deviceCredential": credential,
            "initialPolicy": policy,
            "syncIntervalSeconds": DEFAULT_SYNC_INTERVAL_SECONDS,
        },
    )


def list_audit_events(path_params):
    family_id = require_path_param(path_params, "familyId")
    result = AUDIT_EVENTS_TABLE.query(
        IndexName="familyId-index",
        KeyConditionExpression="familyId = :familyId",
        ExpressionAttributeValues={":familyId": family_id},
    )
    events = sorted(result.get("Items", []), key=lambda event: event["timestamp"], reverse=True)
    return response(200, {"familyId": family_id, "auditEvents": events})


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


def get_usage_summary(path_params, query_params):
    family_id = require_path_param(path_params, "familyId")
    child_id = require_path_param(path_params, "childId")
    usage_date = require_date_query(query_params)
    events = query_usage_events_for_child(child_id)

    total_minutes = 0
    event_count = 0
    device_totals = {}
    activity_totals = {}
    app_totals = {}

    for event in events:
        if event.get("familyId") != family_id or event.get("childId") != child_id:
            continue
        if not str(event.get("startedAt", "")).startswith(f"{usage_date}T"):
            continue

        minutes = usage_event_minutes(event)
        total_minutes += minutes
        event_count += 1
        add_total(device_totals, event.get("deviceId") or "unknown", minutes)
        add_total(activity_totals, event.get("activityType") or "unknown", minutes)
        app_name = event.get("appName")
        if app_name:
            add_total(app_totals, app_name, minutes)

    return response(
        200,
        {
            "familyId": family_id,
            "childId": child_id,
            "date": usage_date,
            "totalMinutes": total_minutes,
            "eventCount": event_count,
            "deviceTotals": device_totals,
            "activityTotals": activity_totals,
            "appTotals": app_totals,
        },
    )


def query_usage_events_for_child(child_id):
    result = USAGE_EVENTS_TABLE.query(
        IndexName="childId-index",
        KeyConditionExpression="childId = :childId",
        ExpressionAttributeValues={":childId": child_id},
    )
    return result.get("Items", [])


def usage_event_minutes(event):
    started_at = parse_iso_time(event.get("startedAt"))
    ended_at = parse_iso_time(event.get("endedAt"))
    seconds = max(0, int((ended_at - started_at).total_seconds()))
    return seconds // 60


def add_total(totals, key, minutes):
    totals[key] = totals.get(key, 0) + minutes


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


def get_device_commands(device):
    commands = query_queued_commands_for_device(device["deviceId"])
    return response(
        200,
        {
            "deviceId": device["deviceId"],
            "commands": commands,
            "syncIntervalSeconds": DEFAULT_SYNC_INTERVAL_SECONDS,
        },
    )


def queue_device_command(path_params, body, command_type):
    now = epoch_seconds()
    family_id = require_path_param(path_params, "familyId")
    device_id = require_path_param(path_params, "deviceId")
    device = DEVICES_TABLE.get_item(Key={"deviceId": device_id}).get("Item")
    if not device or device.get("familyId") != family_id:
        raise HttpError(404, "device_not_found", "Device was not found for this family.")
    if device.get("status") != "active":
        raise HttpError(409, "device_not_active", "Device is not active.")

    command = {
        "commandId": f"cmd_{uuid.uuid4().hex}",
        "deviceId": device_id,
        "familyId": family_id,
        "childId": device["childId"],
        "type": command_type,
        "status": "queued",
        "reason": optional_string(body, "reason"),
        "expiresAt": optional_string(body, "expiresAt"),
        "createdAt": iso_time(now),
        "createdByParentId": body.get("createdByParentId") or "dev-parent",
    }
    DEVICE_COMMANDS_TABLE.put_item(Item=command)
    record_audit_event(
        family_id=family_id,
        actor_type="parent",
        actor_id=command["createdByParentId"],
        action="device_command.queued",
        target_type="device_command",
        target_id=command["commandId"],
        metadata={
            "childId": device["childId"],
            "deviceId": device_id,
            "commandType": command_type,
            "expiresAt": command["expiresAt"],
        },
        now=now,
    )
    return response(201, {"command": public_command(command)})


def query_queued_commands_for_device(device_id):
    result = DEVICE_COMMANDS_TABLE.query(
        IndexName="deviceId-index",
        KeyConditionExpression="deviceId = :deviceId",
        ExpressionAttributeValues={":deviceId": device_id},
    )
    commands = [
        public_command(command)
        for command in result.get("Items", [])
        if command.get("status") == "queued"
    ]
    return sorted(commands, key=lambda command: command["createdAt"])


def acknowledge_device_command(device, path_params, body):
    now = epoch_seconds()
    command_id = require_path_param(path_params, "commandId")
    command = DEVICE_COMMANDS_TABLE.get_item(Key={"commandId": command_id}).get("Item")
    if not command or command.get("deviceId") != device["deviceId"]:
        raise HttpError(404, "command_not_found", "Command was not found for this device.")

    ack_status = optional_string(body, "status") or "acknowledged"
    if ack_status not in {"acknowledged", "applied", "failed"}:
        raise HttpError(400, "invalid_command_status", "Command status must be acknowledged, applied, or failed.")

    values = {
        ":status": ack_status,
        ":acknowledgedAt": iso_time(now),
        ":acknowledgedByDeviceId": device["deviceId"],
        ":errorCode": optional_string(body, "errorCode"),
        ":diagnostics": optional_string(body, "diagnostics"),
    }
    DEVICE_COMMANDS_TABLE.update_item(
        Key={"commandId": command_id},
        UpdateExpression=(
            "SET #status = :status, acknowledgedAt = :acknowledgedAt, "
            "acknowledgedByDeviceId = :acknowledgedByDeviceId, errorCode = :errorCode, "
            "diagnostics = :diagnostics"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=values,
    )

    updated_command = {
        **command,
        "status": ack_status,
        "acknowledgedAt": values[":acknowledgedAt"],
        "acknowledgedByDeviceId": device["deviceId"],
        "errorCode": values[":errorCode"],
        "diagnostics": values[":diagnostics"],
    }
    record_audit_event(
        family_id=command["familyId"],
        actor_type="device",
        actor_id=device["deviceId"],
        action="device_command.acknowledged",
        target_type="device_command",
        target_id=command_id,
        metadata={
            "childId": command["childId"],
            "deviceId": device["deviceId"],
            "commandType": command["type"],
            "status": ack_status,
            "errorCode": values[":errorCode"],
        },
        now=now,
    )
    return response(200, {"command": public_command_ack(updated_command)})


def record_audit_event(family_id, actor_type, actor_id, action, target_type, target_id, metadata, now):
    AUDIT_EVENTS_TABLE.put_item(
        Item={
            "auditId": f"audit_{uuid.uuid4().hex}",
            "familyId": family_id,
            "actorType": actor_type,
            "actorId": actor_id,
            "action": action,
            "targetType": target_type,
            "targetId": target_id,
            "timestamp": iso_time(now),
            "metadata": metadata,
        }
    )


def public_command(command):
    return {
        "commandId": command["commandId"],
        "type": command["type"],
        "status": command["status"],
        "reason": command.get("reason"),
        "expiresAt": command.get("expiresAt"),
        "createdAt": command["createdAt"],
    }


def public_command_ack(command):
    payload = public_command(command)
    payload.update(
        {
            "acknowledgedAt": command.get("acknowledgedAt"),
            "acknowledgedByDeviceId": command.get("acknowledgedByDeviceId"),
            "errorCode": command.get("errorCode"),
            "diagnostics": command.get("diagnostics"),
        }
    )
    return payload


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


def require_date_query(query_params):
    value = query_params.get("date")
    if not isinstance(value, str) or not value.strip():
        raise HttpError(400, "missing_query_parameter", "Missing query parameter: date.")
    value = value.strip()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HttpError(400, "invalid_date", "Query parameter date must use YYYY-MM-DD.")
    return value


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


def parse_iso_time(value):
    if not isinstance(value, str):
        raise HttpError(400, "invalid_usage_event", "Usage event timestamps must be strings.")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise HttpError(400, "invalid_usage_event", "Usage event timestamps must use UTC ISO format.")


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
