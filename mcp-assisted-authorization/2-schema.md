# Part 2 — Build Your First Permissions Schema

## Learning Goals

You will learn to:

- Write and inspect a SpiceDB schema
- Add relationships
- Validate with permission checks
- Explore results

We will model document sharing:

- Owners can share, edit, view
- Editors can edit, view
- Viewers can only view

## 1. Write the Schema

Ask your assistant:

```
Create a schema for a document sharing system. Documents have owners, editors, and viewers. Owners can share, editors can edit, and viewers can only read.
```

A typical result:

```
definition user {}

definition document {
  relation owner: user
  relation editor: user
  relation viewer: user

  permission read = owner + editor + viewer
  permission edit = owner + editor
  permission share = owner
}
```

## 2. Inspect the Schema

Run:

```
Show schema://current
```

The assistant should display the currently loaded schema.

This is how you verify correctness and discover errors like:

undefined types

syntax problems

The documentation indicates that schema errors can be debugged by reviewing the source and validation resources

## 3. Add Test Data

Now let’s populate the system.

Use natural language:

```
Create test data where alice owns doc:readme, bob is an editor, and charlie is a viewer.
```
Your assistant should call update_relationships to apply these relationships in memory.
That should result in something equivalent to:

```
relationship document:readme owner user:alice
relationship document:readme editor user:bob
relationship document:readme viewer user:charlie
```

You can verify them:

```
Show relationships://all
```

## 4. Test Permissions

Test read/edit/share queries using natural language, asking the assistant to use check_permission:

```
Can charlie edit doc:readme?
```

Expected: NO_PERMISSION
Charlie is only a viewer

Then ask:

```
Can bob edit doc:readme?
```

Expected: HAS_PERMISSION
Bob is an editor

Try a share query:

```
Can bob share doc:readme?
```

Expected: NO_PERMISSION
Because share = owner only.

## 5. Explore the Graph

Explore resources by permission:

```
Which documents can alice share?
```

The assistant should use lookup_resources to find documents where alice has share permission, as described 

View subjects with permission:

```
Who can view doc:readme?
```

Expected subjects:

```
alice
bob
charlie
```

This uses `lookup_subjects`

## 6. Iterate

Now evolve the schema.

```
Add a manager role that can edit and also share documents.
```

The assistant will update the existing schema via write_schema and you can immediately test new permissions. This matches the iterative development guidance.

Inspect and retest:

```
Show schema://current
```

## Completion Milestone: Part 2

You’ve built a working permissions model with real schema, test data and permission checks working.

Next we will export our evolving model and save progress so it can be persisted and pushed to GitHub.
