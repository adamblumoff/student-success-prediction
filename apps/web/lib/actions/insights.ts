'use server';

import { emitRealtimeEvent } from '@/lib/realtime';
import { revalidatePath } from 'next/cache';
import { generateQuickInsight } from '@/lib/server/insights';
import { requireTenantContext } from '@/lib/auth';

export async function getQuickInsight(studentDbId: number) {
  const { districtId, institutionId } = await requireTenantContext();
  const result = await generateQuickInsight(studentDbId);
  revalidatePath('/insights');
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/insights'],
    districtId,
    institutionId
  });
  return result;
}
