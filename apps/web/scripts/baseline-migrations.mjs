import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import dotenv from 'dotenv';
import pg from 'pg';

const { Client } = pg;

dotenv.config({ path: path.resolve(process.cwd(), '.env') });

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  console.error('DATABASE_URL is not set. Add it to apps/web/.env');
  process.exit(1);
}

const migrationsDir = path.resolve(process.cwd(), 'db', 'migrations');
const journalPath = path.join(migrationsDir, 'meta', '_journal.json');

if (!fs.existsSync(journalPath)) {
  console.error('Missing migrations meta/_journal.json. Run `bun run db:generate` first.');
  process.exit(1);
}

const journal = JSON.parse(fs.readFileSync(journalPath, 'utf8'));
const entries = Array.isArray(journal.entries) ? journal.entries : [];
if (entries.length === 0) {
  console.error('No migration entries found in meta/_journal.json.');
  process.exit(1);
}

const latest = entries[entries.length - 1];
const migrationFile = path.join(migrationsDir, `${latest.tag}.sql`);
if (!fs.existsSync(migrationFile)) {
  console.error(`Missing migration file: ${migrationFile}`);
  process.exit(1);
}

const sql = fs.readFileSync(migrationFile, 'utf8');
const hash = crypto.createHash('sha256').update(sql).digest('hex');
const createdAt = Number(latest.when);
if (!Number.isFinite(createdAt)) {
  console.error('Invalid migration timestamp in meta/_journal.json');
  process.exit(1);
}

const client = new Client({ connectionString: databaseUrl });

try {
  await client.connect();
  await client.query('CREATE SCHEMA IF NOT EXISTS drizzle');
  await client.query(`
    CREATE TABLE IF NOT EXISTS drizzle.__drizzle_migrations (
      id SERIAL PRIMARY KEY,
      hash text NOT NULL,
      created_at bigint
    );
  `);

  const { rows } = await client.query(
    'SELECT id, hash, created_at FROM drizzle.__drizzle_migrations ORDER BY created_at DESC LIMIT 1'
  );
  if (rows.length > 0 && Number(rows[0].created_at) >= createdAt) {
    console.log('Migrations are already baselined.');
    process.exit(0);
  }

  await client.query(
    'INSERT INTO drizzle.__drizzle_migrations (hash, created_at) VALUES ($1, $2)',
    [hash, createdAt]
  );

  console.log(`Baselined migration ${latest.tag}.`);
} finally {
  await client.end();
}
