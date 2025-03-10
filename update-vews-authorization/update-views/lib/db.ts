import 'server-only';

import { neon } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-http';
import {
  pgTable,
  text,
  numeric,
  integer,
  timestamp,
  pgEnum,
  serial
} from 'drizzle-orm/pg-core';
import { count, eq, ilike, inArray } from 'drizzle-orm';
import { createInsertSchema } from 'drizzle-zod';
import { setupApp, getDeletableProductIds } from 'app/(dashboard)/actions'; 

export const db = drizzle(neon(process.env.POSTGRES_URL!));

export const statusEnum = pgEnum('status', ['active', 'inactive', 'archived']);

export const products = pgTable('products', {
  id: serial('id').primaryKey(),
  imageUrl: text('image_url').notNull(),
  name: text('name').notNull(),
  status: statusEnum('status').notNull(),
  price: numeric('price', { precision: 10, scale: 2 }).notNull(),
  stock: integer('stock').notNull(),
  availableAt: timestamp('available_at').notNull()
});

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

export type SelectProduct = typeof products.$inferSelect;
export const insertProductSchema = createInsertSchema(products);

export async function getProducts(
  search: string,
  offset: number
): Promise<{
  products: SelectProduct[];
  newOffset: number | null;
  totalProducts: number;
}> {
  // Always search the full table, not per page
  if (search) {
    return {
      products: await db
        .select()
        .from(products)
        .where(ilike(products.name, `%${search}%`))
        .limit(1000),
      newOffset: null,
      totalProducts: 0
    };
  }

  if (offset === null) {
    return { products: [], newOffset: null, totalProducts: 0 };
  }

  let totalProducts = await db.select({ count: count() }).from(products);
  let moreProducts = await db.select().from(products).limit(5).offset(offset);
  let newOffset = moreProducts.length >= 5 ? offset + 5 : null;

  return {
    products: moreProducts,
    newOffset,
    totalProducts: totalProducts[0].count
  };
}

export async function deleteProductById(id: number) {
  await db.delete(products).where(eq(products.id, id));
}

/**
 * 🔹 Fetch only products the user is authorized to delete
 */
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

(async () => {
  await initiateAppSetup();
})();
