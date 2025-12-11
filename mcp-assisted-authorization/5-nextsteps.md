# Part 6 — Next Steps

Now that you know the basics, see how you can build permissions for a multi-tenant SaaS application with complex roles and hierarchies. Here's an example scenario:

- Organizations have projects
- Projects have documents
- Users belong to organizations
- Access scoped by tenant
- No cross-tenant permissions

This is a fairly common scenario in the industry, yet traditional authorization techniques such as Role-Based Access Control (RBAC) or Attribute-Based Access Control (ABAC) struggle with the complexities, especially with scale and latency requirements. Fortunately, ReBAC combined with SpiceDB's schema is flexible to model these requirements, and the operators such as `+`, `-`, `->`, `&` makes modelling easy.

### Example Schema

```
definition user {}

definition organization {
  relation admin: user
  relation member: user

  permission manage = admin + member
}

definition project {
  relation parent: organization
  relation member: user
  relation viewer: user

  permission read = member + viewer + parent.admin
  permission edit = member + parent.admin
}

definition document {
  relation parent: project
  relation owner: user
  relation editor: user
  relation viewer: user

  permission read = owner + editor + viewer + parent.read
  permission edit = owner + editor + parent.edit
}
```

### Sample Relationships

Here are some sample relationships that you can write to SpiceDB;

```
org:acme admin user:alice
org:acme member user:bob

project:website parent org:acme
project:website member user:bob

document:homepage parent project:website
document:homepage editor user:bob
```

### Test

Once the test data is written to your SpiceDB instance, ask your AI assistant:

```
Can alice edit document:homepage?
Can bob read document:homepage?
Can charlie view document:homepage?
```

## Homework

1. Add an auditor role:

- Auditors can read everything in their org
- Never edit any document

2. Add Inheritance for Editors

- Allow project members to edit documents.

---

FIN