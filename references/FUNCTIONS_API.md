# Zoho CRM Functions API Reference (Deluge & MCP)

This reference documents how to create, inspect, update, and manage Zoho CRM functions via MCP (`mcporter`) and the Zoho CRM v8 Functions REST API.

## Core Operations

Zoho CRM v8 exposes functions via the Developer Tools API. When using the Zoho CRM MCP server, the following actions are available:

- `ZohoCRM_createFunctions`: Create new functions with metadata and optional inline script or ZIP package.
- `ZohoCRM_getFunctions`: List functions with pagination (`per_page`, `page`).
- `ZohoCRM_getFunction`: Retrieve metadata of a single function using path variable `fxIdentifier` (function ID or API name).
- `ZohoCRM_getFunctionCode`: Retrieve source code of a function (`fxIdentifier`).
- `ZohoCRM_updateFunction`: Update metadata or code (`fxIdentifier`).
- `ZohoCRM_publishFunction`: Explicit publish for compiled multi-file runtimes (Java, NodeJS, Python).

> **Note on Deluge Functions:** Deluge functions are automatically published upon creation or update when `_code` is provided. Explicit `publishFunction` calls are only required for non-Deluge runtimes.

---

## Two-Step Deployment Pattern for Deluge

Uploading large or complete Deluge scripts directly in `createFunctions` can lead to `CANNOT_PROCESS` errors due to compilation or validation timeouts. The proven pattern is two-step:

### Step 1: Create Minimal Stub

Create the function with all metadata, empty arguments (if no parameters), and a minimal valid stub returning a placeholder:

```json
{
  "body": {
    "metadata": "{\"functions\": [{\"name\": \"My New Function\", \"api_name\": \"mynewfunction\", \"category\": \"Button\", \"runtime\": \"Deluge 1.0\", \"description\": \"Description here\", \"arguments\": [], \"_code\": \"string button.myNewFunction()\\n{\\nreturn \\\"stub\\\";\\n}\"}]}"
  }
}
```

### Step 2: Update with Full Code

Update the function via `ZohoCRM_updateFunction` using the `metadata` envelope:

```json
{
  "path_variables": {
    "fxIdentifier": "18575000142778039"
  },
  "body": {
    "metadata": "{\"functions\": [{\"_code\": \"<full Deluge code here>\"}]}"
  }
}
```

> **CRITICAL (`metadata` wrapper):** `ZohoCRM_updateFunction` requires the `metadata` key. Calling `{"body": {"functions": [{"_code": "..."}]}}` directly returns `SUCCESS` without actually updating the code in Zoho CRM (false-positive success). Always wrap inside `metadata`.

---

## Naming & Validation Rules

### 1. Function Name (`name`)
- Must match the regex `^[A-Za-z][A-Za-z0-9 _-]*$`.
- Colons (`:`) and other punctuation marks are strictly rejected with `INVALID_DATA`.
- Must be unique across all functions in the CRM organization (`DUPLICATE_DATA` if duplicate).

### 2. API Name (`api_name`)
- Must start with a letter and contain only lowercase letters, digits, and underscores (`^[a-z][a-z0-9_]*$`).
- CamelCase API names (e.g. `myNewFunction`) fail with `CANNOT_PROCESS`.

### 3. Function Declaration in Deluge Code
- The function signature in `_code` must match the category and existing name:
  - **Button:** `string button.<functionName>()`
  - **Standalone:** `string standalone.<functionName>(...)` or `void standalone.<functionName>(...)`
  - **Automation:** `void automation.<functionName>(...)`
- Changing the function name in the declaration line during `updateFunction` triggers a `COMPILATION_ERROR` (`Function with name ... exists`).

---

## Supported Categories

The `category` property determines how and where the function executes in Zoho CRM:

| Category | UI Location | Trigger Mechanism |
| :--- | :--- | :--- |
| `Button` | Module Links & Buttons | List View, Detail View, Utility Menu buttons |
| `Standalone` | Developer Hub / REST API | Can be called by other functions, schedulers, or exposed as ZAPI/REST API |
| `Automation` | Workflow Rules / Blueprints | Triggered on record create, edit, or stage transitions |
| `Schedule` | Schedulers | Periodic cron execution |
| `Related List` | Module Related Lists | Dynamic data rendering in record tabs |
| `Signals` | Signals / Notifications | Incoming external webhooks |
| `Validation Rule` | Layout Rules | Custom client-side validation |

### Creating `Button` Category Functions via API

Creating `category: "Button"` functions via the Functions API is supported.
To avoid `CANNOT_PROCESS` or `INVALID_DATA`:
1. Use an explicit empty array `"arguments": []`.
2. Do not pass parameters (CRM UI buttons do not accept custom arguments).
3. The Deluge declaration must start with `string button.<FunctionName>()`.
4. Ensure `name` and `api_name` follow the validation regexes above.

---

## Verification After Write

Always verify every function creation or update:

1. **Check Code:** Call `ZohoCRM_getFunctionCode` with `{"path_variables": {"fxIdentifier": "<ID>"}}` and compare the returned `data.result` against your local file.
2. **Check Status:** Call `ZohoCRM_getFunction` and verify `state == "active"` and `has_draft == false`.
