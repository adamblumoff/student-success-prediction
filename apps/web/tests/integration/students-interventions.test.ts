import { describe, expect, it } from 'vitest';
import { GET } from '@/app/api/students/[studentId]/interventions/route';
import { seedIntervention, seedStudent, seedTenant } from '../fixtures';

const createParams = (studentId: number) =>
  Promise.resolve({ studentId: String(studentId) });

describe('GET /api/students/:id/interventions', () => {
  it('returns student detail and interventions', async () => {
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

    const response = await GET(new Request('http://localhost'), {
      params: createParams(student.id)
    });

    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.student.id).toBe(student.id);
    expect(body.interventions.length).toBe(1);
  });
});
