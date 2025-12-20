import { auth, currentUser } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { eq } from 'drizzle-orm';

const DEFAULT_INSTITUTION_ID = Number(process.env.DEFAULT_INSTITUTION_ID || 1);

export async function ensureInstitution() {
  const existing = await db
    .select({ id: tables.institutions.id })
    .from(tables.institutions)
    .where(eq(tables.institutions.id, DEFAULT_INSTITUTION_ID))
    .limit(1);

  if (existing.length > 0) {
    return existing[0].id;
  }

  const [created] = await db
    .insert(tables.institutions)
    .values({
      id: DEFAULT_INSTITUTION_ID,
      name: 'Default District',
      code: `DIST-${DEFAULT_INSTITUTION_ID}`,
      type: 'K12',
      timezone: 'UTC',
      active: true
    })
    .returning({ id: tables.institutions.id });

  return created?.id ?? DEFAULT_INSTITUTION_ID;
}

export async function ensureAppUser() {
  const { userId } = await auth();
  if (!userId) return null;

  const clerkUser = await currentUser();
  const email = clerkUser?.emailAddresses?.[0]?.emailAddress ?? `${userId}@clerk.local`;
  const firstName = clerkUser?.firstName ?? 'Educator';
  const lastName = clerkUser?.lastName ?? 'User';
  const role = (clerkUser?.publicMetadata?.role as string | undefined) ?? 'educator';

  await ensureInstitution();

  const existing = await db
    .select()
    .from(tables.users)
    .where(eq(tables.users.username, userId))
    .limit(1);

  if (existing.length > 0) {
    return existing[0];
  }

  const [created] = await db
    .insert(tables.users)
    .values({
      institutionId: DEFAULT_INSTITUTION_ID,
      username: userId,
      email,
      passwordHash: `clerk:${userId}`,
      firstName,
      lastName,
      role,
      isActive: true,
      isVerified: true
    })
    .returning();

  return created ?? null;
}

export function getInstitutionId() {
  return DEFAULT_INSTITUTION_ID;
}
