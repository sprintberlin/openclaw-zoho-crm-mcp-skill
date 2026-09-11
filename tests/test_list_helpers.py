"""Credential-free tests for the contact and account helper CLIs."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPOSITORY / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"{path.stem}_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HelperCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contacts = load_script("list_contacts.py")
        cls.accounts = load_script("list_accounts.py")

    def run_script(self, script, *arguments):
        env = os.environ.copy()
        env.pop("ZOHO_MCP_URL", None)
        return subprocess.run(
            [sys.executable, str(REPOSITORY / "scripts" / script), *arguments],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_help_needs_no_credentials(self):
        for script in ("list_contacts.py", "list_accounts.py"):
            with self.subTest(script=script):
                result = self.run_script(script, "--help")
                self.assertEqual(result.returncode, 0)
                self.assertIn("usage:", result.stdout)
                self.assertEqual(result.stderr, "")

    def test_unknown_and_missing_options_use_exit_code_2(self):
        cases = (
            ("list_contacts.py", ("--unknown",)),
            ("list_contacts.py", ("--search",)),
            ("list_accounts.py", ("--unknown",)),
            ("list_accounts.py", ("--where",)),
        )
        for script, arguments in cases:
            with self.subTest(script=script, arguments=arguments):
                result = self.run_script(script, *arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage:", result.stderr)

    def test_contact_limit_bounds_first_request_and_result(self):
        rows = [{"id": str(index), "Last_Name": "Example"} for index in range(1, 5)]
        calls = []

        def fake_page(fields, offset=0, limit=100, timeout=30):
            calls.append({"fields": fields, "offset": offset, "limit": limit, "timeout": timeout})
            return {"data": rows, "info": {"more_records": True}}

        with patch.object(self.contacts, "query_contacts_page", side_effect=fake_page):
            result = self.contacts.query_all_contacts(
                ["id", "Last_Name"], per_page=100, max_records=3, timeout=17
            )

        self.assertEqual(calls, [{"fields": ["id", "Last_Name"], "offset": 0, "limit": 3, "timeout": 17}])
        self.assertEqual(len(result["data"]), 3)

    def test_account_limit_bounds_first_request_and_result(self):
        rows = [{"id": str(index), "Account_Name": "Example"} for index in range(1, 5)]
        calls = []

        def fake_page(fields, where_clause, offset=0, limit=100, timeout=30):
            calls.append(
                {
                    "fields": fields,
                    "where": where_clause,
                    "offset": offset,
                    "limit": limit,
                    "timeout": timeout,
                }
            )
            return {"data": rows, "info": {"more_records": True}}

        with patch.object(self.accounts, "query_accounts_page", side_effect=fake_page):
            result = self.accounts.query_all_accounts(
                ["id", "Account_Name"],
                "Account_Name != ''",
                per_page=100,
                max_records=3,
                timeout=19,
            )

        self.assertEqual(
            calls,
            [
                {
                    "fields": ["id", "Account_Name"],
                    "where": "Account_Name != ''",
                    "offset": 0,
                    "limit": 3,
                    "timeout": 19,
                }
            ],
        )
        self.assertEqual(len(result["data"]), 3)


if __name__ == "__main__":
    unittest.main()
