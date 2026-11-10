# Zoho CRM Blueprints via MCP

Use this reference to inspect, create, migrate, and verify Blueprint configurations. A Blueprint defines a state machine and its visual editor layout. Configuring that state machine is different from executing a transition on an individual record.

This guidance combines Zoho's API documentation with observed MCP and editor behavior. Where a behavior has not been verified end to end, it is identified as such. Do not paste customer names, organization IDs, record details, MCP URLs, or credentials into a public repository or issue.

## Actions and first checks

Enable only the actions needed for the job. Runtime names normally have the `ZohoCRM_` prefix.

| Task | MCP actions |
| --- | --- |
| Discover configuration | `getBlueprint`, `getBlueprintId`, `getBlueprintUsageConfigurations`, `getBlueprintProcessConfigurationMeta` |
| Inspect the process | `getBlueprintStates`, `getBlueprintStateById`, `getBlueprintTransitions`, `getBlueprintTransitionById`, `getBlueprintRecordsCount` |
| Create or change a draft | `postBlueprint`, `putBlueprint`, `putBlueprintId`, `cloneBlueprint`, `createBlueprintStates`, `updateBlueprintStateById`, `createBlueprintTransitions`, `updateBlueprintTransitionById` |
| Publish | `activateBlueprint`; `deactivateBlueprint` only if required |
| Inspect or execute a record's next step | `getRecordBlueprintTransition`, `putRecordBlueprintTransition` |

