#!/usr/bin/env python3
"""List or search Zoho CRM accounts through mcporter."""

import argparse
import json
import os
import subprocess
import sys

MCP_URL = os.environ.get("ZOHO_MCP_URL", "")
COQL_TOOL = "ZohoCRM_executeCOQLQuery"

DEFAULT_FIELDS = ["Account_Name", "Website", "Phone", "Billing_City", "Billing_Country", "Industry", "id"]

FIELD_LABELS = {
    "Account_Name": "Company",
    "Website": "Website",
    "Phone": "Phone",
    "Billing_City": "City",
    "Billing_Country": "Country",
    "Industry": "Industry",
    "id": "CRM ID",
}


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def comma_separated_fields(value):
    fields = [field.strip() for field in value.split(",") if field.strip()]
    if not fields:
        raise argparse.ArgumentTypeError("must contain at least one field API name")
    return fields


def build_parser():
    parser = argparse.ArgumentParser(description="List or search Zoho CRM accounts.")
    parser.add_argument("--search", metavar="NAME", help="filter accounts by name, case-insensitively")
    parser.add_argument("--all", action="store_true", help="include accounts without a website")
    parser.add_argument("--where", metavar="COQL", help="custom COQL WHERE clause")
    parser.add_argument("--fields", type=comma_separated_fields, help="comma-separated field API names")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--limit", type=positive_int, help="return at most this many accounts")
    parser.add_argument("--page-size", type=positive_int, default=100, help="COQL page size (default: 100)")
    parser.add_argument("--timeout", type=positive_int, default=30, help="MCP call timeout in seconds (default: 30)")
    return parser


def _mcporter_call(tool, args, timeout=30):
    """Call mcporter directly without a shell."""
    if not MCP_URL:
        print("Error: ZOHO_MCP_URL not set. Please set the environment variable.", file=sys.stderr)
        sys.exit(1)

    cmd = ["mcporter", "call", f"{MCP_URL}.{tool}", "--args", json.dumps(args, ensure_ascii=False)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"error": "mcporter executable not found"}
    except subprocess.TimeoutExpired:
        return {"error": "mcporter call timed out"}

    if result.returncode != 0:
        return {"error": result.stderr.strip() or "mcporter call failed"}
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stderr.strip() or "mcporter returned invalid JSON"}
    if parsed.get("status") in {"error", "failure"}:
        return {"error": parsed.get("error") or parsed.get("data") or parsed.get("message") or "Zoho CRM request failed"}
    return parsed


def normalize_crm_result(result):
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


def query_accounts_page(fields, where_clause, offset=0, limit=100, timeout=30):
    fields_str = ", ".join(fields)
    query = f"SELECT {fields_str} FROM Accounts"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += f" ORDER BY Account_Name LIMIT {offset}, {limit}"
    return _mcporter_call(COQL_TOOL, {"body": {"select_query": query}}, timeout=timeout)


def query_all_accounts(fields, where_clause, per_page=100, max_records=None, timeout=30):
    all_data = []
    offset = 0

    while True:
        request_limit = per_page
        if max_records is not None:
            remaining = max_records - len(all_data)
            if remaining <= 0:
                break
            request_limit = min(request_limit, remaining)

        result = query_accounts_page(
            fields,
            where_clause,
            offset=offset,
            limit=request_limit,
            timeout=timeout,
        )
        if "error" in result:
            return result

        data, info = normalize_crm_result(result)
        if data is None:
            return {"error": "CRM response could not be normalized"}

        all_data.extend(data)
        if max_records is not None and len(all_data) >= max_records:
            break
        if not info.get("more_records") or not data:
            break

        offset += len(data)

    if max_records is not None:
        all_data = all_data[:max_records]
    return {"data": all_data, "info": {"count": len(all_data), "more_records": False}}


def extract_field(row, field):
    val = row.get(field, "")
    if not val:
        return "-"
    if isinstance(val, dict):
        return str(val.get("name") or val)
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

    print(" | ".join(FIELD_LABELS.get(field, field).ljust(col_widths[field]) for field in fields))
    print("-+-".join("-" * col_widths[field] for field in fields))

    for row in data:
        parts = []
        for field in fields:
            val = extract_field(row, field)
            if len(val) > 50:
                val = val[:47] + "..."
            parts.append(val.ljust(col_widths[field]))
        print(" | ".join(parts))

    print(f"\n{len(data)} record(s)")


def main(argv=None):
    args = build_parser().parse_args(argv)
    fields = args.fields or DEFAULT_FIELDS

    if args.where is not None:
        where = args.where
    elif args.search or args.all:
        where = "Account_Name != ''"
    else:
        where = "Website != ''"

    # Account search currently filters client-side; do not apply a fetch limit before filtering.
    query_limit = None if args.search else args.limit
    result = query_all_accounts(
        fields,
        where,
        per_page=args.page_size,
        max_records=query_limit,
        timeout=args.timeout,
    )
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    data, info = normalize_crm_result(result)
    if args.search:
        search_lower = args.search.lower()
        data = [row for row in data if search_lower in (row.get("Account_Name", "") or "").lower()]
        if args.limit is not None:
            data = data[: args.limit]

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_table(data, fields)

    if info.get("more_records"):
        print(f"\nMore records available (showing {len(data)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
