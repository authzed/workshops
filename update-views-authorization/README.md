## Update A Web View Based on Permissions 

This workshop will illustrate how you can update a view based on what permissions the user has. The workshop uses a NextJS template by Vercel for an admin dashboard, written in TypeScript. The software and frameworks used in the tutorial are: 

- NextJS 
- Tailwind CSS
- Postgres (via Neon)
- SpiceDB

### Why is this important? 

Permissions are hard!
A common pattern in a web app is to show a user only the options that they are authorized to access. 

### What you will learn

- How to model a schema based on a use case
- How to write relationships between subjects and resources. For ex: A user and a product
- How to check for permissions. Ex: Does user Alice have 'delete' permissions on Product XYZ.
- How to update a user interface based on what permissions the user has. 

At the end of this tutorial, we'll have an admin dashboard that checks a user's permissions and shows a user the 'delete' button for a product only if they have admin access to do so. Here's [the working solution for this tutorial](https://github.com/authzed/workshops/tree/main/update-views-authorization/working-solution). 

This tutorial is meant for learning purposes only. Please follow best practices when deploying to production. 

**Last Updated**: Mar 24, 2025

## Tutorial

Here's a livestream video that goes through this tutorial step-by-step. The text version can be found below.

[![YouTube thumb](https://github.com/authzed/workshops/tree/main/update-views-authorization/assets/youtube-thumb.png)](http://www.youtube.com/watch?v=ooWQ903blZo "Updating A Web View Based on Permissions")

### Setup 

For this tutorial we'll use this [open source Admin Dashboard template](https://next-admin-dash.vercel.app/) created by Vercel. The install instructions are on the Vercel page. but here's a TL;DR:

1. Create an OAuth app on GitHub [with these instructions](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).
    * Enter an application name
    * Homepage URL: http://localhost:3000
    * Callback URL: http://localhost:3000/api/auth/callback/github
    * Generate a Client Secret
    * Note down both the Client ID and Client Secret.  You will need these later when configuring `AUTH_GITHUB_ID` and `AUTH_GITHUB_SECRET` environment variables.

2. Get a Vercel secret `AUTH_SECRET`
    *  Generate from here: https://generate-secret.vercel.app/32.  Note it down. 

3. Deploy the Vercel template [from here](https://vercel.com/templates/next.js/admin-dashboard-tailwind-postgres-react-nextjs). You will need a Vercel account for the automated deployment.
      * Add Neon Storage -> Serverless Postgres when prompted.
      * Choose a region and 'Development' environmnet when prompted by Neon.
      * Enter the three `Environment Variables` when prompted, using the values from steps 1 and 2 above.
      * You might get an error: `[cause]: Error: No database connection string was provided to neon(). Perhaps an environment variable has not been set?`.  Don't fret - you can trigger a re-deploy in the Vercel -> Deployments tab, making sure to choose `Preview` instead of production
         
      (Note: You could bypass the Vercel deployment but you would have to manually setup the Postgres database.)

4. In the Neon Console (Vercel Dashboard -> Storage) run the following commands to create your database tables:

```SQL
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  username VARCHAR(255)
);

CREATE TYPE status AS ENUM ('active', 'inactive', 'archived');

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  image_url TEXT NOT NULL,
  name TEXT NOT NULL,
  status status NOT NULL,
  price NUMERIC(10, 2) NOT NULL,
  stock INTEGER NOT NULL,
  available_at TIMESTAMP NOT NULL
);

INSERT INTO users (id, email, name, username) VALUES (1, 'me@test.com', 'Me', 'username');
```


5. Now, clone the repo that was generated as part of the Vercel deployment flow, so we can run it locally.

6. Inside the new repo, pull the environment configuration from Vercel to your local repo with these commands:
     ```bash
    npm i -g vercel
    vercel link
    vercel env pull
    ```
    This step will create a file called `.env.local` locally with the correct environment variables created as part of Vercel templated deployment.

6. Install and run the app:
    ```bash
    pnpm install
    pnpm dev
    ```
    Now, you will have application running locally, and navigating to http://localhost:3000/ should show you an empty Products page.

7. Uncomment out the code in `route.ts` and go to `localhost:3000/api/seed` to populate the Products table. Ensure that the `return` statement is at the end of the code. 

Running the app locally should now show you a dashboard of products with Prices, Status etc. displayed. 

Congrats! The Admin Dashboard is now setup.

### Adding SpiceDB

Let's add some SpiceDB into the mix and start a local instance of SpiceDB as our database for write permissions. 

1. Run `pnpm i @authzed/authzed-node` to add the Authzed package into your project

2. This guide assumes you've [installed SpiceDB](https://authzed.com/docs/spicedb/getting-started/installing-spicedb). Start a local instance of SpiceDB with the command `spicedb serve --grpc-preshared-key "sometoken"`

3. Add the following variables to the `.env.local` file:

```
# Same value set for --grpc-preshared-key
SPICEDB_TOKEN=sometoken
# localhost:50051 for local development
SPICEDB_ENDPOINT=localhost:50051
```

We'll write our schema and relationships to this local instance of SpiceDB. 

**Note:** This instance of SpiceDB uses in-memory datastore which is ephemeral. Also, we will use insecure connections and not TLS to communicate with SpiceDB. 

#### Adding a Schema

A [SpiceDB schema](https://authzed.com/docs/spicedb/concepts/schema) defines the types of objects found, how those objects relate to one another, and the permissions that can be computed off of those relations. In this project we have a user and we have products. Currently the user can view, edit and delete all the products. We're going to build permission checks in such a way that the user can view all the products, but can delete a product only if they are authorized to do so. 

In our usecase the subject and the resource is a `user` and a `product`. Also the permissions are to `view` and `delete`. Our schema looks something like this:

```
definition user {}

definition product {
    relation viewer: user | user:*
    relation admin: user

    permission delete = admin
    permission view = admin + viewer
}
```

`relation viewer: user` and `relation admin: user` indicate that `viewer` and `admin` are related to `user`. 
We add `relation viewer: user | user:*` as a wildcard. Wildcard support allows relations to include all subjects of a particular type, allowing a relation or permission to become public for checks. A relationship can now be written between your resource and *all* users.

Let's write this schema to the instance of SpiceDB when the app starts. In our `actions.ts` file import the following files:

```
import { v1 } from '@authzed/authzed-node';
```

Define the schema in your code. (You can also write this to a separate `.zed` file)

```s
const schema = `
definition user {}

definition product {
    relation viewer: user | user:*
    relation admin: user

    permission delete = admin
    permission view = admin + viewer
}
`;
```

Now let's create a method called `setupApp()` that runs on app start, and then write the schema using the SpiceDB client

```
export async function setupApp() {  
  try{
    const apiCalls: { method: string, description: string }[] = [];

    const testClient = v1.NewClient(
      process.env.SPICEDB_TOKEN!,
      process.env.SPICEDB_ENDPOINT!,
      v1.ClientSecurity.INSECURE_LOCALHOST_ALLOWED
    );
    const promiseClient = testClient.promises;

    const schemaRequest = v1.WriteSchemaRequest.create({
      schema: schema,
    });
     
    // Write the schema to SpiceDB
    try {
      apiCalls.push({
        method: 'WriteSchema',
        description: 'Writing schema to SpiceDB...'
      });

      await promiseClient.writeSchema(v1.WriteSchemaRequest.create({ schema }));
      apiCalls.push({
        method: 'WriteSchema',
        description: `Schema written successfully:\n${schema}`
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      apiCalls.push({
        method: 'WriteSchema',
        description: `Failed to write schema: ${errorMessage}`
      });
      throw new Error(`Failed to write schema to SpiceDB. Error: ${errorMessage}`);
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log(apiCalls);
    return apiCalls;

  } catch (error) {
    console.error('SpiceDB connection check failed:', error);
    if (error instanceof Error && error.message.includes('UNAVAILABLE')) {
      return { 
        isRunning: false, 
        error: `SpiceDB server is not running.` 
      };
    }
    return { 
      isRunning: false, 
      error: `Failed to connect to SpiceDB: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
}
```

Now we've to ensure this method is called when the app starts - add a call to the method at the top of actions.ts

```
setupApp();
```

Run `pnpm dev` in the Terminal (ensure the local instance of SpiceDB is running). You should see a message on the terminal and in SpiceDB that the schema is written. 

#### Write Relationships

During the setup phase, we created a user in the Postgres database with this command:
`INSERT INTO users (id, email, name, username) VALUES (1,'me@site.com', 'Me', 'username');`

Currently this user has permissions to view, edit and delete each product. Let's change it so that there is a permission check when a user clicks on the delete button for a product. 

In the `setupApp()` method, add this code snippet to add a subject and object. We'll hardcode that the user has `admin` permissions on Product with ID = 1. In this case 'Smartphone X Pro'

```
export async function setupApp() {  
  try{
    const apiCalls: { method: string, description: string }[] = [];

    // Create a temporary client just to test the connection
    const testClient = v1.NewClient(
      process.env.SPICEDB_TOKEN!,
      process.env.SPICEDB_ENDPOINT!,
      v1.ClientSecurity.INSECURE_LOCALHOST_ALLOWED
    );
    const promiseClient = testClient.promises;
     
    // Write the schema to SpiceDB
    try {
      apiCalls.push({
        method: 'WriteSchema',
        description: 'Writing schema to SpiceDB...'
      });

      await promiseClient.writeSchema(v1.WriteSchemaRequest.create({ schema }));
      apiCalls.push({
        method: 'WriteSchema',
        description: `Schema written successfully:\n${schema}`
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      apiCalls.push({
        method: 'WriteSchema',
        description: `Failed to write schema: ${errorMessage}`
      });
      throw new Error(`Failed to write schema to SpiceDB. Error: ${errorMessage}`);
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Write first relationship

    const resource = v1.ObjectReference.create({
      objectType: 'product',
      objectId: '1',
    });
     
    const loggedInUser = v1.ObjectReference.create({
      objectType: 'user',
      objectId: '1',
    });
     
    const writeRequest = v1.WriteRelationshipsRequest.create({
      updates: [
        // User is an Admin on Product with ID 1
        v1.RelationshipUpdate.create({
          relationship: v1.Relationship.create({
            resource: resource,
            relation: 'admin',
            subject: v1.SubjectReference.create({ object: loggedInUser }),
          }),
          operation: v1.RelationshipUpdate_Operation.CREATE,
        }),
      ],
    });
     
    const response = await promiseClient.writeRelationships(writeRequest)
    apiCalls.push({
      method: 'WriteRelationships',
      description: `Relationship written successfully:`
    }); 

    console.log(apiCalls)
    console.log(response)

    return apiCalls;

  } catch (error) {
    console.error('SpiceDB connection check failed:', error);
    if (error instanceof Error && error.message.includes('UNAVAILABLE')) {
      return { 
        isRunning: false, 
        error: `SpiceDB server is not running.` 
      };
    }
    return { 
      isRunning: false, 
      error: `Failed to connect to SpiceDB: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
}
```

Run `npm run dev` and check the console for messages about this relationship written to SpiceDB. We've now established that the user has `delete' permissions only on product 1. 

#### Check Permissions

Now that we've written a relationship to SpiceDB, we can perform permission checks as well. 

First, go to the `product.tsx` file and add this method as the form action for the delete button. The form action sends the Product `id` to the method

```
<DropdownMenuLabel>Actions</DropdownMenuLabel>
    <DropdownMenuItem>Edit</DropdownMenuItem>
    <DropdownMenuItem>
        <form action={deleteProduct}>
        <input type="hidden" name="id" value={product.id} />
        <button type="submit">Delete</button>
        </form>
    </DropdownMenuItem>
```

In the `actions.ts` file replace the existing method called `deleteProduct`. For now we'll see the result of this check only in the terminal:

```
export async function deleteProduct(formData: FormData) {
  let id = String(formData.get('id'));

  const client = v1.NewClient(
    process.env.SPICEDB_TOKEN!,
    process.env.SPICEDB_ENDPOINT!,
    v1.ClientSecurity.INSECURE_LOCALHOST_ALLOWED
  );
  const promiseClient = client.promises;

  const resource = v1.ObjectReference.create({
    objectType: 'product',
    objectId: id
  });
   
  const loggedInUser = v1.ObjectReference.create({
    objectType: 'user',
    objectId: '1',
  });

  // check permissions
     
  const adminCanDelete = await promiseClient.checkPermission(v1.CheckPermissionRequest.create({
    resource,
    permission: 'delete',
    subject: v1.SubjectReference.create({
      object: loggedInUser,
    }),
  }));

  if(adminCanDelete.permissionship === v1.CheckPermissionResponse_Permissionship.HAS_PERMISSION) {
    console.log('User has permission to delete product');
    // delete product from database
  }
  else {
    console.log('User does not have permission to delete product');
    return 'Not Authorized';
  }
}
```

Congrats! We've written a schema, written a relationship and performed a permission check with SpiceDB. Now it's time to update our views based on user permissions - which was the objective of the tutorial!

#### Multiple Permission Checks

We've performed a Permission check to see if the user has 'delete' permissions on Product id = 1. It is inefficient to perform permission checks against each product in the table. There are couple of ways to see what resources a user can access:

- filtering with LookupResources
- checking with [CheckBulkPermissions](https://buf.build/authzed/api/docs/main:authzed.api.v1#authzed.api.v1.PermissionsService.CheckBulkPermissions)

If the number of resources that a user has access to is sufficiently small, you can use `LookupResources` to get the full list of resources for which a user has a particular permission, and then use that as a filtering clause in your database query. If the number of resources that a user has access to is sufficiently large and `LookupResources` can't satisfy the use case anymore, another approach is to fetch a page of results and then call CheckBulkPermissions to determine which of the resources are accessible to the user.

For our usecase we'll use `LookupResources`. 

#### Lookup Resources

This API provides the ability to find all the resources for a particular subject and permission. For example: What products can the user with User id = 1 delete? To perform this check via [Zed](https://authzed.com/docs/spicedb/getting-started/installing-zed) the command is `zed permission lookup-resources product delete user:1`

This is what it looks like in code:

```
export async function getDeletableProductIds(userId: string | undefined): Promise<string[]> {
  
  // create SpiceDB client

  const lookupRequest = v1.LookupResourcesRequest.create({
    consistency: v1.Consistency.create({
      requirement: {
        oneofKind: 'fullyConsistent',
        fullyConsistent: true,
      },
    }),
    resourceObjectType: "product", // Ensure this matches your schema
    permission: "delete",
    subject: v1.SubjectReference.create({
      object: v1.ObjectReference.create({
        objectType: "user",
        objectId: userId,  
      }),
    }),
  });

  try {
    const responses = await promiseClient.lookupResources(lookupRequest);
    const productIds = responses.map(response => response.resourceObjectId).filter(Boolean);

    console.log(`User ${userId} can delete products:`, productIds);
    return productIds;
  } catch (error) {
    console.error("LookupResources API Error:", error);
    throw new Error("Failed to fetch deletable product IDs.");
  }
}
  ```

  This method returns a list of Product IDs that the user has 'delete' permissions on. 


Now that we have the list of Products that the user can delete, we need to update the dashboard. 
Let's modify the code in the `db.ts`.  First, lets add a new field to the product object called `isDeletable` e.g.

```
export const products = pgTable('products', {
  id: serial('id').primaryKey(),
  imageUrl: text('image_url').notNull(),
  name: text('name').notNull(),
  status: statusEnum('status').notNull(),
  price: numeric('price', { precision: 10, scale: 2 }).notNull(),
  stock: integer('stock').notNull(),
  availableAt: timestamp('available_at').notNull(),
  isDeleteable: boolean('is_deleteable').notNull().default(false),
});
```

Since the list of fields above is tightly coupled to our database table we need to add a column to the `products` table to keep thiings working (even though we won't read/write this column in the database, it's easier for this workshop just to edit the existing `products` object). Run this command in your SQL Editor in Neon. You can also manually add the column to the table in the Neon UI.

```
ALTER TABLE "public"."products" 
ADD COLUMN "is_deleteable" boolean NOT NULL DEFAULT false
```


Add a new function to enrich the products returned from the database with authorization info from SpiceDB, based on what products the current user is allowed to delete:

```
async function enrichWithAuthInfo(products: SelectProduct[]) {
  const HARDCODED_USER_ID = "1"; // ✅ Hardcoded user ID

  const ids = await getDeletableProductIds(HARDCODED_USER_ID);
  products.forEach((product) => {
    product.isDeleteable = ids.includes(product.id.toString());
  });

  return products;
}
  ```

  You'll have to update your imports to pull in the `boolean` and `getDeletableProductIds` references.

  Before we return the products from the main `getProducts` function, call our new `enrichWithAuthInfo` function like this:
  ```
  return {
    products: await enrichWithAuthInfo(moreProducts),
    newOffset,
    totalProducts: totalProducts[0].count
  };
  ```

Now we've to modify the `product.tsx` component so that it shows the delete button only for the products it's authorized to. 

Add the `product.isDeleteable` logic in the component like this:

```
<DropdownMenuContent align="end">
  <DropdownMenuLabel>Actions</DropdownMenuLabel>
  <DropdownMenuItem>Edit</DropdownMenuItem>
  {/* Show Delete button only if user has permission */}
  {product.isDeleteable && (
    <DropdownMenuItem>
      <form
        action={async (formData) => {
          const response = await deleteProduct(formData);

          if (!response.success) {
            alert(response.message); // Show error message in UI
          }
        }}
      >
        <input type="hidden" name="id" value={product.id} />
        <button type="submit">Delete</button>
      </form>
    </DropdownMenuItem>
  )}
</DropdownMenuContent>

```

We can finish up by writing code to perform the deletion from the database. It's good practice to perform another permission check before deletion in case the permissions have changed. This is a benefit of a centralized authorization approach. 

Let's modify our `deleteProduct()` method in `actions.ts`

```
export async function deleteProduct(formData: FormData) {
  let id = String(formData.get('id'));
  if (!id) {
    throw new Error("Invalid product ID.");
  }
  const promiseClient = ensureClientInitialized();

  const resource = v1.ObjectReference.create({
    objectType: 'product',
    objectId: id
  });

  const loggedInUser = v1.SubjectReference.create({
    object: v1.ObjectReference.create({
      objectType: 'user',
      objectId: '1', // Hardcoded user ID
    }),
  });

  const adminCanDelete = await promiseClient.checkPermission(
    v1.CheckPermissionRequest.create({
      resource,
      permission: 'delete',
      subject: loggedInUser,
    })
  );

  if (adminCanDelete.permissionship !== v1.CheckPermissionResponse_Permissionship.HAS_PERMISSION) {
    console.log("User does not have permission to delete product");
    return { success: false, message: "You do not have permission to delete this product." };
  }

  console.log("User has permission to delete product");

  try {
    console.log("Deleting product ID:", id);
    await deleteProductById(Number(id));
    console.log("Product deleted successfully");
    revalidatePath('/');
    return { success: true }; // Return success message
    
  } catch (error) {
    console.error("Error deleting product:", error);
    return { success: false, message: "Failed to delete product." };
  }
}
```

That's it! When you run the app, you'll see that only Product id=1 displays the 'Delete' button. Try adding 'delete' permissions to other products and see for yourself. The code for the entire project is available in [this folder](https://github.com/authzed/workshops/tree/main/update-views-authorization/working-solution) 

#### Troubleshooting

If you see issues related to loading your Avatar, when you log in via the GitHub app, updated your `next.config.ts` to have this content (see the `pathname` field):

```
export default {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.public.blob.vercel-storage.com',
        search: ''
      }
    ]
  }
};
```