Confirm the organization, module, and MCP server before a call. The [CRM Developer action profile](ACTION_PROFILES.md#crm-developer) lists the available configuration actions. A catalog entry does not prove that an action is enabled on the selected server. Inspect the live action schema:

```bash
mcporter list "$ZOHO_CRM_MCP_URL"
```

Treat the endpoint as a credential. Use the live schema for the exact tool arguments and HTTP details. The examples below show observed argument shapes, with placeholders, and must be adapted to the server version.

## Read and compare a Blueprint

1. List Blueprints with `getBlueprint`, identify the correct one, and read it with `getBlueprintId`. Request `include=state,transition`; without it, the response may omit the state and transition lists even when they exist.
2. Obtain the Blueprint's current active-record count with `getBlueprintRecordsCount`. Count again before any replacement or activation, because it can change.
3. Fetch individual state and transition details. The bulk state and transition APIs require a comma-separated `ids` query parameter, not just a Blueprint ID. Get the IDs from the expanded Blueprint response. State details include `pick_list_value` and escalation data; transition details include trigger type, owners, criteria, during-inputs, and actions.
4. Resolve target module, layout, process field, picklist values, users, roles, and related automation actions from the target organization. IDs are organization-specific. Map actual values and API names deliberately; a translated display name alone is not proof of the correct value.
5. Compare entry `criteria`; states and escalation triggers; per-transition `criteria`, `trigger_type`, `trigger_details`, timing, owners, inputs, and after-actions; common-transition `global` / `include_states` and source states; logical connections and `chart_data`. Check notification recipients, units, and duration as well as action IDs.

Example read-only MCP arguments for the expanded Blueprint:

```json
{
  "path_variables": {"blueprintId": "<BLUEPRINT_ID>"},
  "query_params": {"include": "state,transition"}
}
```

For `getBlueprintRecordsCount`, the observed arguments are `{"path_variables":{"blueprintId":"<BLUEPRINT_ID>"}}`. The state list uses the Blueprint ID plus `query_params.ids`; the transition list uses `query_params.ids`. If the schema differs, follow the selected server instead of guessing parameter names. A partial response is not evidence that omitted criteria, states, or transitions are absent.

Store any full configuration snapshots only in an appropriately protected private location. Record a sanitized comparison, not production record data, in the public skill.

## Logical graph versus visual chart

The Blueprint contains distinct data:

- `states`: process states with their own Blueprint state IDs and an associated `pick_list_value`.
- `transitions`: manual or automatic steps, potentially common to several source states.
- top-level `connections`: the logical source-state, transition, and target-state associations.
- `chart_data`: canvas dimensions, positioned nodes, visual connection endpoints, and transition references.

Do not expect the number of logical connections, visual lines, and transition definitions to be identical. A common transition can apply to multiple source states while appearing as one transition definition or one representative line in the editor. Compare actual source/target/transition semantics and `common` / `include_states`, rather than counts alone. Unexpected duplicate logical tuples deserve investigation; do not remove them blindly.

### IDs are representation-specific

Blueprint state IDs, picklist-value IDs, transition IDs, and logical-connection IDs are different identifiers. Match each field to its documented representation and map it through the corresponding state metadata. A source CRM's IDs cannot be reused in a target CRM.

Important observed behavior: in a functioning Blueprint, the public API returned `chart_data.nodes[*].state.id` as Blueprint **state IDs**, while the `from.state.id` and `to.state.id` values inside `chart_data.connections` were **picklist-value IDs**. The editor's internal `ChartData` used picklist IDs for its `nodeId` and `state_<id>_<anchor>` references. A broken Blueprint showed the same API ID pattern. Therefore, different node and edge ID values in the public response do **not** by themselves diagnose a broken chart. An earlier assumption that all those IDs had to be equal was wrong.

Do not overwrite API state IDs with picklist IDs merely to make the JSON look uniform, or copy the editor's private JSON straight into an API request. Use Zoho's documented create/update schema and state `api_name` references, then inspect the API read-back and the editor. Source and target can also normalize response fields differently from input fields.

### Canvas data and anchors

Zoho describes `chart_data` as optional in the schema but practically necessary for a useful editor diagram. Keep its nodes, visual connections, endpoint positions/directions, and `canvas_size` consistent with the intended graph. The create/update documentation uses state and transition API-name references for chart nodes and edges; inspect the current schema and adapt to the live endpoint.

A server response containing the expected node and edge counts is not proof that the diagram renders. In one investigation, stored chart data contained nodes and many connections, but a freshly opened editor showed the nodes and only one rendered connection; a later tab remained on the loading screen. Another attempt created nodes and lines directly in a browser's in-memory canvas but did not establish persistence. The root cause was not proven. Do not infer a particular ID mismatch or browser problem without reproducing it.

Check a known-good diagram and the target side by side, including endpoint anchors and connection/transition associations. Do not bypass the editor's validation or issue undocumented internal save requests on a production process to force a visual result.

## Create or change a draft

Zoho's [create API](https://www.zoho.com/crm/developer/docs/api/v8/create-blueprint.html) creates a Blueprint in Draft status. A creation request can contain the Blueprint, states, transitions, logical connections, entry criteria, and `chart_data` in the `blueprints` array. Only one Blueprint object is accepted per request, for both create and top-level Blueprint update. Resolve module, layout, field, and picklist metadata in the target organization first. Zoho documents a `module` object for each supplied state and a `layout` object for each supplied transition. Keep `api_name` references consistent across states, transitions, logical connections, and visual connections.

For a Blueprint that has ever been activated, Zoho documents that the top-level Blueprint update endpoints do not accept a direct update even after deactivation. Its documented approach is to keep the source active with `chart_data`, clone it as a dependent draft, update the draft, and activate the new version. This restriction concerns the top-level Blueprint update API; it is not proof that every individual state or transition endpoint or every editor operation is blocked.

### Dependent clone

The [clone API](https://www.zoho.com/crm/developer/docs/api/v8/clone-blueprint.html) lists `name`, `type`, `layout`, `field`, and `module` as required; `module` is a string API name, not a module object. The intended dependent-clone request uses the same source module, layout, field, and pipeline, and omits `map_states` at clone time. The documentation's error text calls this mode `draft` while its type description calls it `dependent`; inspect the live schema and test the exact supported value in a non-production environment. Earlier attempts that omitted layout or used a module object failed; a successful dependent-clone payload has not yet been verified in this investigation.

The following is a documented-shape **template**, not a verified successful request:

```json
{
  "path_variables": {"blueprintId": "<SOURCE_BLUEPRINT_ID>"},
  "body": {
    "blueprints": [{
      "name": "<UNIQUE_DRAFT_NAME>",
      "type": "dependent",
      "module": "Leads",
      "layout": {"id": "<SOURCE_LAYOUT_ID>", "name": "<SOURCE_LAYOUT_NAME>"},
      "field": {"id": "<SOURCE_FIELD_ID>", "api_name": "Lead_Status"}
    }]
  }
}
```

Include the existing pipeline when applicable and required by the live schema. `standalone` is a distinct clone operation: Zoho's sample maps `existing_state.actual_value` to `clone_state.actual_value` at clone time. Do not confuse that with activation's `existing_state.id` to `replacing_state.id` picklist mapping. Read the clone response for `uncopied_*` warnings, then rediscover the new draft's IDs and configuration. After a timeout or ambiguous result, list/read first: do not repeat a create or clone blindly.

Zoho's [state creation API](https://www.zoho.com/crm/developer/docs/api/v8/create-blueprint-states.html) marks `process_id` and `state_escalation` as optional; only `module` and `pick_list_value` are documented as mandatory per state. An old MCP action description says every transition must be updated after creation to set `modified_time`; this is not established as a universal requirement by Zoho's transition documentation. Treat it as a diagnostic lead only, not an instruction to rewrite all transitions. The catalog also reports that some transition updates with `during_inputs` need a layout and may append inputs instead of replacing them. Check the live schema and existing transition before writing; read back for duplicates afterward. Zoho's create documentation describes `optional` as a Boolean; its update page says string but gives a Boolean example. Prefer the actual validated schema and test in a draft.

## Activate and protect records

Before activation, independently verify draft entry criteria, individual transition `trigger_details` and `global` / `include_states`, the logical graph, owners, actions, trigger durations, and the visual chart after a fresh reload. Verify semantic parity rather than relying on visual counts. Check the current record count and understand the effect on records and side effects. Do not deactivate or delete a live Blueprint just to make an API update work.

Zoho's [activation API](https://www.zoho.com/crm/developer/docs/api/v8/activate-blueprint.html) requires `move_records`. When republishing a draft:

- `move_records: true` moves active records to the new version and requires `map_states`.
- `move_records: false` exits active records from the current process at their last known state; it is not a harmless default.
- Each `map_states` item maps `existing_state.id` to `replacing_state.id` using the respective **picklist IDs**, not Blueprint state IDs. Identity mappings may be appropriate only after confirming both sides use the same picklist values.

```json
{
  "path_variables": {"blueprintId": "<DRAFT_BLUEPRINT_ID>"},
  "body": {
    "blueprints": [{
      "move_records": true,
      "map_states": [{
        "existing_state": {"id": "<OLD_PICKLIST_VALUE_ID>"},
        "replacing_state": {"id": "<NEW_PICKLIST_VALUE_ID>"}
      }]
    }]
  }
}
```

This is a shape example, not a complete mapping. Construct and validate every required mapping from current metadata. Do not assume a standalone newly created Blueprint will replace an existing Blueprint or migrate records. After activation, re-read the active Blueprint, IDs, record count, and affected transition configuration; IDs may change when a draft replaces a version.

## Verify the result

1. Read the saved configuration back from the server, including criteria, state/transition details, logical connections, `chart_data`, timing and actions. Check that success is reported for each item; an HTTP success alone is insufficient.
2. Open the correct Blueprint in the CRM editor, wait for loading to finish, and visually inspect it. Reload or open a fresh agent-owned tab and inspect the persisted diagram again. Check the actual rendered connections and labels, not just DOM node counts, saved counts, JavaScript object contents, or a screenshot of a locally injected diagram. A loading screen is not a passed visual test.
3. With authorized, isolated test data and controlled recipients, check entry criteria, transition availability and validation, required actions, and an appropriate automatic-transition timing test. `getRecordBlueprintTransition` is a record-level read; `putRecordBlueprintTransition` executes a transition and can trigger actions or notifications. Never test by touching unrelated customer records or sending real mail without authorization.
4. Report separately what is visually verified, what is functionally tested, what is only read back, and what remains unverified. Do not mark a migration complete until all required checks pass.

## Zoho documentation

- [Get a specific Blueprint](https://www.zoho.com/crm/developer/docs/api/v8/get-a-blueprint.html)
- [Create a Blueprint](https://www.zoho.com/crm/developer/docs/api/v8/create-blueprint.html)
- [Update Blueprints](https://www.zoho.com/crm/developer/docs/api/v8/update-blueprints.html)
- [Clone a Blueprint](https://www.zoho.com/crm/developer/docs/api/v8/clone-blueprint.html)
- [Activate a Blueprint](https://www.zoho.com/crm/developer/docs/api/v8/activate-blueprint.html)
- [Get states](https://www.zoho.com/crm/developer/docs/api/v8/blueprint-states.html) and [transitions](https://www.zoho.com/crm/developer/docs/api/v8/blueprint-transitions.html)
- [Get a record's available transitions](https://www.zoho.com/crm/developer/docs/api/v8/blueprint-details.html) and [execute a record transition](https://www.zoho.com/crm/developer/docs/api/v8/update-blueprint.html)

### Duplicate canvas nodes and published Blueprints

- In one case, the server returned 42 chart nodes for 14 distinct states after repeated in-memory canvas reloads and a save; every state had three entries, and the editor showed stacked boxes. The exact server-side cause and a safe deduplication procedure were not established. Check saved node identity, positions and the freshly loaded editor; do not inject a reconstructed chart or call private save functions to force a fix.
- A Blueprint that has been published was rejected by `putBlueprintId` with `NOT_ALLOWED: Published blueprint cannot be updated`, both while active and after deactivation. Deactivating it is not a workaround, and may affect records; check the record count and activation semantics first.
- One dependent-clone request returned `INTERNAL_ERROR`; its cause is unknown. Re-list Blueprints after an ambiguous clone response before retrying. Use documented draft/clone operations, and verify all settings and the editor before any activation or record migration.

### Clone counts and activation observations

- In one observed instance, an active clone had 14 chart nodes versus 42 in its source, but live read-back showed missing entry criteria, empty automatic-transition `trigger_details` (`{}`), 15 logical connections versus 35 in the source, common transitions that lost source states, and differing owner mapping. The visual cleanup did not establish functional equivalence.
- Treat visual node and connection counts as a starting hint only. Before any activation, verify from live read-back: entry `criteria`; individual transition details including `trigger_details` and `global` / `include_states`; the full logical graph (source-state, transition, and target-state semantics); and owners. Do not activate on the basis of visual counts alone.
- In that instance, an activation attempt returned `INVALID_DATA` for a duplicate Blueprint name; the draft was successfully renamed via `putBlueprintId` and the clone was later activated. Neither the conflict nor the rename establishes a universal requirement or semantic equivalence.
- The MCP transition-update schema may not expose `trigger_details`; inspect the live schema. Never infer a successful fix from in-memory assignments alone; verify persisted values by server read-back.
