"""Credential-free CLI tests for scripts/search_records.py."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "search_records.py"


def load_search_records_module():
    spec = importlib.util.spec_from_file_location("search_records_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SearchRecordsCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.search_records = load_search_records_module()

    def run_script(self, *arguments):
        env = os.environ.copy()
        env.pop("ZOHO_MCP_URL", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_help_does_not_require_credentials_or_make_a_request(self):
        result = self.run_script("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_unknown_and_missing_arguments_use_argparse_exit_code_2(self):
        cases = ((), ("Contacts", "--unknown"), ("Contacts", "--search"))

        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.run_script(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage:", result.stderr)

    def test_positional_search_is_compatible_and_limit_bounds_request_and_output(self):
        calls = []

        def fake_mcporter_call(tool, arguments, timeout=30):
            calls.append((tool, arguments, timeout))
            return {"data": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}

        stdout = io.StringIO()
        with patch.object(self.search_records, "mcporter_call", side_effect=fake_mcporter_call):
            with contextlib.redirect_stdout(stdout):
                exit_code = self.search_records.main(
                    ["Contacts", "Smith", "--limit", "2", "--json"]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "ZohoCRM_searchRecords")
        self.assertEqual(
            calls[0][1]["query_params"],
            {"criteria": "(Last_Name:equals:Smith)", "per_page": 2},
        )
        self.assertEqual(calls[0][2], 30)
        self.assertEqual(json.loads(stdout.getvalue()), [{"id": "1"}, {"id": "2"}])

    def test_coql_limit_bounds_request_and_output(self):
        calls = []

        def fake_mcporter_call(tool, arguments, timeout=30):
            calls.append((tool, arguments, timeout))
            return {"data": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}

        stdout = io.StringIO()
        with patch.object(self.search_records, "mcporter_call", side_effect=fake_mcporter_call):
            with contextlib.redirect_stdout(stdout):
                exit_code = self.search_records.main(
                    ["Contacts", "--coql", "Email != ''", "--limit", "2", "--json"]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "ZohoCRM_executeCOQLQuery")
        self.assertEqual(
            calls[0][1]["body"]["select_query"],
            "SELECT id, Full_Name, Email, Mobile, Phone, Account_Name FROM Contacts "
            "WHERE Email != '' LIMIT 2",
        )
        self.assertEqual(json.loads(stdout.getvalue()), [{"id": "1"}, {"id": "2"}])


if __name__ == "__main__":
    unittest.main()
