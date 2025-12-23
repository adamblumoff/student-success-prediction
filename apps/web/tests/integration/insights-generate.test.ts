import { describe, expect, it, vi } from 'vitest';
import { NextRequest } from 'next/server';

vi.mock('@/lib/server/insights', () => ({
  generateQuickInsight: vi.fn(async () => ({
    cached: false,
    formattedHtml: '<ul><li>Test</li></ul>',
    riskLevel: 'High'
  }))
}));

import { POST } from '@/app/api/insights/generate/route';

describe('POST /api/insights/generate', () => {
  it('rejects missing studentId', async () => {
    const request = new NextRequest('http://localhost/api/insights/generate', {
      method: 'POST',
      body: JSON.stringify({}),
      headers: { 'content-type': 'application/json' }
    });

    const response = await POST(request);
    expect(response.status).toBe(400);
  });

  it('returns generated insight', async () => {
    const request = new NextRequest('http://localhost/api/insights/generate', {
      method: 'POST',
      body: JSON.stringify({ studentId: 123 }),
      headers: { 'content-type': 'application/json' }
    });

    const response = await POST(request);
    expect(response.status).toBe(200);

    const body = await response.json();
    expect(body.formattedHtml).toContain('<li>Test</li>');
  });
});
