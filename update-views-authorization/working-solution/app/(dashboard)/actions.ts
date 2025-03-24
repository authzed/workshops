'use server';

import { deleteProductById } from '@/lib/db';
import { revalidatePath } from 'next/cache';
import { v1 } from '@authzed/authzed-node';

function ensureClientInitialized(): ReturnType<typeof v1.NewClient>['promises'] {
  return v1.NewClient(
    process.env.SPICEDB_TOKEN!,
    process.env.SPICEDB_ENDPOINT!,
    v1.ClientSecurity.INSECURE_LOCALHOST_ALLOWED
  ).promises;
}

const schema = `
definition user {}

definition product {
    relation viewer: user | user:*
    relation admin: user

    permission delete = admin
    permission view = admin + viewer
}
`;

setupApp();

export async function setupApp() {
  try {
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

    console.log(response);
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

export async function getDeletableProductIds(userId: string | undefined): Promise<string[]> {

  const promiseClient = ensureClientInitialized();

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