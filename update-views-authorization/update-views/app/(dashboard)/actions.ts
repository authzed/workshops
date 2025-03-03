'use server';

import { deleteProductById } from '@/lib/db';
import { revalidatePath } from 'next/cache';
import { v1 } from '@authzed/authzed-node';
import {
  CheckPermissionResponse_Permissionship,
  ClientSecurity,
  RelationshipUpdate_Operation,
  Relationship as SpiceDBRelationship
} from '@authzed/authzed-node/dist/src/v1';

let client: ReturnType<typeof v1.NewClient> | null = null;
let promiseClient: ReturnType<typeof v1.NewClient>['promises'] | null = null;

function ensureClientInitialized(): ReturnType<typeof v1.NewClient>['promises'] {
  if (!client || !promiseClient) {
    throw new Error("SpiceDB client not initialized. Please initialize the app first.");
  }
  return promiseClient;
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

export async function setupApp() {  
  try {
    const apiCalls: { method: string, description: string }[] = [];

    if (!process.env.SPICEDB_TOKEN || !process.env.SPICEDB_ENDPOINT) {
      throw new Error("SPICEDB_TOKEN or SPICEDB_ENDPOINT is missing.");
    }

    // 🔹 Lazy initialization: Only create the client if it doesn't exist
    if (!client) {
      console.log("🔹 Initializing SpiceDB client...");
      client = v1.NewClient(
        process.env.SPICEDB_TOKEN!,
        process.env.SPICEDB_ENDPOINT!,
        ClientSecurity.INSECURE_LOCALHOST_ALLOWED
      );
      promiseClient = client.promises;
    }

    console.log("✅ SpiceDB client initialized");

    const schemaRequest = v1.WriteSchemaRequest.create({ schema });

    try {
      apiCalls.push({ method: 'WriteSchema', description: 'Writing schema to SpiceDB...' });

      await promiseClient.writeSchema(v1.WriteSchemaRequest.create({ schema }));
      apiCalls.push({ method: 'WriteSchema', description: `Schema written successfully:\n${schema}` });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      apiCalls.push({ method: 'WriteSchema', description: `Failed to write schema: ${errorMessage}` });
      throw new Error(`Failed to write schema to SpiceDB. Error: ${errorMessage}`);
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Write initial relationships
    const resource = v1.ObjectReference.create({ objectType: 'product', objectId: '1' });
    const loggedInUser = v1.ObjectReference.create({ objectType: 'user', objectId: '1' });

    const writeRequest = v1.WriteRelationshipsRequest.create({
      updates: [
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

    const response = await promiseClient.writeRelationships(writeRequest);
    apiCalls.push({ method: 'WriteRelationships', description: `Relationship written successfully` });

    console.log(response);

    return apiCalls;

  } catch (error) {
    console.error('SpiceDB connection check failed:', error);
    return { 
      isRunning: false, 
      error: `Failed to connect to SpiceDB: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
}

// 🔹 Ensure `setupApp` runs before using SpiceDB
await setupApp();

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

export async function getDeletableProductIds(userId: string | undefined): Promise<string[]> {
  const promiseClient = await ensureClientInitialized();

  // 🔹 Validate userId before using it in the request
  if (!userId || typeof userId !== "string") {
    console.error("🚨 Invalid userId received:", userId);
    throw new Error("User ID is missing or invalid.");
  }

  console.log(`Fetching deletable product IDs for user ${userId}...`);

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

