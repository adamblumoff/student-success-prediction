import OpenAI from 'openai';

export type InsightInput = {
  student: {
    studentId: string;
    name?: string | null;
    gradeLevel?: string | number | null;
    currentGpa?: number | null;
    attendanceRate?: number | null;
  };
  prediction?: {
    riskCategory?: string | null;
    riskScore?: number | null;
  };
  interventions?: Array<{ title: string; status?: string | null }>;
};

export type InsightResult = {
  rawResponse: string;
  formattedHtml: string;
  tokensUsed?: number;
  model: string;
};

export async function generateInsight(input: InsightInput): Promise<InsightResult> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY is not configured');
  }

  const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';
  const client = new OpenAI({ apiKey });

  const context = {
    studentId: input.student.studentId,
    name: input.student.name ?? 'Student',
    gradeLevel: input.student.gradeLevel ?? 'N/A',
    currentGpa: input.student.currentGpa ?? 'N/A',
    attendanceRate: input.student.attendanceRate ?? 'N/A',
    riskCategory: input.prediction?.riskCategory ?? 'Unknown',
    riskScore: input.prediction?.riskScore ?? 'N/A',
    activeInterventions: input.interventions?.map((item) => item.title).slice(0, 5) ?? []
  };

  const systemPrompt =
    'You are an education success strategist. Provide three concise, actionable recommendations for educators. ' +
    'Avoid repeating existing interventions. Keep each recommendation under 20 words.';

  const userPrompt = `Student context:\n${JSON.stringify(context, null, 2)}\n\nReturn exactly 3 bullet recommendations.`;

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ]
  });

  const content = response.choices?.[0]?.message?.content?.trim() || 'No insights generated.';
  const lines = content
    .split(/\n+/)
    .map((line) => line.replace(/^[-*\d.\s]+/, '').trim())
    .filter(Boolean)
    .slice(0, 3);

  const escapeHtml = (value: string) =>
    value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

  const formattedHtml = `
    <ul>
      ${lines.map((line) => `<li>${escapeHtml(line)}</li>`).join('')}
    </ul>
  `.trim();

  return {
    rawResponse: content,
    formattedHtml,
    tokensUsed: response.usage?.total_tokens,
    model
  };
}
