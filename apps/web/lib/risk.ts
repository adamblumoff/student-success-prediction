export const RISK_THRESHOLDS = {
  high: 0.7,
  moderate: 0.3
};

export function calculateRiskCategory(riskScore: number) {
  if (riskScore >= RISK_THRESHOLDS.high) return 'High Risk';
  if (riskScore >= RISK_THRESHOLDS.moderate) return 'Moderate Risk';
  return 'Low Risk';
}

export function calculateRiskLevel(riskScore: number) {
  if (riskScore >= RISK_THRESHOLDS.high) return 'danger';
  if (riskScore >= RISK_THRESHOLDS.moderate) return 'warning';
  return 'success';
}
