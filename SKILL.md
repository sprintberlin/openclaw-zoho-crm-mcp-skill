---
name: "zoho-crm-mcp"
description: "Use Zoho CRM via MCP; run safe record workflows, COQL, select Actions, and report reproducible skill defects to GitHub."
---

# Zoho CRM MCP

Use Zoho CRM through an MCP endpoint from `mcp.zoho.eu`. This skill is the canonical home for CRM-specific MCP action documentation and least-privilege action profiles.

Source: [sprintberlin/openclaw-zoho-crm-mcp-skill](https://github.com/sprintberlin/openclaw-zoho-crm-mcp-skill)

## Requirements

- A Zoho CRM MCP endpoint from `mcp.zoho.eu`
- `mcporter`
- Endpoint configuration via `ZOHO_CRM_MCP_URL` / `ZOHO_MCP_URL`, `--profile`, or `--mcp-url`

Treat the endpoint as a credential. Never print it, commit it, or copy it into tickets, prompts, or chats.

## First setup

1. Create or open a Zoho CRM connection at `mcp.zoho.eu`.
2. Select only the required Actions. Start with [references/ACTION_PROFILES.md](references/ACTION_PROFILES.md).
3. Use [references/ZOHO_CRM_MCP_ACTIONS.md](references/ZOHO_CRM_MCP_ACTIONS.md) only when a profile lacks a required Action.
4. Configure one default endpoint with `ZOHO_CRM_MCP_URL` (legacy `ZOHO_MCP_URL` also works), or create named profiles using [references/MULTI_ACCOUNT.md](references/MULTI_ACCOUNT.md).
5. Inspect the selected live server before relying on an Action:

```bash
mcporter list "$ZOHO_CRM_MCP_URL"
```

The catalog describes possible Actions. It does not prove that an Action is enabled on a particular MCP server. Runtime tool names usually have the `ZohoCRM_` prefix, while the Zoho MCP setup UI uses the Action name without that prefix.

## Endpoint selection

For one account, set `ZOHO_CRM_MCP_URL`; legacy `ZOHO_MCP_URL` remains supported. For multiple accounts, pass `--profile NAME` to a bundled helper. Profiles live in `~/.config/zoho-mcp/profiles.json` by default and can resolve endpoints through an environment variable, a local URL file, or a direct URL. One-off `--mcp-url URL` overrides everything, but may expose the credential in shell history or process listings.

Resolution order is `--mcp-url`, selected profile, then the environment fallback. Profile selection is `--profile`, `ZOHO_CRM_MCP_PROFILE`, then `ZOHO_MCP_PROFILE`. See [references/MULTI_ACCOUNT.md](references/MULTI_ACCOUNT.md) for the shared CRM, People, and Books format.

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
mcporter call "$ZOHO_CRM_MCP_URL.ZohoCRM_searchRecords" --args "$(< /tmp/zoho_search.json)"
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
mcporter call "$ZOHO_CRM_MCP_URL.ZohoCRM_executeCOQLQuery" --args "$(< /tmp/zoho_coql.json)"
```

Use the schema shown by the live MCP server when it differs from these examples. For deeply nested arguments, use a temporary JSON file instead of fragile shell quoting.

## Bundled scripts

The scripts resolve the endpoint via `--mcp-url`, `--profile` (`~/.config/zoho-mcp/profiles.json`), or environment variables (`ZOHO_CRM_MCP_URL`, `ZOHO_MCP_URL`), call `mcporter` without shell expansion, paginate results, and normalize common Zoho MCP response envelopes.

```bash
python3 scripts/list_contacts.py --search "Smith" --json --limit 20
python3 scripts/list_accounts.py --search "Acme Corp" --json --limit 20
python3 scripts/search_records.py Contacts --search "Smith" --json --limit 20
python3 scripts/search_records.py Deals \
  --fields id,Deal_Name,Stage,Amount,Closing_Date \
  --coql "Stage = 'Qualification'" --json --limit 20
python3 scripts/record_url.py Leads 407625000068467001
```

Never hand-assemble CRM record links; generate them with `record_url.py`, which resolves the org `zgid`, the module tab name, and the data center itself.

Supported options:

- `list_contacts.py`: `--search`, `--fields`, `--json`, `--full`, `--limit`, `--page-size`, `--timeout`
- `list_accounts.py`: `--search`, `--all`, `--where`, `--fields`, `--json`, `--limit`, `--page-size`, `--timeout`
- `search_records.py`: positional `module`, optional positional search term, `--search`, `--coql`, `--fields`, `--json`, `--limit`, `--page-size`, `--timeout`
- `record_url.py`: positional `module` and numeric `record id`, `--dc`, `--json`, `--timeout`
- All helpers: `--mcp-url`, `--profile`, `--profiles-file`

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
mcporter call "$ZOHO_CRM_MCP_URL.ZohoCRM_getFields" --args "$(< /tmp/zoho_fields.json)"
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

## Report skill defects and contribute

Contributions are explicitly welcome from humans and agents. A CRM task is complete only after serving the user and filing or linking every reproducible skill defect found.

- **Issue**: For schema mismatches, broken helpers or workflows, wrong COQL or field guidance, or missing profile Actions. File via GitHub CLI: `gh issue create --repo sprintberlin/openclaw-zoho-crm-mcp-skill --title "bug: ..." --body "..."`.
- **Pull request**: Preferred when you can fix and verify the defect. Follow the standard branch, test, and PR workflow.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules and `gh` workflows.

Do not file skill issues for endpoint/auth/profile setup, rate limits, transient service failures, timeouts, organization-specific fields, or unsupported CRM operations. Never include MCP URLs, record content, contacts, or customer data.

## References

- [Action profiles](references/ACTION_PROFILES.md): recommended least-privilege selections for new MCP servers
- [Complete CRM Actions catalog](references/ZOHO_CRM_MCP_ACTIONS.md): all known CRM Actions and descriptions
- [Functions API](references/FUNCTIONS_API.md): create, update, and verify Deluge functions through MCP (`createFunctions`, `updateFunction`, naming rules, Button category)
- [Multi-account profiles](references/MULTI_ACCOUNT.md): portable endpoint selection for one or many Zoho accounts
- [Contributing guide](CONTRIBUTING.md): issue and pull request workflows for humans and agents

Load the profile reference when configuring a connection. Load the full catalog only when the profile lacks a required Action. Load the Functions API reference before creating or updating CRM functions.

## Troubleshooting and safety

- **No endpoint configured**: set `ZOHO_CRM_MCP_URL` / `ZOHO_MCP_URL`, use `--profile`, or pass `--mcp-url`; never print the value.
- **Profile not found or wrong app**: verify `--profiles-file`, the profile name, and its `services.crm` entry.
- **Module or field error**: use `getModules` or `getFields` to confirm the API name and permissions.
- **OAuth scope error**: reconnect the affected MCP connection with the required scope; never switch to another customer's endpoint.
- Keep all delete Actions disabled by default.
- Keep functions, workflows, blueprints, layouts, fields, modules, users, profiles, roles, sharing, sandboxes, and CRM administration disabled for normal staff.
- Avoid mass and bulk mutations in normal staff profiles.
