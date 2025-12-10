# Part 3 — Export, Version, and Save to GitHub

## Learning Goals

By the end of this part, learners will:

- Export the current schema to a file
- Save validation test cases
- Create a repository structure for versioning
- Preserve work between server sessions
- Commit files to GitHub

This is essential because the SpiceDB Dev MCP Server is in-memory only and all data is lost on shutdown 

## 1. Why Export?

The development server is a rapid iteration tool:

- No persistence
- Everything lives in memory
- Shutting down loses all changes
- Therefore, the correct workflow is:

```
Build schema
Test behavior
Export to files
Commit to GitHub
```

Documentation guidance:

- “Track schemas in version control” 

- “Use validation files to capture test cases” 

## 2. Save the Schema

Ask your MCP-enabled assistant:

```
Save my schema to schema.zed
```

The assistant reads from schema://current and writes to the path you specify

You can also use subfolders:
```
Write the current schema to permissions/document-sharing.zed
```

This is recommended when you grow more than one schema.
After saving, verify the file exists locally.

## 3. Export Validation Files

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

## 4. Create Repo Structure

Recommended structure:

```
spicedb-workshop/
├── permissions/
│   └── document-sharing.zed
├── tests/
│   └── document-permissions.yaml
└── README.md
```
README.md describes:

- How to run the dev server
- How to modify schemas
- How to run validation

## 5. Commit and Push

Run the standard git commands:

```
git init
git add .
git commit -m "Initial schema and validation"
git branch -M main
git remote add origin https://github.com/<user>/spicedb-workshop.git
git push -u origin main
```
Now your work is backed up.

This follows best practices from the documentation:

- “Track schemas in version control” 
- “Use validation files to capture test cases”

## 6. Reload After Restart

Restart your dev server:

```
zed mcp experimental-run
```

Then ask your assistant:

```
Load the schema from permissions/document-sharing.zed and apply it to the dev server.
```
This reads the file and uses write_schema to load it into the development instance.
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

You should get NO_PERMISSION as before.

## Completion Milestone: Part 3

You now have:

A schema saved to disk and a validation file with test cases. This means your authorization system is no longer ephemeral.

Next, we will use this foundation to learn how to:

- Debug permissions
- Explore the authorization graph
- Test edge cases
