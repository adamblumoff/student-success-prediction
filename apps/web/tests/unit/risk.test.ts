import { calculateRiskCategory, calculateRiskLevel, RISK_THRESHOLDS } from '@/lib/risk';
import { describe, expect, it } from 'vitest';

describe('risk helpers', () => {
  it('classifies high risk correctly', () => {
    const score = RISK_THRESHOLDS.high;
    expect(calculateRiskCategory(score)).toBe('High Risk');
    expect(calculateRiskLevel(score)).toBe('danger');
  });

  it('classifies moderate risk correctly', () => {
    const score = RISK_THRESHOLDS.moderate + 0.01;
    expect(calculateRiskCategory(score)).toBe('Moderate Risk');
    expect(calculateRiskLevel(score)).toBe('warning');
  });

  it('classifies low risk correctly', () => {
    const score = 0.1;
    expect(calculateRiskCategory(score)).toBe('Low Risk');
    expect(calculateRiskLevel(score)).toBe('success');
  });
});
