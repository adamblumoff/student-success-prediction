export type MLPrediction = {
  student_id: string | number;
  name?: string;
  grade_level?: number;
  current_gpa?: number;
  attendance_rate?: number;
  risk_probability?: number;
  risk_category?: string;
  risk_level?: string;
  confidence?: number;
  model_type?: string;
  recommendations?: string[];
  [key: string]: unknown;
};

export type MLResponse = {
  predictions: MLPrediction[];
  model_info?: Record<string, unknown>;
};

export async function runMLPrediction(file: File): Promise<MLResponse> {
  if (process.env.SKIP_ML === 'true') {
    return {
      predictions: [],
      model_info: {
        model_version: 'skipped',
        reason: 'SKIP_ML enabled'
      }
    };
  }

  const serviceUrl = process.env.ML_SERVICE_URL;
  if (!serviceUrl) {
    throw new Error('ML_SERVICE_URL is not configured');
  }
  const apiKey = process.env.ML_SERVICE_API_KEY;

  const form = new FormData();
  form.append('file', file, file.name || 'gradebook.csv');

  const response = await fetch(`${serviceUrl.replace(/\/$/, '')}/predict`, {
    method: 'POST',
    body: form,
    headers: apiKey ? { 'x-ml-api-key': apiKey } : undefined
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`ML service error: ${message}`);
  }

  return response.json();
}
