# Part 4 — Query, Check, Debug, and Explore the Graph

## Learning Goals

By the end of this part, learners will:

- Inspect all current relationships
- Use lookup_resources to answer “what can this user do?”
- Use lookup_subjects to answer “who can do this on that?”
- Debug unexpected permission results using the recommended workflow
- Use the AuthZed MCP server to learn concepts while debugging

We assume you still have the document-sharing schema from Part 2/3:

- `document` with relations: `owner`, `editor`, `viewer`
- Permissions: `read`, `edit`, `share`

## 1. Inspect All Relationships

First, see everything currently in your in-memory instance:

In your assistant:

```
Show relationships://all
```
This uses the relationships://all resource that the dev MCP server exposes.

You should see entries similar to:

```
document:readme owner user:alice
document:readme editor user:bob
document:readme viewer user:charlie
```

## 2. “What Can This User Do?”

Now, answer questions like:

“Which documents can alice share?”

Ask the assistant:

```
Which documents can alice share?
```

Under the hood, it should call lookup_resources on:

- resource type: `document`
- permission: share
- subject: `user:alice` 

You should see:

- `document:readme`

Try a few more:

```
Which documents can bob edit?
Which documents can charlie read?
```

These correspond to:

- `lookup_resources(document, edit, user:bob)`
- `lookup_resources(document, read, user:charlie)`

This mimics real-world questions like:

- “Show me all files this user can access.”
- “List documents a user can share.”

## 3. “Who Can Do This on That?”

Now flip the question:

“Who can view doc:readme?”

Ask:

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

Try:

```
Who can edit doc:readme?
Who can share doc:readme?
```

These are direct analogs of common product questions:

- “Which users can edit this document?”

- “Who has share rights on this resource?”

## 4. Testing Edge Cases

The dev MCP server is meant for testing edge cases, including:

- Indirect permissions through nested relations
- Complex unions/intersections
- Caveats and context values
- Deep hierarchies 

Even with our simple document example, you can simulate more complexity.

### Example: Manager Role (If Added in Part 2)

Suppose your schema now includes:

```
relation manager: user
permission edit = owner + editor + manager
permission share = owner + manager
```

Create relationships:

```
Make dave a manager of document:readme.
```

Now test:

```
Can dave edit doc:readme?
Can dave share doc:readme?
Which documents can dave share?
Who can share doc:readme?
```
This lets you verify that your new relation correctly participates in permission expressions.

## 5. Using AuthZed MCP for Conceptual Help

When debugging, it’s common to ask conceptual questions.

Use the AuthZed MCP Server for this. It exposes tools like `search_docs`, `search_api`, `search_examples`, and prompts like `explain_concept` to answer conceptual questions with documentation references.

Example:

```
Using the AuthZed MCP server, explain how unions in permissions work in SpiceDB and show a simple example.
```

This combines:

- AuthZed MCP for knowledge and examples
- SpiceDB dev MCP for your live model and tests

## Completion Milestone: Part 4

You now know how to:

View all relationships in the system and use `lookup_resources` to see what a user can do. You also learned to combine the local dev MCP server with the AuthZed documentation MCP server for conceptual support.

Let's see how you can take this setup to production using AuthZed Cloud.
