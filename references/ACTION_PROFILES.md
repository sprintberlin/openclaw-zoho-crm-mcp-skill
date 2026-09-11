# Recommended Zoho CRM MCP Action Profiles

Zoho CRM exposes roughly 1,300 MCP Actions. Do not enable the entire catalog for a normal agent. Start with the smallest profile that covers the role and add individual Actions only after a real requirement appears.

Names below match the Zoho MCP setup UI and the complete catalog in `ZOHO_CRM_MCP_ACTIONS.md`. Runtime tools usually appear as `ZohoCRM_<Action>`, for example `ZohoCRM_executeCOQLQuery`.

## Profile overview

1. **CRM Analyst, read-only**: searches, reports, metadata, related records and COQL.
2. **CRM Employee, read/write without delete**: recommended normal profile. Reads, creates and updates records, notes and record tags. No delete, automation or administration.
3. **Sales Operator**: CRM Employee plus selected lead conversion, owner and activity Actions.
4. **CRM Developer or Administrator**: no blanket profile. Add workflow, function, layout, field, module and security Actions individually for a defined task.

## CRM Analyst, read-only

```text
getModules
getModuleByApiName
getFields
getFieldsWithID
getPickListValues
getCustomViews
getCustomViewById
getUsers
getOrganization
getRecord
getRecords
getRecordCount
searchRecords
bulkSearchRecords
executeCOQLQuery
getRelatedLists
getRelatedRecord
getRelatedRecords
getRelatedRecordsCount
getNotes
getNotesById
getNoteById
getNotesModule
getTags
getTimelines
```

`executeCOQLQuery` belongs in every useful profile. It gives the agent controlled field selection, filtering and pagination without enabling administration. `bulkSearchRecords` is a POST-based read-only search for criteria too large for a query string.

## CRM Employee, read/write without delete

Start with every Action from **CRM Analyst, read-only**, then add:

```text
createRecords
updateRecord
createNotes
createNotesModule
updateNoteById
updateRelatedNoteById
updateNotesModule
postAddTags
postAddTagsWithId
postRemoveTags
postRemoveTagsWithId
```

This is the recommended default for a normal CRM employee or operational agent. It can find, inspect, create and update business records, but it cannot delete records or change CRM configuration.

Optional when batch editing is a normal part of the role:

```text
updateRecords
```

Do not include `upsertRecords` by default. It is useful for integrations, but a wrong duplicate-check field can create unintended records.

## Sales Operator additions

Enable only when the role actually performs these operations:

```text
convertLead
changeSingleRecordOwner
createEventsRecords
updateEventsRecord
```

`convertLead` creates or links Contacts, Accounts and Deals. `changeSingleRecordOwner` changes responsibility. Both have more business impact than a normal field update.

## Optional read-only communication history

```text
getEmails
getSpecificEmail
getAttachments
getAttachmentById
```

Do not include `sendMail` in a standard profile. Sending email is external communication and needs its own authorization policy.

## Explicitly excluded from normal profiles

- Every `delete*`, `massDelete*`, recycle-bin emptying and permanent-delete Action
- Functions and custom code
- Workflows, connected workflows, cadences, blueprints and assignment rules
- Layout, field, module, picklist-definition, profile, role, user and organization configuration
- Sharing rules, territories, portals, sandboxes, backups and audit exports
- Bulk write/import jobs, mass updates, mass owner changes and mass mail
- Email sending, relay, templates and mailbox configuration
- Record locking and broad administrative changes

## Validation after creating an MCP server

1. Run `mcporter list "$ZOHO_MCP_URL"`.
2. For the employee profile, confirm `executeCOQLQuery`, `searchRecords`, `getRecord`, `createRecords`, and `updateRecord` are present.
3. Search the returned list for `delete`, `workflow`, `function`, `layout`, `field`, `module`, `profile`, `role`, `sandbox`, `mass`, and `bulkWrite`.
4. Remove unintended high-impact Actions in `mcp.zoho.eu` and reconnect if OAuth scopes changed.
5. Test one read first. Test writes only in the intended organization and verify the record afterward.
