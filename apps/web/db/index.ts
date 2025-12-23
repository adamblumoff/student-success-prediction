import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import * as schema from './schema';

const connectionString =
  process.env.NODE_ENV === 'test'
    ? process.env.LOCAL_DATABASE_URL
    : process.env.DATABASE_URL;
if (!connectionString) {
  if (process.env.NODE_ENV === 'test') {
    throw new Error('LOCAL_DATABASE_URL is not set for tests');
  }
  throw new Error('DATABASE_URL is not set');
}

const globalForDb = globalThis as typeof globalThis & {
  __dbPool?: Pool;
};

const allowSelfSigned = process.env.PG_SSL_ALLOW_SELF_SIGNED === 'true';

const pool =
  globalForDb.__dbPool ??
  new Pool({
    connectionString,
    ssl: connectionString.includes('sslmode=require')
      ? { rejectUnauthorized: !allowSelfSigned }
      : undefined
  });

if (process.env.NODE_ENV !== 'production') {
  globalForDb.__dbPool = pool;
}

export const db = drizzle(pool, { schema });
export * as tables from './schema';
