'use server';

import { NextResponse, type NextRequest } from 'next/server';
import { revalidatePath } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';
import { generateQuickInsight } from '@/lib/server/insights';
import { requireTenantContext } from '@/lib/auth';

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  const studentId = typeof body?.studentId === 'number' ? body.studentId : null;

  if (!studentId) {
    return NextResponse.json({ error: 'Missing studentId' }, { status: 400 });
  }

  try {
    const { districtId, institutionId } = await requireTenantContext();
    const result = await generateQuickInsight(studentId);
    revalidatePath('/insights');
    emitRealtimeEvent({
      type: 'data:mutation',
      paths: ['/insights'],
      districtId,
      institutionId
    });
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to generate insight' },
      { status: 500 }
    );
  }
}
