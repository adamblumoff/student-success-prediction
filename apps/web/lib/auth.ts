import { auth, currentUser } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { and, asc, eq } from 'drizzle-orm';
import { cookies } from 'next/headers';

export async function requireUserAndOrg() {
  const { userId, orgId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }
  if (!orgId) {
    throw new Error('Organization is required');
  }
  return { userId, orgId };
}

export async function ensureDistrict(orgId: string) {
  const [existing] = await db
    .select({ id: tables.districts.id })
    .from(tables.districts)
    .where(eq(tables.districts.externalId, orgId))
    .limit(1);

  if (existing) {
    return existing.id;
  }

  const [created] = await db
    .insert(tables.districts)
    .values({
      name: 'New District',
      externalId: orgId,
      timezone: 'UTC',
      active: true
    })
    .returning({ id: tables.districts.id });

  if (!created) {
    throw new Error('Failed to create district');
  }
  return created.id;
}

export async function ensureInstitutionForDistrict(districtId: number) {
  const [existingInstitution] = await db
    .select({ id: tables.institutions.id })
    .from(tables.institutions)
    .where(eq(tables.institutions.districtId, districtId))
    .orderBy(asc(tables.institutions.id))
    .limit(1);

  if (existingInstitution) {
    return existingInstitution.id;
  }

  const [createdInstitution] = await db
    .insert(tables.institutions)
    .values({
      districtId,
      name: 'Default School',
      code: `DEFAULT-${districtId}`,
      type: 'K12',
      timezone: 'UTC',
      active: true
    })
    .returning({ id: tables.institutions.id });

  if (!createdInstitution) {
    throw new Error('Failed to create default institution');
  }

  return createdInstitution.id;
}

async function resolveActiveInstitutionId(districtId: number) {
  const cookieStore = await cookies();
  const raw = cookieStore.get('activeInstitutionId')?.value;
  const parsed = raw ? Number(raw) : NaN;
  if (!Number.isFinite(parsed)) {
    return null;
  }

  const [institution] = await db
    .select({ id: tables.institutions.id })
    .from(tables.institutions)
    .where(
      and(eq(tables.institutions.id, parsed), eq(tables.institutions.districtId, districtId))
    )
    .limit(1);

  return institution?.id ?? null;
}

export async function ensureAppUser() {
  const { userId, orgId } = await requireUserAndOrg();

  const clerkUser = await currentUser();
  const email = clerkUser?.emailAddresses?.[0]?.emailAddress ?? `${userId}@clerk.local`;
  const firstName = clerkUser?.firstName ?? 'Educator';
  const lastName = clerkUser?.lastName ?? 'User';
  const role = (clerkUser?.publicMetadata?.role as string | undefined) ?? 'admin';

  const districtId = await ensureDistrict(orgId);
  const institutionId = await ensureInstitutionForDistrict(districtId);

  const existing = await db
    .select()
    .from(tables.users)
    .where(eq(tables.users.username, userId))
    .limit(1);

  if (existing.length > 0) {
    const user = existing[0];
    if (user.districtId !== districtId) {
      await db
        .update(tables.users)
        .set({
          districtId,
          email,
          firstName,
          lastName,
          role,
          updatedAt: new Date()
        })
        .where(eq(tables.users.id, user.id));
    }
    return existing[0];
  }

  const [created] = await db
    .insert(tables.users)
    .values({
      districtId,
      institutionId,
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

export async function requireTenantContext() {
  const { userId, orgId } = await requireUserAndOrg();
  const districtId = await ensureDistrict(orgId);
  const activeInstitutionId = await resolveActiveInstitutionId(districtId);
  const institutionId = activeInstitutionId ?? (await ensureInstitutionForDistrict(districtId));
  return { userId, orgId, districtId, institutionId };
}
