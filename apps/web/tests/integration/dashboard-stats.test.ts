import { describe, expect, it } from 'vitest';
import { NextRequest } from 'next/server';
import { GET } from '@/app/api/dashboard/stats/route';
import { seedIntervention, seedPrediction, seedStudent, seedTenant } from '../fixtures';

const createRequest = (institutionId: number) =>
  new NextRequest(`http://localhost/api/dashboard/stats?institutionId=${institutionId}`);

describe('GET /api/dashboard/stats', () => {
  it('returns aggregated stats for a tenant', async () => {
    const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const orgId = `test-org-${suffix}`;
    const userId = `test-user-${suffix}`;
    process.env.TEST_ORG_ID = orgId;
    process.env.TEST_USER_ID = userId;
    const { district, institution } = await seedTenant({ externalId: orgId, userId });
    const student = await seedStudent({
      districtId: district.id,
      institutionId: institution.id
    });
    const prediction = await seedPrediction({
      districtId: district.id,
      institutionId: institution.id,
      studentDbId: student.id
    });
    await seedIntervention({
      districtId: district.id,
      institutionId: institution.id,
      studentDbId: student.id,
      predictionId: prediction.id
    });

    const response = await GET(createRequest(institution.id));
    expect(response.status).toBe(200);

    const body = await response.json();
    expect(body.totalStudents).toBe(1);
    expect(body.totalPredictions).toBe(1);
    expect(body.totalInterventions).toBe(1);
    expect(body.riskDistribution.high).toBeGreaterThan(0);
    expect(body.topRiskStudents.length).toBeGreaterThan(0);
  });
});
