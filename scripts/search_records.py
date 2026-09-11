#!/usr/bin/env python3
"""
Search records in any Zoho CRM module via mcporter.
Uses ZohoCRM_searchRecords and executeCOQLQuery.

Setup:
  export ZOHO_MCP_URL="https://your-org-zoho-crm-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message"

Usage:
  python3 scripts/search_records.py Contacts "Smith"
  python3 scripts/search_records.py Accounts "Acme Corp"
  python3 scripts/search_records.py Deals "Project X"
  python3 scripts/search_records.py Leads "Leadname" --json
  python3 scripts/search_records.py Leads --fields id,Last_Name,Company,Email --json
  python3 scripts/search_records.py Contacts --coql "Email != ''"
"""

import argparse
import json
import os
import subprocess
import sys

MCP_URL = os.environ.get("ZOHO_MCP_URL", "")


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
    parser = argparse.ArgumentParser(
        description="Search records in any Zoho CRM module via mcporter."
    )
    parser.add_argument(
        "module",
        help="CRM module name (e.g. Contacts, Accounts, Deals, Leads, Products)",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="search term (positional alternative to --search)",
    )
    parser.add_argument(
        "--search",
        metavar="TERM",
        help="search term for module name/last name field",
    )
    parser.add_argument(
        "--coql",
        metavar="WHERE",
        help="custom COQL WHERE clause",
    )
    parser.add_argument(
        "--fields",
        type=comma_separated_fields,
        help="comma-separated field API names",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print JSON instead of a table",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        help="maximum number of records to return and query limit",
    )
    parser.add_argument(
        "--page-size",
        type=positive_int,
        default=100,
        help="request page size (default: 100)",
    )
    parser.add_argument(
        "--timeout",
        type=positive_int,
        default=30,
        help="MCP call timeout in seconds (default: 30)",
    )
    return parser


def mcporter_call(tool, args, timeout=30):
    mcp_url = os.environ.get("ZOHO_MCP_URL") or MCP_URL
    if not mcp_url:
        print("Error: ZOHO_MCP_URL not set. Please set the environment variable.", file=sys.stderr)
        print("  export ZOHO_MCP_URL='https://your-org-zoho-crm-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message'", file=sys.stderr)
        sys.exit(1)

    cmd = [
        "mcporter",
        "call",
        f"{mcp_url}.{tool}",
        "--args",
        json.dumps(args, ensure_ascii=False),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"error": "mcporter executable not found"}
    except subprocess.TimeoutExpired:
        return {"error": "mcporter call timed out"}

    if result.returncode != 0:
        return {"error": result.stderr.strip() or "mcporter call failed"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout + result.stderr}


def normalize_crm_result(result):
    """Return a records list across CRM MCP response variants.

    Records may arrive directly under "data" as a list, or nested as
    {"data": {"data": [...], "info": {...}}}, or wrapped with a "message"
    (e.g. no records). This normalizes all of them to a plain list.
    """
    if not isinstance(result, dict):
        return []
    payload = result.get("data", [])
    if isinstance(payload, dict):
        if "data" in payload:
            return payload.get("data") or []
        if "message" in payload:
            return []
    if isinstance(payload, list):
        return payload
    return []


def search_module(module, search_term, limit=None, page_size=100, timeout=30):
    """Search a module by name field."""
    name_field_map = {
        "Contacts": "Last_Name",
        "Accounts": "Account_Name",
        "Deals": "Deal_Name",
        "Leads": "Last_Name",
        "Products": "Product_Name",
    }
    name_field = name_field_map.get(module, "Name")
    criteria = f"({name_field}:equals:{search_term})"
    query_params = {"criteria": criteria}
    query_params["per_page"] = min(limit or page_size, 200)
    args = {
        "path_variables": {"module": module},
        "query_params": query_params,
    }
    return mcporter_call("ZohoCRM_searchRecords", args, timeout=timeout)


def default_fields_for_module(module):
    """Return broadly useful fields because Zoho COQL does not support SELECT *."""
    return {
        "Contacts": ["id", "Full_Name", "Email", "Mobile", "Phone", "Account_Name"],
        "Accounts": ["id", "Account_Name", "Website", "Phone", "Billing_City"],
        "Deals": ["id", "Deal_Name", "Stage", "Amount", "Closing_Date", "Account_Name"],
        "Leads": ["id", "Last_Name", "First_Name", "Company", "Email", "Phone", "Lead_Status"],
        "Products": ["id", "Product_Name", "Product_Code", "Unit_Price"],
    }.get(module, ["id"])


def coql_query(module, fields, where_clause, limit=100, timeout=30):
    """Execute a COQL query on a module."""
    query = f"SELECT {', '.join(fields)} FROM {module}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += f" LIMIT {limit}"
    return mcporter_call(
        "ZohoCRM_executeCOQLQuery",
        {"body": {"select_query": query}},
        timeout=timeout,
    )


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    module = args.module
    search_term = args.search or args.query
    coql_where = args.coql
    fields = args.fields or default_fields_for_module(module)
    coql_limit = args.limit or args.page_size

    if coql_where is not None:
        result = coql_query(module, fields, coql_where, limit=coql_limit, timeout=args.timeout)
    elif search_term:
        result = search_module(
            module,
            search_term,
            limit=args.limit,
            page_size=args.page_size,
            timeout=args.timeout,
        )
    else:
        result = coql_query(module, fields, "", limit=coql_limit, timeout=args.timeout)

    if "error" in result or result.get("status") in {"error", "failure"}:
        print(f"Error: {result.get('error') or result.get('data') or result.get('message')}", file=sys.stderr)
        return 1

    data = normalize_crm_result(result)
    if args.limit is not None:
        data = data[: args.limit]

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        if not data:
            print(f"No {module} records found.")
            return 0
        keys = list(data[0].keys())[:8]
        col_widths = {k: max(len(k), min(max(len(str(row.get(k, ""))) for row in data), 40)) for k in keys}

        print(" | ".join(k.ljust(col_widths[k]) for k in keys))
        print("-+-".join("-" * col_widths[k] for k in keys))
        for row in data:
            vals = []
            for k in keys:
                v = str(row.get(k, "") or "-")
                if len(v) > 40:
                    v = v[:37] + "..."
                vals.append(v.ljust(col_widths[k]))
            print(" | ".join(vals))
        print(f"\n{len(data)} record(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
