'use server';

import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { eq, desc, and } from 'drizzle-orm';
import { emitRealtimeEvent } from '@/lib/realtime';
import { revalidatePath } from 'next/cache';
import { sha256 } from '@/lib/hash';
import { generateInsight } from '@/lib/gpt';
import { getInstitutionId } from '@/lib/auth';

export async function getQuickInsight(studentDbId: number) {
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();

  const [student] = await db
    .select()
    .from(tables.students)
    .where(and(eq(tables.students.id, studentDbId), eq(tables.students.institutionId, institutionId)))
    .limit(1);

  if (!student) {
    throw new Error('Student not found');
  }

  const [prediction] = await db
    .select()
    .from(tables.predictions)
    .where(eq(tables.predictions.studentId, studentDbId))
    .orderBy(desc(tables.predictions.predictionDate))
    .limit(1);

  const interventions = await db
    .select({ id: tables.interventions.id, status: tables.interventions.status })
    .from(tables.interventions)
    .where(eq(tables.interventions.studentId, studentDbId))
    .orderBy(desc(tables.interventions.createdAt))
    .limit(25);

  const normalizedInterventions = interventions
    .map((intervention) => ({
      id: intervention.id,
      status: intervention.status ?? 'planned'
    }))
    .sort((a, b) => a.id - b.id);

  const normalizedStudent = {
    id: student.id,
    studentId: student.studentId,
    gradeLevel: student.gradeLevel,
    currentGpa: student.currentGpa,
    attendanceRate: student.attendanceRate,
    enrollmentStatus: student.enrollmentStatus
  };

  const normalizedPrediction = prediction
    ? {
        id: prediction.id,
        riskCategory: prediction.riskCategory,
        riskScore: prediction.riskScore
      }
    : null;

  const dataHash = sha256(
    JSON.stringify({
      student: normalizedStudent,
      prediction: normalizedPrediction,
      interventions: normalizedInterventions
    })
  );

  const [cached] = await db
    .select()
    .from(tables.gptInsights)
    .where(
      and(
        eq(tables.gptInsights.institutionId, institutionId),
        eq(tables.gptInsights.studentDatabaseId, student.id),
        eq(tables.gptInsights.dataHash, dataHash)
      )
    )
    .limit(1);

  if (cached) {
    await db
      .update(tables.gptInsights)
      .set({
        cacheHits: (cached.cacheHits ?? 0) + 1,
        lastAccessed: new Date(),
        isCached: true
      })
      .where(eq(tables.gptInsights.id, cached.id));

    return {
      cached: true,
      formattedHtml: cached.formattedHtml,
      riskLevel: cached.riskLevel
    };
  }

  const insight = await generateInsight({
    student: {
      studentId: student.studentId,
      name: student.name,
      gradeLevel: student.gradeLevel,
      currentGpa: student.currentGpa,
      attendanceRate: student.attendanceRate
    },
    prediction: {
      riskCategory: prediction?.riskCategory ?? null,
      riskScore: prediction?.riskScore ?? null
    },
    interventions
  });

  const [saved] = await db
    .insert(tables.gptInsights)
    .values({
      institutionId,
      studentId: student.studentId,
      studentDatabaseId: student.id,
      riskLevel: prediction?.riskCategory ?? 'Unknown',
      dataHash,
      rawResponse: insight.rawResponse,
      formattedHtml: insight.formattedHtml,
      gptModel: insight.model,
      tokensUsed: insight.tokensUsed ?? null,
      generationTimeMs: null,
      sessionId: null,
      userId: null,
      isCached: false,
      cacheHits: 0
    })
    .returning();

  revalidatePath('/insights');
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/insights'] });

  return {
    cached: false,
    formattedHtml: saved.formattedHtml,
    riskLevel: saved.riskLevel
  };
}
