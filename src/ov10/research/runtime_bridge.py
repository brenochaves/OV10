from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import parse, request

DEFAULT_BRIDGE_URL = os.environ.get(
    "OV10_BRIDGE_URL",
    "https://script.google.com/macros/s/AKfycbyyV_nNLy3jaTyBwZmEdFvyOR9JGjNk1Z_EFM1-WnNNi0s5RxWQI2EacyV285N_DCzU/exec",
)
DEFAULT_BRIDGE_KEY = os.environ.get(
    "OV10_BRIDGE_KEY",
    "ov10-bridge-20260312-b8d1f0f6",
)
DEFAULT_REFERENCE_SPREADSHEET_ID = "1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U"


class RuntimeBridgeError(RuntimeError):
    """Raised when the online runtime bridge returns an invalid or failed response."""


@dataclass(frozen=True)
class RuntimeBridgeClient:
    bridge_url: str = DEFAULT_BRIDGE_URL
    bridge_key: str = DEFAULT_BRIDGE_KEY
    spreadsheet_id: str = DEFAULT_REFERENCE_SPREADSHEET_ID

    def call(self, operation: str, **params: Any) -> dict[str, Any]:
        query = {
            "operation": operation,
            "bridgeKey": self.bridge_key,
        }
        if self.spreadsheet_id and "spreadsheetId" not in params:
            query["spreadsheetId"] = self.spreadsheet_id
        for key, value in params.items():
            if value is not None:
                query[key] = value
        url = self.bridge_url + "?" + parse.urlencode(query)
        with request.urlopen(url) as response:
            payload_text = response.read().decode("utf-8")
        return _parse_bridge_response(payload_text)


def create_debug_copy(
    client: RuntimeBridgeClient,
    copy_name_prefix: str = "OV10 Debug Copy",
) -> dict[str, Any]:
    payload = client.call("createDebugCopy", copyNamePrefix=copy_name_prefix)
    _require_string_field(payload, "copiedSpreadsheetId", "createDebugCopy response")
    _require_string_field(payload, "copiedName", "createDebugCopy response")
    _require_string_field(payload, "copiedUrl", "createDebugCopy response")
    return payload


def capture_remote_script_artifact(
    output_dir: Path,
    client: RuntimeBridgeClient,
    chunk_length: int = 50_000,
) -> dict[str, Any]:
    if chunk_length <= 0:
        raise ValueError("chunk_length must be positive.")

    summary = _validate_remote_script_summary(client.call("fetchRemoteScriptSummary"))
    total_length = summary["contentLength"]
    remote_script_version = summary["remoteScriptVersion"]
    captured_parts: list[str] = []

    for start in range(0, total_length, chunk_length):
        chunk = _validate_remote_script_chunk(
            client.call(
                "fetchRemoteScriptChunk",
                start=start,
                length=chunk_length,
            )
        )
        captured_parts.append(chunk["content"])

    content = "".join(captured_parts)
    actual_length = len(content)
    if actual_length != total_length:
        raise RuntimeBridgeError(
            f"Captured payload length mismatch: expected {total_length}, got {actual_length}."
        )

    actual_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    expected_sha256 = summary["sha256Hex"]
    if actual_sha256 != expected_sha256:
        raise RuntimeBridgeError(
            f"Captured payload hash mismatch: expected {expected_sha256}, got {actual_sha256}."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    payload_path = output_dir / f"{remote_script_version}.js"
    metadata_path = output_dir / f"{remote_script_version}.metadata.json"

    payload_path.write_text(content, encoding="utf-8")
    metadata = dict(summary)
    metadata["capturedLength"] = actual_length
    metadata["capturedSha256Hex"] = actual_sha256
    metadata["payloadPath"] = str(payload_path.resolve())
    metadata["metadataPath"] = str(metadata_path.resolve())
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata


def _parse_bridge_response(payload_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise RuntimeBridgeError("Bridge returned invalid JSON.") from exc

    root = _require_mapping(payload, "bridge response")
    ok_value = root.get("ok")
    if not isinstance(ok_value, bool):
        raise RuntimeBridgeError("Bridge response is missing boolean `ok`.")
    if not ok_value:
        error_payload = root.get("error")
        if isinstance(error_payload, Mapping):
            message = error_payload.get("message")
            if isinstance(message, str) and message.strip():
                raise RuntimeBridgeError(message)
        raise RuntimeBridgeError("Bridge call failed.")

    data = root.get("data")
    if not isinstance(data, dict):
        raise RuntimeBridgeError("Bridge returned a non-dict data payload.")
    return {str(key): value for key, value in data.items()}


def _validate_remote_script_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "remoteScriptVersion": _require_string_field(
            payload,
            "remoteScriptVersion",
            "fetchRemoteScriptSummary response",
        ),
        "contentLength": _require_int_field(
            payload,
            "contentLength",
            "fetchRemoteScriptSummary response",
        ),
        "sha256Hex": _require_string_field(
            payload,
            "sha256Hex",
            "fetchRemoteScriptSummary response",
        ),
        "remoteUrl": _require_string_field(
            payload,
            "remoteUrl",
            "fetchRemoteScriptSummary response",
        ),
    }


def _validate_remote_script_chunk(payload: dict[str, Any]) -> dict[str, Any]:
    _require_int_field(payload, "start", "fetchRemoteScriptChunk response")
    _require_int_field(payload, "chunkLength", "fetchRemoteScriptChunk response")
    _require_int_field(payload, "totalLength", "fetchRemoteScriptChunk response")
    return {
        **payload,
        "content": _require_string_field(
            payload,
            "content",
            "fetchRemoteScriptChunk response",
        ),
    }


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeBridgeError(f"{field_name} must be a JSON object.")
    return value


def _require_string_field(payload: Mapping[str, object], field_name: str, context: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeBridgeError(f"{context} is missing non-empty string `{field_name}`.")
    return value


def _require_int_field(payload: Mapping[str, object], field_name: str, context: str) -> int:
    value = payload.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeBridgeError(f"{context} is missing integer `{field_name}`.")
    return value
