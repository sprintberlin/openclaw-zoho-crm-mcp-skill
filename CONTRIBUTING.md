# Contributing

Contributions from humans and agents are explicitly welcome. Issues and pull requests are both wanted. Prefer a pull request when you can implement and verify the fix.

## Issue

Use an issue for a reproducible defect, incomplete documentation, a live-schema mismatch, a broken helper or workflow, incorrect COQL or field guidance, or a missing profile Action.

1. Search open issues with GitHub CLI and link an existing match:
   ```bash
   gh issue list --repo sprintberlin/openclaw-zoho-crm-mcp-skill --state open
   ```
2. If none exists, write a sanitized body file and create the issue with `gh`:
   ```bash
   cat > /tmp/zoho-crm-issue.md <<'EOF'
   ### What happened
   ...

   ### Expected behavior
   ...

   ### Reproduction / Environment
   ...
   EOF
   gh issue create \
     --repo sprintberlin/openclaw-zoho-crm-mcp-skill \
     --title "bug(schema): <short description>" \
     --body-file /tmp/zoho-crm-issue.md
   ```
3. State expected and actual behavior plus minimal reproduction details.
4. Return the issue URL.

Do not file skill issues for endpoint, authentication or profile setup, rate limits, transient service failures, timeouts, organization-specific fields, or unsupported Zoho CRM operations.

## Pull request

Use a pull request for a verified improvement or fix.

1. Branch from `main` and keep the change focused.
2. Add or update tests for behavior changes.
3. Run `python3 -m unittest discover -s tests`.
4. Run the skill validator.
5. Write a sanitized PR body file, then open the pull request with `gh pr create` and link its issue when present:
   ```bash
   cat > /tmp/zoho-crm-pr.md <<'EOF'
   Resolves #<issue-number>

   ### Summary
   ...
   EOF
   gh pr create \
     --repo sprintberlin/openclaw-zoho-crm-mcp-skill \
     --title "feat(profiles): <short description>" \
     --body-file /tmp/zoho-crm-pr.md
   ```

## Requirements

- Use an authenticated GitHub CLI (`gh`) with the required repository access.
- Never submit MCP URLs, tokens, record content, contacts, or customer data.
- Keep `SKILL.md` short and imperative. Put reference material in `references/` and deterministic logic in `scripts/`.
- Preserve compatibility with `mcporter` and existing helper interfaces.
