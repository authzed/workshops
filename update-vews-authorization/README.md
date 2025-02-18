## Update A View Based on Permissions 

This workshop will illustrate how you can update a view based on what permissions the user has. The workshop uses a NextJS template by Vercel for an admin dashboard, written in TypeScript. The software and frameworks used are: 

- NextJS 
- Tailwind CSS
- Postgres (via Neon)
- SpiceDB

### Why is this important? 

Permissions are hard!
A common pattern in a web app is to show a user only the options that they are authorized to access. 

### What you will learn

- How to model a schema based on a use case
- How to write relationships between objects and subjects. For ex: A user and a product
- How to check for permissions. Ex: Does user Alice have 'delete' permissions on Product XYZ.

At the end of this tutorial, we'll have an admin dashboard that checks a user's permissions and shows a user the 'delete' button for a product only if they have admin access to do so. 

**Last Updated**: Feb 20, 2025

## Tutorial

#### Setup 

For this tutorial we'll use this [open source Admin Dashboard template](https://next-admin-dash.vercel.app/) created by Vercel. The install instructions are on the Vercel page. but here's a TL;DR:

1. Deploy the template [from here](https://vercel.com/templates/next.js/admin-dashboard-tailwind-postgres-react-nextjs). You will need a Vercel account for the automated deployment. You can bypass this by cloning the repo, but will have to manually setup the Postgres database. 

2. Create an OAuth app on GitHub and note down the client ID and Secret. Get your AUTH_SECRET generated from here: https://generate-secret.vercel.app/32 . 

3. Once deployed to GitHub, clone the app locally and run `npm install` and `npm run dev`. Follow the instructions on the page to create Postgres tables for Products & Users. Also, create a user which we will use later as our Admin user. 

4. Uncomment out the code in `route.ts` and go to `localhost:3000/api/seed` to populate the Products table. Ensure that the `return` statement is at the end of the code. 

5. Rename the `.env.example` file to `.env` and add the required variables. You can find `POSTGRES_URL` in your Vercel dashboard. Run the app locally should now should you a dashboard of products with Prices, Status etc. displayed. 

Congrats your Admin Dashboard is now setup

#### Adding SpiceDB

Let's add SpiceDB into this project and start a local instance of SpiceDB as our database for write permissions. 

1. Run `npm i @authzed/authzed-node` to add the Authzed package into your project

2. This guide assumes you've [installed SpiceDB](https://authzed.com/docs/spicedb/getting-started/installing-spicedb). Start a local instance of SpiceDB with the command `spicedb serve --grpc-preshared-key "sometoken"`

3. Add the following variables to the `.env` file:

```
# Same value set for --grpc-preshared-key
SPICEDB_TOKEN=sometoken
# localhost:50051 for local development
SPICEDB_ENDPOINT=localhost:50051
```

We'll write our schema and relationships to this local instance of SpiceDB. 

Note: This is just for learning purposes so the permissions are written to the local datastore which is ephemeral. Also we will use insecure connections and not TLS to communicate with SpiceDB. 

#### Adding a Schema

A [SpiceDB schema](https://authzed.com/docs/spicedb/concepts/schema) defines the types of objects found, how those objects relate to one another, and the permissions that can be computed off of those relations. In this project we have a user and we have products. Currently the user can view, edit and delete all the products. We're going to build permission checks in such a way that the user can view all the products, but can delete a product only if they are authorized to do so. 

In our usecase the subject and the object is a `user` and a `product`. Also the permissions are to `view` and `delete`. Our schema looks something like this:

```
definition user {}

definition product {
    relation viewer: user | user:*
    relation admin: user

    permission delete = admin
    permission view = admin + viewer
}
```
We need to write this schema to the instance of SpiceDB when the app starts. In our `actions.ts` file import the following files:

```
import { v1 } from '@authzed/authzed-node';
import {
  CheckPermissionResponse_Permissionship,
  ClientSecurity,
  RelationshipUpdate_Operation,
  Relationship as SpiceDBRelationship
} from '@authzed/authzed-node/dist/src/v1';
```

Define the schema in your code. (You can also write this to a separate `.zed` file)

```
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
      ClientSecurity.INSECURE_LOCALHOST_ALLOWED
    );
    promiseClient = testClient.promises;

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

Now we've to ensure this method is called when the app starts. Go to the `db.ts` file

`import { setupApp } from 'app/(dashboard)/actions';`

Let's add a function that calls the setupApp() method when the app starts.

```
async function initiateAppSetup () {
  try {
    const result = await setupApp();
    console.log('Setup successful:', result);
    return true;
  } catch (error) {
    console.error('Setup failed:', error);
    return false;
  }
}

(async () => {
  await initiateAppSetup();
})();
```

Run `npm run dev` in the Terminal (ensure the local instance of SpiceDB is running). You should see a message on the terminal and in SpiceDB that the schema is written. 

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
      ClientSecurity.INSECURE_LOCALHOST_ALLOWED
    );
    promiseClient = testClient.promises;

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

    console.log(response)

    return apiCalls;

  } catch (error) {
    console.error('SpiceDB connection check failed:', error);
    if (error instanceof Error && error.message.includes('UNAVAILABLE')) {
      return { 
        isRunning: false, 
        error: `SpiceDB server is not running. Please start the server using 'docker-compose up -d' and try again.` 
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

First, go to the `product.tsx` file and add this method as the form action for the delete button. The form action sends the `id` of the product to the method

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

In the `actions.ts` file add a method called `deleteProduct`. For now we'll see the result of this check only in the terminal:

```
export async function deleteProduct(formData: FormData) {
  let id = String(formData.get('id'));

  const client = v1.NewClient(
    process.env.SPICEDB_TOKEN!,
    process.env.SPICEDB_ENDPOINT!,
    ClientSecurity.INSECURE_LOCALHOST_ALLOWED
  );
  promiseClient = client.promises;

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

This API provides the ability to find all the resources for a particular subject and permission. For example: What products can the user delete? To perform this check via [Zed](https://authzed.com/docs/spicedb/getting-started/installing-zed) the command is `zed permission lookup-resources product delete user:1`

This is what it looks like in code:

```
export async function getDeletableProductIds(userId: string | undefined): Promise<string[]> {
  
  // create SpiceDB client and validate user ID first

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

  Let's modify the `db.ts` file to filter products from the database based on which ones are delete-able

  ```
  export async function fetchProducts(userId: string): Promise<SelectProduct[]> {
  const deletableIds = await getDeletableProductIds(userId);

  console.log(`Filtering products by deletable IDs:`, deletableIds);

  if (deletableIds.length === 0) {
    return []; // Return an empty list if no deletable products
  }

  // Fetch only products the user has permission to delete
  const authorizedProducts = await db
    .select()
    .from(products)
    .where(inArray(products.id, deletableIds.map(id => Number(id))));

  return authorizedProducts;
}
```

Let's modify the code in the `products-table.tsx` to get a list of Product IDs that are delete-able. We can perform this once when the app is mounted:

```
import { getDeletableProductIds } from 'app/(dashboard)/actions';
const HARDCODED_USER_ID = "1"; 

  useEffect(() => {
    async function fetchDeletableIds() {
      const ids = await getDeletableProductIds(HARDCODED_USER_ID);
      setDeletableProductIds(ids);
    }
    fetchDeletableIds();
  }, []); // Only run once on component mount
  ```

  Also, modify the `<TableBody>` code to include this:

  ```
  <TableBody>
    {products.map((product) => (
        <Product key={product.id} product={product} deletableProductIds={deletableProductIds} />
    ))}
  </TableBody>
```

Now we've to modify the `product.tsx` component so that it shows the delete button only for the products it's authorized to. 

```
export function Product({ product, deletableProductIds }: { product: SelectProduct, deletableProductIds: string[] }) {
  const canDelete = deletableProductIds.includes(String(product.id));
```

Add the logic in the component:

```
<DropdownMenuItem>Edit</DropdownMenuItem>
    {/* Show Delete button only if user has permission */}
    {canDelete && (
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
```

We can finish up by writing code to perform the deletion from the database. It's good practice to perform another permission check before deletion in case the permissions have changed. Let's modify our `deleteProduct()` method in `actions.ts`

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
      objectId: '1', // ✅ Hardcoded user ID
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
    console.log("🟡 Deleting product ID:", id);
    await deleteProductById(Number(id));
    console.log("✅ Product deleted successfully");
    revalidatePath('/');
    return { success: true }; // Return success message
    
  } catch (error) {
    console.error("🚨 Error deleting product:", error);
    return { success: false, message: "Failed to delete product." };
  }
}
```

That's it! When you run the app, you'll see that only Product id=1 displays the 'Delete' button. Try adding 'delete' permissions to other products and see for yourself. The code for the entire project is in this folder. 

#### Troubleshooting

// TBA