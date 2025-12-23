import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { afterAll, beforeAll, beforeEach, vi } from 'vitest';
import { closeDatabase, migrateDatabase, resetDatabase } from './db';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const envPath = path.resolve(process.cwd(), '.env');
dotenv.config({ path: envPath });

const env = process.env as Record<string, string | undefined>;
env.NODE_ENV = 'test';
env.SKIP_ML = 'true';
env.OPENAI_API_KEY = env.OPENAI_API_KEY ?? 'test';
env.OPENAI_MODEL = env.OPENAI_MODEL ?? 'gpt-4o-mini';

vi.mock('@clerk/nextjs/server', () => ({
  auth: vi.fn(async () => ({
    userId: process.env.TEST_USER_ID ?? 'test-user',
    orgId: process.env.TEST_ORG_ID ?? 'test-org'
  })),
  currentUser: vi.fn(async () => ({
    emailAddresses: [
      { emailAddress: `${process.env.TEST_USER_ID ?? 'test-user'}@example.com` }
    ],
    firstName: 'Test',
    lastName: 'User',
    publicMetadata: { role: 'admin' }
  })),
  clerkMiddleware: vi.fn(),
  createRouteMatcher: vi.fn(() => () => false)
}));

vi.mock('next/headers', () => ({
  cookies: () => ({
    get: () => undefined
  })
}));

vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
  revalidateTag: vi.fn(),
  unstable_cache: (fn: () => Promise<unknown>) => fn
}));

vi.mock('@/lib/realtime', () => ({
  emitRealtimeEvent: vi.fn()
}));

beforeAll(async () => {
  await migrateDatabase();
});

beforeEach(async () => {
  await resetDatabase();
});

afterAll(async () => {
  await closeDatabase();
});
