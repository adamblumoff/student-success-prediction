import { db, tables } from '@/db';

export async function seedTenant({
  externalId = 'test-org',
  userId = 'test-user'
} = {}) {
  const suffix = externalId.slice(-6);
  const code = `TEST-${suffix}`.toUpperCase();
  const [district] = await db
    .insert(tables.districts)
    .values({
      name: 'Test District',
      externalId,
      timezone: 'UTC',
      active: true
    })
    .returning();

  const [institution] = await db
    .insert(tables.institutions)
    .values({
      districtId: district.id,
      name: `Test High ${suffix}`,
      code,
      type: 'K12',
      timezone: 'UTC',
      active: true
    })
    .returning();

  const [user] = await db
    .insert(tables.users)
    .values({
      districtId: district.id,
      institutionId: institution.id,
      username: userId,
      email: `${userId}@example.com`,
      passwordHash: 'test',
      firstName: 'Test',
      lastName: 'User',
      role: 'admin',
      isActive: true,
      isVerified: true
    })
    .returning();

  return { district, institution, user };
}

export async function seedStudent({
  districtId,
  institutionId,
  studentId,
  name = 'Student One',
  gradeLevel = '10',
  riskScore = 0.82,
  riskCategory = 'High Risk'
}: {
  districtId: number;
  institutionId: number;
  studentId?: string;
  name?: string;
  gradeLevel?: string;
  riskScore?: number;
  riskCategory?: string;
}) {
  const resolvedStudentId =
    studentId ?? `student-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const [student] = await db
    .insert(tables.students)
    .values({
      districtId,
      institutionId,
      studentId: resolvedStudentId,
      name,
      gradeLevel,
      latestRiskScore: riskScore,
      latestRiskCategory: riskCategory,
      latestPredictionDate: new Date()
    })
    .returning();

  return student;
}

export async function seedPrediction({
  districtId,
  institutionId,
  studentDbId,
  riskScore = 0.82,
  riskCategory = 'High Risk'
}: {
  districtId: number;
  institutionId: number;
  studentDbId: number;
  riskScore?: number;
  riskCategory?: string;
}) {
  const [prediction] = await db
    .insert(tables.predictions)
    .values({
      districtId,
      institutionId,
      studentId: studentDbId,
      riskScore,
      riskCategory,
      successProbability: 1 - riskScore,
      confidenceScore: 0.9,
      modelVersion: 'v1',
      modelType: 'success_default',
      dataHash: 'hash',
      dataSource: 'test'
    })
    .returning();

  return prediction;
}

export async function seedIntervention({
  districtId,
  institutionId,
  studentDbId,
  predictionId
}: {
  districtId: number;
  institutionId: number;
  studentDbId: number;
  predictionId?: number;
}) {
  const [intervention] = await db
    .insert(tables.interventions)
    .values({
      districtId,
      institutionId,
      studentId: studentDbId,
      predictionId,
      interventionType: 'Check-in',
      title: 'Weekly check-in',
      status: 'planned'
    })
    .returning();

  return intervention;
}

export async function seedInsight({
  districtId,
  institutionId,
  studentDbId,
  studentId
}: {
  districtId: number;
  institutionId: number;
  studentDbId: number;
  studentId: string;
}) {
  const [insight] = await db
    .insert(tables.gptInsights)
    .values({
      districtId,
      institutionId,
      studentDatabaseId: studentDbId,
      studentId,
      riskLevel: 'High',
      dataHash: 'hash',
      rawResponse: 'raw',
      formattedHtml: '<ul><li>Test</li></ul>',
      gptModel: 'gpt-4o-mini',
      isCached: false
    })
    .returning();

  return insight;
}
