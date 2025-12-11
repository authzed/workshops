# Part 2 — Build Your First Permissions Schema

In this step, you will learn to:

- Write and inspect a SpiceDB schema
- Add relationships
- Validate with permission checks
- Explore results

If you're new to the world of SpiceDB and authorization, please familiarize yourself with concepts such as [schema](https://authzed.com/docs/spicedb/concepts/schema), [relationships](https://authzed.com/docs/spicedb/concepts/relationships) and [permissions](https://authzed.com/docs/spicedb/concepts/caveats#checkpermission)
 
## 1. Write the Schema

A SpiceDB schema defines the types of objects found your application, how those objects can relate to one another, and the permissions that can be computed off of those relations. 

For this tutorial, we're going to create a Google Docs-style document sharing usecase. So ask your assistant:

```
Create a schema for a document sharing system. Documents have owners, editors, and viewers. 
Owners can `share`, editors can `edit`, and viewers can only `read`.
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

This basically defines a document sharing system where users can be owners, editors, or viewers of documents. Owners can share, editors can edit, and all three roles can read documents. 

The assistant uses `write_schema` to create the schema in your development instance. You can verify this by opening the terminal window where the SpiceDB Dev MCP Server.

## 2. Inspect the Schema

Run:

```
Show schema://current
```

The assistant should display the currently loaded schema.

This is how you verify correctness and discover errors like:

- undefined types
- syntax problems

The documentation indicates that schema errors can be debugged by reviewing the source and validation resources

## 3. Add Test Data

Now let’s populate the system by building relationships between different objects. This is the core tenet of any Relationship-Based Access Control (ReBAC) system. The real power of ReBAC comes from transforming authorization questions into graph reachability  problems, and then answering them efficiently.

Let's use natural language to create a relationship: (typically this would be done via an API/gRPC call in your app)

```
Create test data where alice owns doc:readme, bob is an editor, and charlie is a viewer.
```

Your assistant should call `update_relationships` to apply these relationships in memory.
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

Test read/edit/share queries using natural language, which asks the MCP Server to use `check_permission`:

```
Can charlie edit doc:readme?
```

Expected: `NO_PERMISSION`
Charlie is only a viewer

Then ask:

```
Can bob edit doc:readme?
```

Expected: `HAS_PERMISSION`
Bob is an editor

Try a share query:

```
Can bob share doc:readme?
```

Expected: `NO_PERMISSION`
Because share = owner only.

## 5. Explore the Graph

SpiceDB can traverse the graph to answer questions such as “what can this user do?” or “who can do this on that?”

Lets explore resources by permission:

```
Which documents can alice share?
```

Under the hood, it should call `lookup_resources` on:

- resource type: `document`
- permission: share
- subject: `user:alice` 

You should see:

- `document:readme`

This mimics real-world questions like:

- “Show me all files this user can access.”
- “List documents a user can share.”

You can also view subjects with permission:

```
Who can view doc:readme?
```

The assistant should call `lookup_subjects` for:

- `resource: document:readme`
- `permission: read` 

You should see:

- `user:alice`
- `user:bob`
- `user:charlie`

These are direct analogues of common product questions such as:

- “Which users can edit this document?”
- “Who has share rights on this resource?”

## 6. Using AuthZed MCP for Conceptual Help

When debugging, it’s common to ask the AI conceptual questions. Use the AuthZed MCP Server for this. It exposes tools like `search_docs`, `search_api`, `search_examples`, and prompts like `explain_concept` to answer conceptual questions with documentation references.

Example:

```
Using the AuthZed MCP server, explain how unions in permissions work in SpiceDB and show a simple example.
```

This combines:

- AuthZed MCP for knowledge and examples
- SpiceDB dev MCP for your live model and tests

## Completion Milestone: Part 2

You’ve built a working permissions model with real schema, test data and permission checks working.

Next we will export our evolving model and save progress so it can be persisted and pushed to GitHub. See you in [Part 3](mcp-assisted-authorization/3-export.md)