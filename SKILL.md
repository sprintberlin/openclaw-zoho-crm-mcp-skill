---
name: "zoho-crm-mcp"
description: "Zoho CRM via MCP with action catalog, least-privilege profiles, COQL, helper scripts, and verified record workflows."
---

# Zoho CRM MCP

Use Zoho CRM through an MCP endpoint from `mcp.zoho.eu`. This skill is the canonical home for CRM-specific MCP action documentation and least-privilege action profiles.

Source: [sprintberlin/openclaw-zoho-crm-mcp-skill](https://github.com/sprintberlin/openclaw-zoho-crm-mcp-skill)

## Requirements

- A Zoho CRM MCP endpoint from `mcp.zoho.eu`
- `mcporter`
- `ZOHO_MCP_URL` for the bundled scripts

Treat the endpoint as a credential. Never print it, commit it, or copy it into tickets, prompts, or chats.

## First setup

1. Create or open a Zoho CRM connection at `mcp.zoho.eu`.
2. Select only the required Actions. Start with [references/ACTION_PROFILES.md](references/ACTION_PROFILES.md).
3. Use [references/ZOHO_CRM_MCP_ACTIONS.md](references/ZOHO_CRM_MCP_ACTIONS.md) only when a profile lacks a required Action.
4. Store the endpoint securely and expose it to the local process as `ZOHO_MCP_URL`.
5. Inspect the live server before relying on an Action:

```bash
mcporter list "$ZOHO_MCP_URL"
```

The catalog describes possible Actions. It does not prove that an Action is enabled on a particular MCP server. Runtime tool names usually have the `ZohoCRM_` prefix, while the Zoho MCP setup UI uses the Action name without that prefix.

## Safe workflow

1. Confirm the correct Zoho account and organization. Never reuse an endpoint from another customer.
2. Identify the standard module. For customer lookup, use at least two reliable attributes where possible, such as account name, email address, phone number, or address.
3. Resolve module and field API names with `getModules` and `getFields`. Represent an organization-specific field in portable instructions as `<CUSTOM_FIELD_API_NAME>`.
4. Read records before creating or updating them. Mark ambiguous matches and duplicates rather than guessing.
5. Use `searchRecords` for normal criteria and `executeCOQLQuery` for controlled field selection, filtering, ordering, and pagination. COQL does not support `SELECT *` or joins.
6. For writes, send only intended fields and read the affected record back immediately.
7. Do not use delete, workflow, function, layout, field-creation, bulk-job, mass-update, or administrative Actions unless the task explicitly requires them.

## Common calls

Search records with structured JSON:

```bash
cat > /tmp/zoho_search.json <<'JSON'
{
  "path_variables": {"module": "Contacts"},
  "query_params": {"criteria": "(Email:equals:user@example.com)"}
}
JSON
mcporter call "$ZOHO_MCP_URL.ZohoCRM_searchRecords" --args "$(< /tmp/zoho_search.json)"
```

Run COQL:

```bash
cat > /tmp/zoho_coql.json <<'JSON'
{
  "body": {
    "select_query": "SELECT id, Account_Name, Website FROM Accounts WHERE Website != '' ORDER BY Account_Name LIMIT 50"
  }
}
JSON
mcporter call "$ZOHO_MCP_URL.ZohoCRM_executeCOQLQuery" --args "$(< /tmp/zoho_coql.json)"
```

Use the schema shown by the live MCP server when it differs from these examples. For deeply nested arguments, use a temporary JSON file instead of fragile shell quoting.

## Bundled scripts

The scripts require `ZOHO_MCP_URL`, call `mcporter` without shell expansion, paginate results, and normalize common Zoho MCP response envelopes.

```bash
python3 scripts/list_contacts.py --search "Smith" --json --limit 20
python3 scripts/list_accounts.py --search "Acme Corp" --json --limit 20
python3 scripts/search_records.py Contacts --search "Smith" --json --limit 20
python3 scripts/search_records.py Deals \
  --fields id,Deal_Name,Stage,Amount,Closing_Date \
  --coql "Stage = 'Qualification'" --json --limit 20
```

Supported options:

- `list_contacts.py`: `--search`, `--fields`, `--json`, `--full`, `--limit`, `--page-size`, `--timeout`
- `list_accounts.py`: `--search`, `--all`, `--where`, `--fields`, `--json`, `--limit`, `--page-size`, `--timeout`
- `search_records.py`: positional `module`, optional positional search term, `--search`, `--coql`, `--fields`, `--json`, `--limit`, `--page-size`, `--timeout`

Run any helper with `--help` without configuring credentials. Unknown or incomplete options must exit with status 2.

## COQL and field rules

- `executeCOQLQuery` is mandatory in every recommended Action profile.
- Query one base module at a time.
- Use API names, not UI labels.
- Use standard API names such as `Last_Name`, `Email`, `Account_Name`, `Deal_Name`, `Stage`, and `Closing_Date` in portable examples.
- Select only required fields.
- Use single quotes for strings, for example `WHERE Billing_City = 'Berlin'`.
- Use ISO timestamps including timezone offsets.
- Use `LIMIT <offset>, <count>` for offset pagination and do not assume one response contains every record.
- Inspect the live `executeCOQLQuery` schema before the first call.

Inspect field metadata before using a custom field:

```bash
cat > /tmp/zoho_fields.json <<'JSON'
{
  "query_params": {"module": "Contacts"}
}
JSON
mcporter call "$ZOHO_MCP_URL.ZohoCRM_getFields" --args "$(< /tmp/zoho_fields.json)"
```

After confirming an organization-specific API name, substitute it where documentation shows `<CUSTOM_FIELD_API_NAME>`.

## Higher-impact employee Actions

The recommended CRM Employee profile includes `sendMail`, `convertLead`, `changeSingleRecordOwner`, `createEventsRecords`, and `updateEventsRecord` because these are normal CRM operations. Apply these safeguards:

- Enabling `sendMail` gives technical capability, not authorization for a particular email. Follow the active communication approval policy and verify recipient, sender, subject, and content before sending.
- Read a Lead before `convertLead` and verify the resulting Account, Contact, and Deal links afterward.
- Resolve the target user before `changeSingleRecordOwner` and read the record back afterward.
- Check participants, timezone, start time, and end time before creating or updating an Event.

## Attachments

Zoho MCP upload Actions may report success without transferring local binary data. For verified binary uploads, use the separate `zoho-attachment-bridge` skill and read the attachment back after upload.

## References

- [Action profiles](references/ACTION_PROFILES.md): recommended least-privilege selections for new MCP servers
- [Complete CRM Actions catalog](references/ZOHO_CRM_MCP_ACTIONS.md): all known CRM Actions and descriptions
- [Functions API](references/FUNCTIONS_API.md): create, update, and verify Deluge functions through MCP (`createFunctions`, `updateFunction`, naming rules, Button category)

Load the profile reference when configuring a connection. Load the full catalog only when the profile lacks a required Action. Load the Functions API reference before creating or updating CRM functions.

## Troubleshooting and safety

- **`ZOHO_MCP_URL not set`**: set the environment variable in the current session without exposing its value.
- **Module or field error**: use `getModules` or `getFields` to confirm the API name and permissions.
- **OAuth scope error**: reconnect the affected MCP connection with the required scope; never switch to another customer's endpoint.
- Keep all delete Actions disabled by default.
- Keep functions, workflows, blueprints, layouts, fields, modules, users, profiles, roles, sharing, sandboxes, and CRM administration disabled for normal staff.
- Avoid mass and bulk mutations in normal staff profiles.
