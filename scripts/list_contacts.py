#!/usr/bin/env python3
"""List or search Zoho CRM contacts through mcporter."""

import argparse
import json
import os
import subprocess
import sys

MCP_URL = os.environ.get("ZOHO_MCP_URL", "")
TOOL = "ZohoCRM_searchRecords"
COQL_TOOL = "ZohoCRM_executeCOQLQuery"

DEFAULT_FIELDS = ["Full_Name", "Email", "Mobile", "Phone", "Account_Name", "Owner"]
COQL_BASE_FIELDS = ["First_Name", "Last_Name", "id"]

FIELD_LABELS = {
    "Full_Name": "Name",
    "First_Name": "First Name",
    "Last_Name": "Last Name",
    "Email": "Email",
    "Mobile": "Mobile",
    "Phone": "Phone",
    "Account_Name": "Company",
    "Owner": "Owner",
    "Designation": "Title",
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
    parser = argparse.ArgumentParser(description="List or search Zoho CRM contacts.")
    parser.add_argument("--search", metavar="LAST_NAME", help="search by exact last name")
    parser.add_argument("--fields", type=comma_separated_fields, help="comma-separated field API names")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--full", action="store_true", help="with --json, print complete search records")
    parser.add_argument("--limit", type=positive_int, help="return at most this many contacts")
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


def query_contacts_page(fields, offset=0, limit=100, timeout=30):
    fields_str = ", ".join(fields)
    query = (
        f"SELECT {fields_str} FROM Contacts WHERE Last_Name != '' "
        f"ORDER BY Last_Name LIMIT {offset}, {limit}"
    )
    return _mcporter_call(COQL_TOOL, {"body": {"select_query": query}}, timeout=timeout)


def query_all_contacts(fields, per_page=100, max_records=None, timeout=30):
    all_data = []
    offset = 0

    while True:
        request_limit = per_page
        if max_records is not None:
            remaining = max_records - len(all_data)
            if remaining <= 0:
                break
            request_limit = min(request_limit, remaining)

        result = query_contacts_page(fields, offset=offset, limit=request_limit, timeout=timeout)
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


def search_contacts_by_name(last_name, limit=None, page_size=100, timeout=30):
    criteria = f"(Last_Name:equals:{last_name})"
    args = {
        "path_variables": {"module": "Contacts"},
        "query_params": {"criteria": criteria, "page": 1, "per_page": min(limit or page_size, 200)},
    }
    return _mcporter_call(TOOL, args, timeout=timeout)


def extract_table_field(contact, field):
    val = contact.get(field, "")
    if not val:
        return "-"
    if isinstance(val, dict):
        return str(val.get("name") or val)
    return str(val)


def print_table(data, fields):
    if not data:
        print("No contacts found.")
        return

    col_widths = {}
    for field in fields:
        label = FIELD_LABELS.get(field, field)
        max_val_len = max((len(extract_table_field(row, field)) for row in data), default=0)
        col_widths[field] = max(len(label), min(max_val_len, 50))

    print(" | ".join(FIELD_LABELS.get(field, field).ljust(col_widths[field]) for field in fields))
    print("-+-".join("-" * col_widths[field] for field in fields))

    for row in data:
        parts = []
        for field in fields:
            val = extract_table_field(row, field)
            if len(val) > 50:
                val = val[:47] + "..."
            parts.append(val.ljust(col_widths[field]))
        print(" | ".join(parts))

    print(f"\n{len(data)} contact(s)")


def main(argv=None):
    args = build_parser().parse_args(argv)
    table_fields = args.fields or DEFAULT_FIELDS

    if args.search:
        result = search_contacts_by_name(args.search, args.limit, args.page_size, args.timeout)
        data, info = normalize_crm_result(result)
        if data is None:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1
        if args.limit is not None:
            data = data[: args.limit]
    else:
        coql_fields = list(dict.fromkeys(table_fields + COQL_BASE_FIELDS))
        result = query_all_contacts(
            coql_fields,
            per_page=args.page_size,
            max_records=args.limit,
            timeout=args.timeout,
        )
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1
        data, info = normalize_crm_result(result)

    if args.json:
        if args.full:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            simplified = [{field: row.get(field) for field in table_fields} for row in data]
            print(json.dumps(simplified, indent=2, ensure_ascii=False))
    else:
        print_table(data, table_fields)

    if info.get("more_records"):
        print(f"\nMore records available (showing {len(data)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
