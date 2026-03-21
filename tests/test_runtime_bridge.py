from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ov10.research import RuntimeBridgeClient, capture_remote_script_artifact, create_debug_copy


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class RuntimeBridgeTests(unittest.TestCase):
    def test_capture_remote_script_artifact_writes_verified_payload(self) -> None:
        payload_text = "const answer = 42;\nfunction ping() { return answer; }\n"
        payload_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
        responses = [
            {
                "ok": True,
                "data": {
                    "remoteScriptVersion": "v61_controle_64",
                    "contentLength": len(payload_text),
                    "sha256Hex": payload_hash,
                    "remoteUrl": "https://example.invalid/script.js",
                },
            },
            {
                "ok": True,
                "data": {
                    "start": 0,
                    "chunkLength": 20,
                    "totalLength": len(payload_text),
                    "content": payload_text[:20],
                },
            },
            {
                "ok": True,
                "data": {
                    "start": 20,
                    "chunkLength": 20,
                    "totalLength": len(payload_text),
                    "content": payload_text[20:40],
                },
            },
            {
                "ok": True,
                "data": {
                    "start": 40,
                    "chunkLength": len(payload_text[40:]),
                    "totalLength": len(payload_text),
                    "content": payload_text[40:],
                },
            },
        ]
        requested_urls: list[str] = []

        def fake_urlopen(url: str) -> FakeHTTPResponse:
            requested_urls.append(url)
            return FakeHTTPResponse(responses.pop(0))

        client = RuntimeBridgeClient(
            bridge_url="https://bridge.example/exec",
            bridge_key="secret-key",
            spreadsheet_id="spreadsheet-1",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("ov10.research.runtime_bridge.request.urlopen", side_effect=fake_urlopen):
                metadata = capture_remote_script_artifact(
                    Path(temp_dir),
                    client=client,
                    chunk_length=20,
                )

            payload_path = Path(metadata["payloadPath"])
            metadata_path = Path(metadata["metadataPath"])

            self.assertTrue(payload_path.exists())
            self.assertTrue(metadata_path.exists())
            self.assertEqual(payload_path.read_text(encoding="utf-8"), payload_text)
            self.assertEqual(metadata["capturedSha256Hex"], payload_hash)
            self.assertEqual(len(requested_urls), 4)
            self.assertIn("operation=fetchRemoteScriptSummary", requested_urls[0])
            self.assertIn("bridgeKey=secret-key", requested_urls[0])
            self.assertIn("start=0", requested_urls[1])
            self.assertIn("start=20", requested_urls[2])
            self.assertIn("start=40", requested_urls[3])

    def test_create_debug_copy_passes_copy_name_prefix(self) -> None:
        requested_urls: list[str] = []

        def fake_urlopen(url: str) -> FakeHTTPResponse:
            requested_urls.append(url)
            return FakeHTTPResponse(
                {
                    "ok": True,
                    "data": {
                        "copiedSpreadsheetId": "copy-123",
                        "copiedName": "Nightly Debug Copy",
                        "copiedUrl": "https://docs.google.com/spreadsheets/d/copy-123/edit",
                    },
                }
            )

        client = RuntimeBridgeClient(
            bridge_url="https://bridge.example/exec",
            bridge_key="secret-key",
            spreadsheet_id="spreadsheet-1",
        )

        with patch("ov10.research.runtime_bridge.request.urlopen", side_effect=fake_urlopen):
            payload = create_debug_copy(client, copy_name_prefix="Nightly Debug Copy")

        self.assertEqual(payload["copiedSpreadsheetId"], "copy-123")
        self.assertEqual(len(requested_urls), 1)
        self.assertIn("operation=createDebugCopy", requested_urls[0])
        self.assertIn("copyNamePrefix=Nightly+Debug+Copy", requested_urls[0])

    def test_runtime_bridge_rejects_invalid_json_shape(self) -> None:
        def fake_urlopen(url: str) -> FakeHTTPResponse:
            del url
            return FakeHTTPResponse({"ok": True, "data": []})

        client = RuntimeBridgeClient(
            bridge_url="https://bridge.example/exec",
            bridge_key="secret-key",
            spreadsheet_id="spreadsheet-1",
        )

        with patch("ov10.research.runtime_bridge.request.urlopen", side_effect=fake_urlopen):
            with self.assertRaisesRegex(
                RuntimeError,
                "Bridge returned a non-dict data payload.",
            ):
                create_debug_copy(client, copy_name_prefix="Nightly Debug Copy")

    def test_capture_remote_script_artifact_rejects_missing_summary_fields(self) -> None:
        def fake_urlopen(url: str) -> FakeHTTPResponse:
            del url
            return FakeHTTPResponse(
                {
                    "ok": True,
                    "data": {
                        "remoteScriptVersion": "v61_controle_64",
                        "sha256Hex": "abc123",
                        "remoteUrl": "https://example.invalid/script.js",
                    },
                }
            )

        client = RuntimeBridgeClient(
            bridge_url="https://bridge.example/exec",
            bridge_key="secret-key",
            spreadsheet_id="spreadsheet-1",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("ov10.research.runtime_bridge.request.urlopen", side_effect=fake_urlopen):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "fetchRemoteScriptSummary response is missing integer `contentLength`.",
                ):
                    capture_remote_script_artifact(
                        Path(temp_dir),
                        client=client,
                        chunk_length=20,
                    )
