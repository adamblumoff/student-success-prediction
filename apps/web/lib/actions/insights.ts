'use server';

import { emitRealtimeEvent } from '@/lib/realtime';
import { revalidatePath } from 'next/cache';
import { generateQuickInsight } from '@/lib/server/insights';

export async function getQuickInsight(studentDbId: number) {
  const result = await generateQuickInsight(studentDbId);
  revalidatePath('/insights');
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/insights'] });
  return result;
}
