# OpenClaw Zoho CRM MCP Skill

Public source repository for the ClawHub skill `@sprintcx/zoho-crm-mcp`.

The skill connects an OpenClaw agent to Zoho CRM through Zoho's MCP endpoint and includes helper scripts for contacts, accounts, generic module searches, and COQL queries through `mcporter`.

## Files

- `SKILL.md`: ClawHub/OpenClaw skill instructions.
- `skill-card.md`: ClawHub release card metadata.
- `scripts/list_contacts.py`: List or search Zoho CRM contacts.
- `scripts/list_accounts.py`: List or search Zoho CRM accounts.
- `scripts/search_records.py`: Generic Zoho CRM module search and COQL helper.

## Requirements

- OpenClaw with `mcporter` available.
- A Zoho CRM MCP endpoint from <https://mcp.zoho.eu>.
- `ZOHO_MCP_URL` set in the environment.

```bash
export ZOHO_MCP_URL="https://your-org-zoho-crm-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message"
```

Treat `ZOHO_MCP_URL` like a password. It contains CRM access credentials.

## Usage

```bash
python3 scripts/list_contacts.py
python3 scripts/list_contacts.py --search "Smith" --json

python3 scripts/list_accounts.py
python3 scripts/list_accounts.py --search "Acme"

python3 scripts/search_records.py Contacts --search "Smith"
python3 scripts/search_records.py Accounts --coql "Website != ''" --json
```

## Security Notes

Earlier ClawHub releases called `mcporter` through `bash -c`, which made the credential-bearing `ZOHO_MCP_URL` unsafe if a malicious value was ever injected into the environment.

The repository version calls `mcporter` directly through `subprocess.run([...])` without shell expansion.

## Publish

Publish under the SprintCX ClawHub organization and attach GitHub source metadata:

```bash
clawhub skill publish . \
  --slug zoho-crm-mcp \
  --owner sprintcx \
  --version 1.3.1 \
  --source-repo sprintberlin/openclaw-zoho-crm-mcp-skill \
  --source-ref main \
  --source-path . \
  --changelog "Move source to GitHub and remove shell-based mcporter calls"
```
