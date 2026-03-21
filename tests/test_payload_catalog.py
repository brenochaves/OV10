from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ov10.research import analyze_remote_script_artifact, extract_function_catalog_entries


class PayloadCatalogTests(unittest.TestCase):
    def test_extract_function_catalog_entries_classifies_major_modules(self) -> None:
        payload = """
        function Portfolio() {}
        function portfolioDefinirAtivos() {}
        function obterCaixaJSON() {}
        function calcularDARF() {}
        function validarIDPlanilha() {}
        function html_alpha() {}
        function helperGeral() {}
        """

        entries = {entry.name: entry for entry in extract_function_catalog_entries(payload)}

        self.assertIn("sheet_descriptors", entries["Portfolio"].modules)
        self.assertIn("portfolio_positions", entries["portfolioDefinirAtivos"].modules)
        self.assertIn("cash_brokers", entries["obterCaixaJSON"].modules)
        self.assertIn("fiscal", entries["calcularDARF"].modules)
        self.assertIn("alpha_licensing", entries["validarIDPlanilha"].modules)
        self.assertIn("ui_and_menu", entries["html_alpha"].modules)
        self.assertEqual(entries["helperGeral"].modules, ("utilities",))

    def test_analyze_remote_script_artifact_writes_catalog_json(self) -> None:
        payload = """
        function Portfolio() {}
        function portfolioDefinirAtivos() {}
        function obterCaixaJSON() {}
        function calcularDARF() {}
        function validarIDPlanilha() {}
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.js"
            output_path = Path(temp_dir) / "payload.catalog.json"
            payload_path.write_text(payload, encoding="utf-8")

            catalog = analyze_remote_script_artifact(payload_path, output_path=output_path)

            self.assertEqual(catalog["functionCount"], 5)
            self.assertTrue(output_path.exists())

            persisted = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["payloadPath"], str(payload_path.resolve()))
            portfolio_ref = persisted["selectedReferences"]["portfolioDefinirAtivos"]
            cash_ref = persisted["selectedReferences"]["obterCaixaJSON"]
            self.assertIn("portfolio_positions", portfolio_ref["modules"])
            self.assertIn("cash_brokers", cash_ref["modules"])
