'use server';

import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { eq } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';
import {
  createInstitutionSchema,
  parseFormData,
  setActiveInstitutionSchema,
  updateInstitutionSchema,
  updateTenantSettingsSchema
} from '@/lib/validation';
import { cookies } from 'next/headers';

export async function updateTenantSettings(formData: FormData) {
  const { districtId } = await requireTenantContext();

  const parsed = parseFormData(updateTenantSettingsSchema, formData);

  await db
    .update(tables.districts)
    .set({ name: parsed.districtName, updatedAt: new Date() })
    .where(eq(tables.districts.id, districtId));

  revalidatePath('/settings');
  revalidatePath('/dashboard');
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/settings', '/dashboard'],
    districtId,
    institutionId: null
  });

  return;
}

export async function createInstitution(formData: FormData) {
  const { districtId } = await requireTenantContext();
  const parsed = parseFormData(createInstitutionSchema, formData);

  const [created] = await db
    .insert(tables.institutions)
    .values({
      districtId,
      name: parsed.name,
      code: parsed.code,
      type: parsed.type,
      timezone: 'UTC',
      active: true
    })
    .returning();

  revalidatePath('/settings');
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/settings'],
    districtId,
    institutionId: created?.id ?? null
  });

  return;
}

export async function updateInstitution(formData: FormData) {
  const { districtId } = await requireTenantContext();
  const parsed = parseFormData(updateInstitutionSchema, formData);

  const [existing] = await db
    .select({ id: tables.institutions.id, districtId: tables.institutions.districtId })
    .from(tables.institutions)
    .where(eq(tables.institutions.id, parsed.institutionId))
    .limit(1);

  if (!existing || existing.districtId !== districtId) {
    throw new Error('Institution not found');
  }

  const [updated] = await db
    .update(tables.institutions)
    .set({
      name: parsed.name,
      code: parsed.code,
      type: parsed.type,
      updatedAt: new Date()
    })
    .where(eq(tables.institutions.id, parsed.institutionId))
    .returning();

  revalidatePath('/settings');
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/settings'],
    districtId,
    institutionId: updated?.id ?? parsed.institutionId
  });

  return;
}

export async function setActiveInstitution(formData: FormData) {
  const { districtId } = await requireTenantContext();
  const parsed = parseFormData(setActiveInstitutionSchema, formData);

  const [institution] = await db
    .select({ id: tables.institutions.id, districtId: tables.institutions.districtId })
    .from(tables.institutions)
    .where(eq(tables.institutions.id, parsed.institutionId))
    .limit(1);

  if (!institution || institution.districtId !== districtId) {
    throw new Error('Institution not found');
  }

  const cookieStore = await cookies();
  cookieStore.set('activeInstitutionId', String(parsed.institutionId), {
    path: '/',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 365,
    httpOnly: false
  });

  revalidatePath('/', 'layout');
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/'],
    districtId,
    institutionId: parsed.institutionId
  });

  return { status: 'success' as const };
}
