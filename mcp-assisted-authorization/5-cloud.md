# Part 5 — Taking It to Production with AuthZed Cloud

## Overview

So far, you have:

- Built and iterated on a permissions model using the SpiceDB Dev MCP Server
- Validated behavior with document sharing and (optionally) multi-tenant SaaS examples
- Exported schemas and validation files and versioned them in Git

This part shows how to take that work **toward production** using **AuthZed Cloud**:

1. Create a **Permissions System** in AuthZed Cloud
2. Configure **access control** for your application (Service Account, Token, Role, Policy)
3. Connect your application to AuthZed Cloud
4. Apply your **existing schema** (e.g., document sharing) in a managed, production-ready environment

---

## 1. Prerequisites

Before you start:

- You have an AuthZed Cloud account
- You have your schema exported (for example: `permissions/document-sharing.zed`)
- You have a basic understanding of how your application will talk to SpiceDB (e.g., via gRPC/HTTP client libraries)

---

## 2. Create a Permissions System (PS) in AuthZed Cloud

1. **Sign in** to AuthZed Cloud.
2. Click the **+Create** button to create a new **Permissions System (PS)**.
3. Fill in the required details:

   - **Type**  
     - Choose **Production** or **Development** depending on the environment you’re targeting.

   - **Name**  
     - Give your Permissions System a descriptive name, e.g.:
       - `doc-sharing-prod`
       - `doc-sharing-dev`

   - **Datastore**  
     - Choose a datastore. Currently, **CockroachDB** is supported for a PS on AuthZed Cloud.

   - **Update channel**  
     - Select how you want SpiceDB updates to be applied:
       - **rapid**: Receive new SpiceDB releases sooner.
       - **regular**: More conservative update cadence.

4. In the **Deployments** tab, configure:

   - **Deployment name**  
     - For example: `doc-sharing-prod-us-east`.

   - **Region**  
     - Choose a region for the deployment, such as:
       - `us-east-1`
       - `eu-central-1`

   - **vCPUs**  
     - Start with **2 vCPUs**. Monitor metrics and adjust as needed based on workload.

   - **Replicas**  
     - Number of replicas for primarily read workloads. A common starting point is **3**, but tune based on latency and availability requirements.

5. Click **Save** to create the Permissions System.

At this point, you have a managed SpiceDB deployment ready to receive your schema and data.

---

## 3. Configure Access (Service Account, Token, Role, Policy)

AuthZed Cloud lets you apply **least-privilege access** to your Permissions System. You will:

1. Create a **Service Account**
2. Create a **Token**
3. Create a **Role** with specific API permissions
4. Create a **Policy** binding the Role to the Service Account

### 3.1 Create a Service Account

A **Service Account** represents a single workload or application.

1. In the AuthZed Cloud UI, go to the Permissions System you just created.
2. Navigate to **Service Accounts**.
3. Click **Create Service Account**.
4. Provide:
   - **Name**: for example, `blog-app` or `doc-sharing-api`.
   - **Description**: e.g., “Service account for the document sharing application backend.”
5. Click **Save**.

Recommendation:  
Create a separate Service Account for each application or service that will access the SpiceDB API.

### 3.2 Create a Token

**Tokens** are long-lived credentials for Service Accounts. Your SpiceDB client uses a token in the `Authorization` header.

1. In the same Permissions System, click **Tokens** in the menu.
2. Click **Create token**.
3. Provide:
   - **Name** (e.g., `blog-app-token`)
   - **Description**
4. Save the token and **securely record** the value.  
   - This is what your application will present when calling the API.

### 3.3 Create a Role

A **Role** defines which API operations are allowed. Roles are later bound to Service Accounts via Policies.

1. Go to **Roles**.
2. Click **Create Role**.
3. Provide:
   - **Name** (e.g., `blog-app-role`)
   - **Description**
4. Add the following permissions for a typical application with full read/write access:

   - `ReadSchema`
   - `WriteSchema`
   - `DeleteRelationships`
   - `ReadRelationships`
   - `WriteRelationships`
   - `CheckPermission`

Later, for production hardening, you can split roles into read-only and read/write sets.

