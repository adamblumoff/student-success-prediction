import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { eq } from 'drizzle-orm';
import { cache } from 'react';

const loadTenantSummaryCached = cache(async () => {
  const { districtId, institutionId } = await requireTenantContext();

  const [district] = await db
    .select({
      id: tables.districts.id,
      name: tables.districts.name
    })
    .from(tables.districts)
    .where(eq(tables.districts.id, districtId))
    .limit(1);

  const [institution] = await db
    .select({ id: tables.institutions.id, name: tables.institutions.name })
    .from(tables.institutions)
    .where(eq(tables.institutions.id, institutionId))
    .limit(1);

  const institutions = await db
    .select({
      id: tables.institutions.id,
      name: tables.institutions.name,
      code: tables.institutions.code,
      type: tables.institutions.type,
      active: tables.institutions.active
    })
    .from(tables.institutions)
    .where(eq(tables.institutions.districtId, districtId))
    .orderBy(tables.institutions.id);

  return { district, institution, institutions };
});

export async function loadTenantSummary() {
  return loadTenantSummaryCached();
}
