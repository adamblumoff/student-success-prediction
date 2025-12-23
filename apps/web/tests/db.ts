import path from 'path';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import { migrate } from 'drizzle-orm/node-postgres/migrator';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const envPath = path.resolve(process.cwd(), '.env');
dotenv.config({ path: envPath });

const connectionString = process.env.LOCAL_DATABASE_URL;

if (!connectionString) {
  throw new Error('LOCAL_DATABASE_URL must be set for integration tests.');
}

const pool = new Pool({ connectionString });
const db = drizzle(pool);

let migrationsApplied = false;

export async function migrateDatabase() {
  if (migrationsApplied) return;
  const migrationsFolder = path.join(process.cwd(), 'db', 'migrations');
  await migrate(db, { migrationsFolder });
  migrationsApplied = true;
}

export async function resetDatabase() {
  const client = await pool.connect();
  try {
    const result = await client.query<{
      tablename: string;
    }>(
      `select tablename from pg_tables where schemaname = 'public'`
    );

    const tables = result.rows
      .map((row) => row.tablename)
      .filter((name) => name && name !== 'schema_migrations');

    if (tables.length === 0) return;

    const quoted = tables.map((name) => `"${name.replace(/"/g, '""')}"`).join(', ');
    await client.query(`truncate table ${quoted} restart identity cascade`);
  } finally {
    client.release();
  }
}

export async function closeDatabase() {
  await pool.end();
}
