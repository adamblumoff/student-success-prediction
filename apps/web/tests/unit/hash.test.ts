import { sha256 } from '@/lib/hash';
import { describe, expect, it } from 'vitest';

describe('sha256', () => {
  it('produces deterministic hashes', () => {
    const first = sha256('hello');
    const second = sha256('hello');
    const different = sha256('world');

    expect(first).toBe(second);
    expect(first).not.toBe(different);
    expect(first).toHaveLength(64);
  });
});
