import { describe, expect, it } from 'vitest';
import { NextRequest } from 'next/server';
import { GET } from '@/app/api/insights/latest/route';
import { seedInsight, seedStudent, seedTenant } from '../fixtures';
import { db, tables } from '@/db';
import { eq } from 'drizzle-orm';

const createRequest = (institutionId: number) =>
  new NextRequest(`http://localhost/api/insights/latest?institutionId=${institutionId}`);

describe('GET /api/insights/latest', () => {
  it('returns latest insights for institution', async () => {
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

    await seedInsight({
      districtId: district.id,
      institutionId: institution.id,
      studentDbId: student.id,
      studentId: student.studentId
    });

    const response = await GET(createRequest(institution.id));
    expect(response.status).toBe(200);

    const body = await response.json();
    expect(body.insights).toHaveLength(1);
    expect(body.insights[0].studentDatabaseId).toBe(student.id);
    expect(typeof body.version).toBe('string');
  });

  it('updates version when insight changes', async () => {
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

    const insight = await seedInsight({
      districtId: district.id,
      institutionId: institution.id,
      studentDbId: student.id,
      studentId: student.studentId
    });

    const firstResponse = await GET(createRequest(institution.id));
    const firstBody = await firstResponse.json();

    await db
      .update(tables.gptInsights)
      .set({ formattedHtml: '<ul><li>Updated</li></ul>', updatedAt: new Date() })
      .where(eq(tables.gptInsights.id, insight.id));

    const secondResponse = await GET(createRequest(institution.id));
    const secondBody = await secondResponse.json();

    expect(firstBody.version).not.toBe(secondBody.version);
  });
});
