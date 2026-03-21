from __future__ import annotations

import io
import json
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


class CliEntrypointTests(unittest.TestCase):
    def test_module_entrypoint_executes_main(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "synthetic"
            stdout = io.StringIO()
            argv = [
                "ov10.cli",
                "generate-synthetic-status-invest-matrix",
                str(output_dir),
            ]
            original_module = sys.modules.pop("ov10.cli", None)
            with patch.object(sys, "argv", argv):
                with redirect_stdout(stdout):
                    try:
                        with self.assertRaises(SystemExit) as exit_context:
                            runpy.run_module("ov10.cli", run_name="__main__")
                    finally:
                        if original_module is not None:
                            sys.modules["ov10.cli"] = original_module

            self.assertTrue(output_dir.exists())
            payload = json.loads(stdout.getvalue())
            self.assertGreaterEqual(len(payload), 1)

        self.assertEqual(exit_context.exception.code, 0)
