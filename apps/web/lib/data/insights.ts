import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { desc, eq, inArray, and } from 'drizzle-orm';

export async function loadLatestInsights(studentIds: number[]) {
  const { userId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  if (studentIds.length === 0) {
    return [] as Array<{
      studentDatabaseId: number;
      formattedHtml: string;
      riskLevel: string;
      createdAt: Date | null;
    }>;
  }

  const institutionId = getInstitutionId();
  const rows = await db
    .select({
      studentDatabaseId: tables.gptInsights.studentDatabaseId,
      formattedHtml: tables.gptInsights.formattedHtml,
      riskLevel: tables.gptInsights.riskLevel,
      createdAt: tables.gptInsights.createdAt
    })
    .from(tables.gptInsights)
    .where(
      and(
        eq(tables.gptInsights.institutionId, institutionId),
        inArray(tables.gptInsights.studentDatabaseId, studentIds)
      )
    )
    .orderBy(desc(tables.gptInsights.createdAt));

  const latestByStudent = new Map<number, (typeof rows)[number]>();
  for (const row of rows) {
    const id = row.studentDatabaseId ?? 0;
    if (!id || latestByStudent.has(id)) continue;
    latestByStudent.set(id, row);
  }

  return Array.from(latestByStudent.values());
}
