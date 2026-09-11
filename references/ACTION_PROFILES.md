# Recommended Zoho CRM MCP Action Profiles

Zoho CRM exposes roughly 1,300 MCP Actions. Do not enable the entire catalog for a normal agent. Start with the smallest profile that covers the role and add individual Actions only after a real requirement appears.

Names below match the Zoho MCP setup UI and the complete catalog in `ZOHO_CRM_MCP_ACTIONS.md`. Runtime tools usually appear as `ZohoCRM_<Action>`, for example `ZohoCRM_executeCOQLQuery`.

## Profile overview

1. **CRM Analyst, read-only**: searches, reports, metadata, related records and COQL.
2. **CRM Employee, read/write without delete**: recommended operational profile. Includes COQL, record creation and updates, notes, tags, CRM email, lead conversion, owner changes and Events. No delete, functions, workflows or CRM administration.
3. **CRM Developer or Administrator**: no blanket profile. Add workflow, function, layout, field, module and security Actions individually for a defined task.

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

`executeCOQLQuery` is mandatory in every recommended profile. It gives the agent controlled field selection, filtering and pagination without enabling administration. `bulkSearchRecords` is a POST-based read-only search for criteria too large for a query string.

## CRM Employee, read/write without delete

This is the recommended default for a normal CRM employee or operational agent. It can search, inspect, create and update business records, work with notes and tags, inspect and send CRM email, convert Leads, change a record owner, and manage Events. It cannot delete records or change CRM configuration.

Select every Action from **CRM Analyst, read-only**, then add:

### Email and attachment history

```text
getEmails
getSpecificEmail
getAttachments
getAttachmentById
getEmailTemplates
getEmailTemplateById
listOrgEmails
getOrgEmailDetailsbyId
```

These are reads. `getAttachments` and `getAttachmentById` inspect attachment metadata. For verified local binary uploads use the separate `zoho-attachment-bridge` skill.

### Record, note and tag writes

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

Optional when batch editing is a normal part of the role:

```text
updateRecords
```

Do not include `upsertRecords` by default. It is useful for integrations, but a wrong duplicate-check field can create unintended records.

### Normal CRM operations

```text
sendMail
convertLead
changeSingleRecordOwner
createEventsRecords
updateEventsRecord
```

Safeguards:

- `sendMail`: enabling the Action gives technical capability but does not authorize a particular outbound email. Follow the active approval policy and verify recipient, sender, subject, template or body, and attachments before sending.
- `convertLead`: read the Lead first and verify the resulting Contact, Account and Deal links afterward.
- `changeSingleRecordOwner`: resolve the destination user ID first and read the record back afterward.
- Events: verify participants, timezone, start and end time before create or update.

### Complete CRM Employee copy list

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
getEmails
getSpecificEmail
getAttachments
getAttachmentById
getEmailTemplates
getEmailTemplateById
listOrgEmails
getOrgEmailDetailsbyId
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
sendMail
convertLead
changeSingleRecordOwner
createEventsRecords
updateEventsRecord
```

## CRM Developer or Administrator

Do not create a reusable blanket profile. Add high-impact Actions individually for the current task and remove them again when the task is complete. This includes functions, workflows, blueprints, layouts, fields, modules, picklist definitions, profiles, roles, users, sharing, territories, portals, sandboxes, backups and other CRM configuration.

## Explicitly excluded from normal profiles

- Every `delete*`, `massDelete*`, recycle-bin emptying and permanent-delete Action
- Functions and custom code
- Workflows, connected workflows, cadences, blueprints and assignment rules
- Layout, field, module, picklist-definition, profile, role, user and organization configuration
- Sharing rules, territories, portals, sandboxes, backups and audit exports
- Bulk write/import jobs, mass updates, mass owner changes and mass mail
- Email relay, email-template modification and mailbox configuration
- Record locking and broad administrative changes

## Validation after creating an MCP server

1. Run `mcporter list "$ZOHO_MCP_URL"`.
2. For CRM Employee, confirm at least `executeCOQLQuery`, `searchRecords`, `getRecord`, `createRecords`, `updateRecord`, `sendMail`, `convertLead`, `changeSingleRecordOwner`, `createEventsRecords`, and `updateEventsRecord` are present.
3. Search the returned list for unintended `delete`, `workflow`, `function`, `layout`, `field`, `module`, `profile`, `role`, `sandbox`, `mass`, and `bulkWrite` Actions.
4. Remove unintended high-impact Actions in `mcp.zoho.eu` and reconnect if OAuth scopes changed.
5. Test one read first. Test writes only in the intended organization and verify the result afterward.
