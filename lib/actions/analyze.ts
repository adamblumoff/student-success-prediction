'use server';

import crypto from 'crypto';
import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { runMLPrediction, type MLPrediction } from '@/lib/ml-client';
import { getInstitutionId } from '@/lib/auth';
import { eq } from 'drizzle-orm';

function normalizeRiskCategory(input: string | undefined, riskScore: number) {
  if (input) return input;
  if (riskScore >= 0.7) return 'High Risk';
  if (riskScore >= 0.3) return 'Moderate Risk';
  return 'Low Risk';
}

function normalizeRiskLevel(input: string | undefined, riskScore: number) {
  if (input) return input;
  if (riskScore >= 0.7) return 'danger';
  if (riskScore >= 0.3) return 'warning';
  return 'success';
}

export async function analyzeGradebook(formData: FormData) {
  const { userId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const file = formData.get('file');
  if (!file || !(file instanceof File)) {
    throw new Error('CSV file is required');
  }

  const { predictions, model_info } = await runMLPrediction(file);

  const institutionId = getInstitutionId();
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
      const riskCategory = normalizeRiskCategory(pred.risk_category as string | undefined, riskScore);
      const riskLevel = normalizeRiskLevel(pred.risk_level as string | undefined, riskScore);

      if (riskScore >= 0.7) summary.high += 1;
      else if (riskScore >= 0.3) summary.medium += 1;
      else summary.low += 1;

      const studentValues = {
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

      await tx.insert(tables.predictions).values({
        institutionId,
        studentId: student.id,
        riskScore,
        riskCategory,
        successProbability: 1 - riskScore,
        confidenceScore: Number(pred.confidence ?? Math.abs(riskScore - 0.5) * 2),
        modelVersion: String((model_info as { model_type?: string } | undefined)?.model_type ?? 'k12_ultra'),
        modelType: String(pred.model_type ?? 'ultra_advanced'),
        featuresUsed: JSON.stringify(pred),
        sessionId,
        dataSource: 'csv_upload',
        predictionDate: new Date()
      });

      storedPredictions.push({
        ...pred,
        risk_category: riskCategory,
        risk_level: riskLevel,
        student_db_id: student.id
      });
    }
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
