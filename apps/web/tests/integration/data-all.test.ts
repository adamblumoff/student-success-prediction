import { describe, expect, it } from 'vitest';
import { NextRequest } from 'next/server';
import { GET } from '@/app/api/data/all/route';
import { seedInsight, seedIntervention, seedStudent, seedTenant } from '../fixtures';

const createRequest = (query: string) =>
  new NextRequest(`http://localhost/api/data/all?${query}`);

describe('GET /api/data/all', () => {
  it('respects include flags', async () => {
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
    await seedIntervention({
      districtId: district.id,
      institutionId: institution.id,
      studentDbId: student.id
    });
    await seedInsight({
      districtId: district.id,
      institutionId: institution.id,
      studentDbId: student.id,
      studentId: student.studentId
    });

    const response = await GET(
      createRequest('includeStudents=false&includeInsights=false&includeInterventions=false')
    );
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.students).toHaveLength(0);
    expect(body.insights).toHaveLength(0);
    expect(body.interventions).toHaveLength(0);
  });
});
