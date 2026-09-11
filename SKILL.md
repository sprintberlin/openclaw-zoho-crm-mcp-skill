---
name: "zoho-crm-mcp"
description: "Zoho CRM via MCP with action catalog, least-privilege profiles, COQL, and record workflows."
---

# Zoho CRM MCP

Use Zoho CRM through an MCP endpoint from `mcp.zoho.eu`. This skill is the canonical home for CRM-specific MCP action documentation and least-privilege action profiles.

Source: [sprintberlin/openclaw-zoho-crm-mcp-skill](https://github.com/sprintberlin/openclaw-zoho-crm-mcp-skill)

## Requirements

- A Zoho CRM MCP endpoint from `mcp.zoho.eu`
- `mcporter`
- `ZOHO_MCP_URL` for the bundled scripts

Treat the endpoint as a credential. Never print it, commit it, or copy it into tickets and chats.

## First setup

1. Create or open a Zoho CRM connection at `mcp.zoho.eu`.
2. Select only the required Actions. Start with [references/ACTION_PROFILES.md](references/ACTION_PROFILES.md).
3. Use [references/ZOHO_CRM_MCP_ACTIONS.md](references/ZOHO_CRM_MCP_ACTIONS.md) only when a profile lacks a required Action.
4. Store the endpoint securely and expose it to the local process as `ZOHO_MCP_URL`.
5. Check the actual server:

```bash
mcporter list "$ZOHO_MCP_URL"
```

The catalog describes possible Actions. It does not prove that an Action is enabled on a particular MCP server. Runtime tool names usually have the `ZohoCRM_` prefix, while the Zoho MCP setup UI uses the Action name without that prefix.

## Safe workflow

1. Confirm the correct Zoho account and organization. Never reuse an endpoint from another customer.
2. Run `mcporter list "$ZOHO_MCP_URL"` and verify the required Action exists.
3. Resolve module and field API names with `getModules` and `getFields` before querying or writing custom fields.
4. Read the exact record before changing it.
5. Use `searchRecords` for normal criteria and `executeCOQLQuery` for controlled field selection, filtering and pagination.
6. For writes, send only intended fields and read the record back.
7. Do not use delete, workflow, function, layout, field-creation, bulk-job, mass-update, or administrative Actions unless the task explicitly requires them.

## Common calls

List tools:

```bash
mcporter list "$ZOHO_MCP_URL"
```

Search records:

```bash
cat > /tmp/zoho_search.json <<'JSON'
{
  "query_params": {
    "module": "Contacts",
    "criteria": "(Email:equals:user@example.com)"
  }
}
JSON
mcporter call "$ZOHO_MCP_URL.ZohoCRM_searchRecords" --args "$(< /tmp/zoho_search.json)"
```

Run COQL:

```bash
cat > /tmp/zoho_coql.json <<'JSON'
{
  "body": {
    "select_query": "SELECT id, Full_Name, Email FROM Contacts WHERE Email is not null LIMIT 100"
  }
}
JSON
mcporter call "$ZOHO_MCP_URL.ZohoCRM_executeCOQLQuery" --args "$(< /tmp/zoho_coql.json)"
```

Use the schema shown by the live MCP server when it differs from these examples. Zoho occasionally changes wrapper argument shapes. For deeply nested arguments, use a temporary JSON file instead of fragile shell quoting.

## Bundled scripts

The scripts call `mcporter` without shell expansion and require `ZOHO_MCP_URL`:

```bash
python3 scripts/list_contacts.py --search "Mustermann" --json
python3 scripts/list_accounts.py --search "Beispiel GmbH" --json
python3 scripts/search_records.py --module Deals --word "Renewal"
```

The list helpers paginate and normalize common Zoho MCP response envelopes.

## COQL rules

- Query one base module at a time.
- Use API names, not UI labels.
- Select only required fields.
- Use single quotes for strings.
- Use ISO timestamps including timezone offsets.
- Paginate explicitly and do not assume one page is complete.
- Inspect the live `executeCOQLQuery` schema before the first call.

## Attachments

Zoho MCP upload Actions may report success without transferring local binary data. For verified binary uploads use the separate `zoho-attachment-bridge` skill and read the attachment back after upload.

## References

- [Action profiles](references/ACTION_PROFILES.md): recommended least-privilege selections for new MCP servers
- [Complete CRM Actions catalog](references/ZOHO_CRM_MCP_ACTIONS.md): all known CRM Actions and descriptions

Load the profile reference when configuring a connection. Load the full catalog only when the profile lacks a required Action.

## Safety

- Start with the smallest profile that satisfies the task.
- Keep all delete Actions disabled by default.
- Keep functions, workflows, blueprints, layouts, fields, modules, users, profiles, roles, sharing, sandboxes and CRM administration disabled for normal staff.
- Avoid mass and bulk mutations in normal staff profiles.
- `sendMail` and other outbound communication Actions require separate authorization and are not part of a default profile.
- Revoke and reconnect the affected MCP connection after an OAuth scope mismatch. Never switch to another customer's endpoint.
