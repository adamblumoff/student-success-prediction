import { describe, expect, it } from 'vitest';
import { createInstitutionSchema, parseFormData } from '@/lib/validation';

describe('parseFormData', () => {
  it('parses valid form data', () => {
    const form = new FormData();
    form.append('name', 'Test High');
    form.append('code', 'TEST-HIGH');
    form.append('type', 'K12');

    const result = parseFormData(createInstitutionSchema, form);
    expect(result).toEqual({
      name: 'Test High',
      code: 'TEST-HIGH',
      type: 'K12'
    });
  });

  it('throws on invalid data', () => {
    const form = new FormData();
    form.append('name', '');
    form.append('code', '');

    expect(() => parseFormData(createInstitutionSchema, form)).toThrow();
  });
});
