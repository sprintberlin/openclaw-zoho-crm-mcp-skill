#!/usr/bin/env python3
"""
List Zoho CRM accounts (companies) or search by name.
Uses getRecords via mcporter, with automatic pagination.

Setup:
  export ZOHO_MCP_URL="https://your-org-zoho-crm-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message"

Usage:
  python3 scripts/list_accounts.py                         # Accounts with a website, as table
  python3 scripts/list_accounts.py --json                  # Raw JSON output
  python3 scripts/list_accounts.py --search "Acme"         # Search by company name
  python3 scripts/list_accounts.py --all                   # All accounts (no default filter)
  python3 scripts/list_accounts.py --fields Account_Name,Website,Google_Drive_URL,Trello_URL

Custom fields:
  --fields lets you list any Zoho field API names (comma-separated), including
  org-specific custom fields. Field API names appear as-is in the header unless
  a label exists.

Default fields: Account_Name, Website, Phone, Billing_City, Billing_Country, Industry, id
"""

import subprocess
import json
import sys
import os

MCP_URL = os.environ.get("ZOHO_MCP_URL", "")
TOOL = "ZohoCRM_getRecords"

DEFAULT_FIELDS = ["Account_Name", "Website", "Phone", "Billing_City", "Billing_Country", "Industry", "id"]

FIELD_LABELS = {
    "Account_Name": "Company",
    "Website": "Website",
    "Phone": "Phone",
    "Billing_City": "City",
    "Billing_Country": "Country",
    "Industry": "Industry",
    "Google_Drive_URL": "Drive URL",
    "Trello_URL": "Trello URL",
    "Trello_ID": "Trello ID",
    "id": "CRM ID",
}


def _mcporter_call(tool, args):
    """Call mcporter directly (no shell) to avoid expanding the credential-bearing URL."""
    if not MCP_URL:
        print("Error: ZOHO_MCP_URL not set. Please set the environment variable.", file=sys.stderr)
        print("  export ZOHO_MCP_URL='https://your-org-zoho-crm-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message'", file=sys.stderr)
        sys.exit(1)

    cmd = ["mcporter", "call", f"{MCP_URL}.{tool}", "--args", json.dumps(args, ensure_ascii=False)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout + result.stderr}


def normalize_crm_result(result):
    """Return a consistent (data, info) tuple across CRM MCP response variants."""
    if "error" in result:
        return None, None

    payload = result.get("data", [])
    if isinstance(payload, dict):
        if "data" in payload:
            return payload.get("data") or [], payload.get("info", {})
        if "message" in payload:
            return [], {}

    if isinstance(payload, list):
        return payload, result.get("info", {})

    return [], result.get("info", {})


def query_accounts_page(fields, page=1, per_page=200):
    """Fetch one accounts page using getRecords."""
    args = {
        "path_variables": {"module": "Accounts"},
        "query_params": {"fields": ",".join(fields), "page": page, "per_page": per_page},
    }
    return _mcporter_call(TOOL, args)


def query_all_accounts(fields, per_page=200):
    """Fetch all accounts using paginated getRecords queries."""
    all_data = []
    page = 1

    while True:
        result = query_accounts_page(fields, page=page, per_page=per_page)
        if "error" in result:
            return result

        data, info = normalize_crm_result(result)
        if data is None:
            return {"error": "CRM response could not be normalized"}

        all_data.extend(data)
        if not info.get("more_records") or not data:
            break

        page += 1

    return {"data": all_data, "info": {"count": len(all_data), "more_records": False}}


def extract_field(row, field):
    val = row.get(field, "")
    if not val:
        return "-"
    if isinstance(val, dict):
        return val.get("name", str(val))
    return str(val)


def print_table(data, fields):
    if not data:
        print("No accounts found.")
        return

    col_widths = {}
    for field in fields:
        label = FIELD_LABELS.get(field, field)
        max_val_len = max((len(extract_field(row, field)) for row in data), default=0)
        col_widths[field] = max(len(label), min(max_val_len, 50))

    header_parts = [FIELD_LABELS.get(f, f).ljust(col_widths[f]) for f in fields]
    print(" | ".join(header_parts))
    print("-+-".join("-" * col_widths[f] for f in fields))

    for row in data:
        parts = []
        for field in fields:
            val = extract_field(row, field)
            if len(val) > 50:
                val = val[:47] + "..."
            parts.append(val.ljust(col_widths[field]))
        print(" | ".join(parts))

    print(f"\n{len(data)} record(s)")


def main():
    args = sys.argv[1:]
    json_mode = "--json" in args
    show_all = "--all" in args
    search_term = None
    custom_fields = None

    for i, arg in enumerate(args):
        if arg == "--search" and i + 1 < len(args):
            search_term = args[i + 1]
        elif arg == "--fields" and i + 1 < len(args):
            custom_fields = [f.strip() for f in args[i + 1].split(",") if f.strip()]
        elif arg == "--where":
            print("Error: --where requires COQL. Use search_records.py --coql on MCP servers with executeCOQLQuery enabled.", file=sys.stderr)
            sys.exit(2)

    fields = custom_fields if custom_fields else DEFAULT_FIELDS

    result = query_all_accounts(fields)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    data, info = normalize_crm_result(result)

    if search_term:
        search_lower = search_term.lower()
        data = [row for row in data if search_lower in (row.get("Account_Name", "") or "").lower()]
    elif not show_all:
        data = [row for row in data if row.get("Website")]

    if json_mode:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_table(data, fields)

    if info.get("more_records"):
        print(f"\nMore records available (showing {info.get('count', '?')}).")


if __name__ == "__main__":
    main()
