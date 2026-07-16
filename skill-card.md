## Description: <br>
Connects an agent to Zoho CRM through MCP so it can search contacts, list accounts, query records with COQL, and use mcporter-based helper scripts for common CRM operations. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[sprintcx](https://clawhub.ai/user/sprintcx) <br>

### License/Terms of Use: <br>
MIT <br>


## Use Case: <br>
Developers and CRM operators use this skill to connect an agent to Zoho CRM via MCP, configure the required MCP endpoint, search CRM modules, list contacts and accounts, and run COQL queries through mcporter. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The ZOHO_MCP_URL endpoint is credential-bearing and could expose CRM access if echoed, logged, or shared. <br>
Mitigation: Treat the MCP URL like a password, avoid printing the full value, and start with read-only Zoho scopes. <br>
Risk: Helper scripts pass the credential-bearing MCP endpoint to mcporter, so local process visibility and logs should be treated carefully. <br>
Mitigation: The scripts call mcporter directly without shell expansion and never print ZOHO_MCP_URL intentionally. Run them only on trusted systems. <br>
Risk: Read-write Zoho CRM actions can create or update business records if enabled on the MCP server. <br>
Mitigation: Enable only the CRM actions needed for the use case and avoid delete actions unless explicitly required. <br>


## Reference(s): <br>
- [Zoho CRM MCP ClawHub page](https://clawhub.ai/sprintcx/skills/zoho-crm-mcp) <br>
- [GitHub source repository](https://github.com/sprintberlin/openclaw-zoho-crm-mcp-skill) <br>
- [Zoho MCP portal](https://mcp.zoho.eu) <br>


## Skill Output: <br>
**Output Type(s):** [guidance, shell commands, configuration, code] <br>
**Output Format:** [Markdown guidance with bash, JSON, SQL, and Python examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a ZOHO_MCP_URL endpoint; bundled helper scripts can print table or JSON output from Zoho CRM MCP calls.] <br>

## Skill Version(s): <br>
1.4.0 <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