### 3.4 Create a Policy

A **Policy** binds a Role to a Service Account.

1. Go to **Policies**.
2. Click **Create policy**.
3. Provide:
   - **Name** (e.g., `blog-app-policy`)
   - **Description**
4. Choose:
   - The **Service Account** you created (e.g., `blog-app`)
   - The **Role** you just defined (e.g., `blog-app-role`)

5. Save the policy.

You now have:

- A Service Account (`blog-app`)
- A Token (for that Service Account)
- A Role with specific API permissions
- A Policy binding them together

Your application is now authorized to use the AuthZed Cloud Permissions System.

---

## 4. Apply Your Schema from the Workshop

Now that your AuthZed Cloud deployment is ready, you can take the schema you developed locally (for example, the document sharing schema) and use it in the cloud.

### 4.1 Use the Same Schema

From earlier parts of this workshop, you should have a file such as:

- `permissions/document-sharing.zed`

This is the schema you tested with the SpiceDB Dev MCP Server.

### 4.2 Load the Schema into AuthZed Cloud

Use one of the following approaches:

1. **CLI / client library**  
   Configure your client to point at your AuthZed Cloud SpiceDB endpoint with:

   - The correct **endpoint URL**
   - The **Token** for your Service Account in the `Authorization` header
   - TLS/other required settings

   Then call the equivalent of `WriteSchema` with the contents of `document-sharing.zed`.

2. **IDE / tools**  
   If your environment or tooling has native AuthZed integration, configure it with:
   - Endpoint
   - Token
   - Permissions System ID

   And then write the schema from your local file.

Once applied, your AuthZed Cloud deployment is running the **same schema** you developed using the MCP dev server.

---

## 5. Connect Your Application

Finally, configure your application to use this Permissions System instead of the local dev server.

High-level steps:

1. Update your application configuration with:

   - **SpiceDB endpoint** (AuthZed Cloud URL)
   - **Token** for the Service Account (from the Tokens step)
   - Any required TLS / region-specific config

2. Use the same APIs you conceptually used via MCP tooling:
   - `CheckPermission` (for authorization decisions)
   - `WriteRelationships` (for updating relationships)
   - `ReadRelationships` / lookups as needed

3. For your document-sharing use case, the flow now becomes:

   - When a document is created:
     - Write relationships like `document:<id> owner user:<user-id>`
   - When a user tries to view/edit/share:
     - Call `CheckPermission` for `read`, `edit`, or `share` on `document:<id>` for `user:<user-id>`.
   - Authorization decisions are enforced by the production SpiceDB deployment on AuthZed Cloud.

---

## 6. Production Readiness Tips

As you move to production:

- Start with a **Development** Permissions System in AuthZed Cloud, mirroring your dev/staging environment.
- Use **Production** Permissions Systems only after:
  - Schema is stable
  - Validation tests are robust
  - Observability and metrics are in place
- Consider:
  - Separate Service Accounts and Tokens for each environment (dev/staging/prod)
  - More restrictive Roles in production (e.g., read-only for most services, write access for admin/ingest services only)
  - Gradual rollout of schema changes and careful testing of new permissions

---

## Completion Milestone: Part 6

You have:

Created a Permissions System in AuthZed Cloud while configuring least-privilege access via Service Accounts, Tokens, Roles, and Policies. You also applied the schema built in the workshop to a managed SpiceDB deployment and connected your application to a production-ready authorization system

## Next Steps

Now that you know the basics see how you can build permissions for a multi-tenant SaaS application with complex roles and hierarchies. Here's an example scenario:

- Organizations have projects
- Projects have documents
- Users belong to organizations
- Access scoped by tenant
- No cross-tenant permissions

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

```
org:acme admin user:alice
org:acme member user:bob

project:website parent org:acme
project:website member user:bob

document:homepage parent project:website
document:homepage editor user:bob
```

### Test

```
Can alice edit document:homepage?
Can bob read document:homepage?
Can charlie view document:homepage?
```

## Homework

1. Add an auditor role:

- Auditors can read everything in their org
- Never edit

2. Exercise B — Add Inheritance for Editors

- Allow project members to edit documents.