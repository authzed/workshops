# Part 3 — Export, Version, and Save to GitHub

In this section you will learn how to export the current schema to a file and save validation test cases as well as preserve work between server sessions. This is essential because the SpiceDB Dev MCP Server is in-memory only and all data is lost on shutdown 

## 1. Save the Schema

Ask your MCP-enabled assistant:

```
Save my schema to schema.zed
```

The assistant reads from schema://current and writes to the path you specify

This is recommended when you grow more than one schema.
After saving, verify the file exists locally.

## 2. Export Validation Files

Validation files capture expected permissions:

```
- Who can read?
- Who can edit?
- Who can share?
```

This creates test cases.

Ask:

```
Save the validation file to tests/document-permissions.yaml
```

The assistant reads from validation://current and writes to your specified file path
You can build validation checks like:

```
document:readme:
  share:
    allowed:
      - user:alice
    denied:
      - user:bob
      - user:charlie
  edit:
    allowed:
      - user:alice
      - user:bob
    denied:
      - user:charlie
  read:
    allowed:
      - user:alice
      - user:bob
      - user:charlie
```
These serve as golden tests.

## 3. Create Repo Structure

Recommended structure:

```
spicedb-workshop/
├── permissions/
│   └── document-sharing.zed
├── tests/
│   └── document-permissions.yaml
└── README.md
```

## 4. Reload After Restart

Restart your dev server:

```
zed mcp experimental-run
```

Then ask your assistant:

```
Load the schema from permissions/document-sharing.zed and apply it to the dev server.
```

This reads the file and uses `write_schema` to load it into the development instance.
You can repeat with validation files as needed.

## Verify Everything Works

Ask:

```
Show schema://current
```

Then repeat a permission check:

```
Can charlie edit doc:readme?
```

You should get `NO_PERMISSION` as before.

## Completion Milestone: Part 3

You now have:

A schema saved to disk and a validation file with test cases. This means your authorization system is no longer ephemeral.

Let's see how you can take this setup to production using AuthZed Cloud in [Part 4](mcp-assisted-authorization/4-cloud.md).
