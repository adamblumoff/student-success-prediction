'use server';

import crypto from 'crypto';
import { db, tables } from '@/db';
import { runMLPrediction, type MLPrediction } from '@/lib/ml-client';
import { requireTenantContext } from '@/lib/auth';
import { and, eq, isNull, lte, or } from 'drizzle-orm';
import { revalidatePath, revalidateTag } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';
import { calculateRiskCategory, calculateRiskLevel } from '@/lib/risk';

export async function analyzeGradebook(formData: FormData) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const file = formData.get('file');
  if (!file || !(file instanceof File)) {
    throw new Error('CSV file is required');
  }
  const maxBytes = Number(process.env.MAX_CSV_BYTES ?? 5 * 1024 * 1024);
  if (Number.isFinite(maxBytes) && file.size > maxBytes) {
    throw new Error('CSV file is too large');
  }

  const { predictions, model_info } = await runMLPrediction(file);

  const sessionId = crypto.randomUUID();
  const summary = {
    total: predictions.length,
    high: 0,
    medium: 0,
    low: 0
  };

  const storedPredictions: Array<MLPrediction & { student_db_id?: number }> = [];

  await db.transaction(async (tx) => {
    for (const pred of predictions) {
      const studentExternalId = String(
        pred.student_id ?? pred.id ?? (pred as { ID?: string }).ID ?? `student-${crypto.randomUUID()}`
      );
      const riskScore = Number(pred.risk_probability ?? 0.5);
      const riskCategory = calculateRiskCategory(riskScore);
      const riskLevel = calculateRiskLevel(riskScore);

      if (riskScore >= 0.7) summary.high += 1;
      else if (riskScore >= 0.3) summary.medium += 1;
      else summary.low += 1;

      const studentValues = {
        districtId,
        institutionId,
        studentId: studentExternalId,
        name: (pred.name as string | undefined) ?? null,
        gradeLevel: pred.grade_level ? String(pred.grade_level) : null,
        currentGpa: pred.current_gpa ? Number(pred.current_gpa) : null,
        attendanceRate: pred.attendance_rate ? Number(pred.attendance_rate) : null,
        previousGpa: pred.previous_gpa ? Number(pred.previous_gpa) : null,
        studyHoursWeek: pred.study_hours_week ? Number(pred.study_hours_week) : null,
        extracurricular: pred.extracurricular ? Number(pred.extracurricular) : null,
        parentEducation: pred.parent_education ? Number(pred.parent_education) : null,
        socioeconomicStatus: pred.socioeconomic_status ? Number(pred.socioeconomic_status) : null
      };

      const [student] = await tx
        .insert(tables.students)
        .values(studentValues)
        .onConflictDoUpdate({
          target: [tables.students.institutionId, tables.students.studentId],
          set: {
            ...studentValues,
            lastActivity: new Date()
          }
        })
        .returning({ id: tables.students.id });

      const modelVersion = String(
        (model_info as { model_type?: string; model_version?: string } | undefined)?.model_version ??
          (model_info as { model_type?: string } | undefined)?.model_type ??
          'success_models'
      );
      const modelType = String(pred.model_type ?? 'success_default');
      const dataHash = String((pred as { input_hash?: string }).input_hash ?? '');

      let predictionId: number | undefined;
      if (dataHash) {
        const [existing] = await tx
          .select({ id: tables.predictions.id })
          .from(tables.predictions)
          .where(
            and(
              eq(tables.predictions.districtId, districtId),
              eq(tables.predictions.institutionId, institutionId),
              eq(tables.predictions.studentId, student.id),
              eq(tables.predictions.modelVersion, modelVersion),
              eq(tables.predictions.dataHash, dataHash)
            )
          );
        if (existing) predictionId = existing.id;
      }

      if (!predictionId) {
        const predictionDate = new Date();
        const [inserted] = await tx
          .insert(tables.predictions)
          .values({
            districtId,
            institutionId,
            studentId: student.id,
            riskScore,
            riskCategory,
            successProbability: 1 - riskScore,
            confidenceScore: Number(pred.confidence ?? Math.abs(riskScore - 0.5) * 2),
            modelVersion,
            modelType,
            dataHash: dataHash || null,
            featuresUsed: JSON.stringify(pred),
            sessionId,
            dataSource: 'csv_upload',
            predictionDate
          })
          .returning({ id: tables.predictions.id });
        predictionId = inserted?.id;

        await tx
          .update(tables.students)
          .set({
            latestRiskScore: riskScore,
            latestRiskCategory: riskCategory,
            latestConfidenceScore: Number(pred.confidence ?? Math.abs(riskScore - 0.5) * 2),
            latestPredictionDate: predictionDate
          })
          .where(
            and(
              eq(tables.students.id, student.id),
              or(
                isNull(tables.students.latestPredictionDate),
                lte(tables.students.latestPredictionDate, predictionDate)
              )
            )
          );
      }

      storedPredictions.push({
        ...pred,
        risk_category: riskCategory,
        risk_level: riskLevel,
        student_db_id: student.id,
        prediction_id: predictionId
      });
    }
  });

  revalidatePath('/dashboard');
  revalidatePath('/students');
  revalidatePath('/insights');
  revalidatePath('/upload');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/dashboard', '/students', '/insights', '/upload'],
    districtId,
    institutionId
  });

  return {
    summary,
    sessionId,
    modelInfo: model_info ?? null,
    predictions: storedPredictions.slice(0, 150)
  };
}

export type AnalyzeState = {
  status: 'idle' | 'success' | 'error';
  error?: string;
  result?: Awaited<ReturnType<typeof analyzeGradebook>>;
};

export async function analyzeGradebookAction(
  _prevState: AnalyzeState,
  formData: FormData
): Promise<AnalyzeState> {
  try {
    const result = await analyzeGradebook(formData);
    return { status: 'success', result };
  } catch (error) {
    return {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unexpected error'
    };
  }
}
