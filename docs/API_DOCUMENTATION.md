# API Documentation

## Overview

The Student Success Prediction System provides a comprehensive REST API built with FastAPI, featuring modular routers for different functional areas. All endpoints require API key authentication.

## Authentication

All API endpoints require an API key in the request headers:

```http
Authorization: Bearer your-api-key
```

**Default Development Key**: `dev-key-change-me`
**Environment Variable**: `MVP_API_KEY`

## Base URLs

- **Development**: `http://localhost:8001`
- **Production**: Your deployed domain
- **Interactive Documentation**: `/docs` (Swagger UI)
- **Health Check**: `/health`

## API Routers

The API is organized into specialized routers:

### Core MVP Endpoints (`/api/mvp/*`)

#### Student Data Analysis
```http
POST /api/mvp/analyze
```
Upload and analyze student CSV data using K-12 specialized neural network model.

**Request Body**: 
- Form data with CSV file upload
- Supports Canvas LMS and generic CSV formats

**Response**:
```json
{
  "message": "Analysis completed",
  "total_students": 150,
  "high_risk": 12,
  "medium_risk": 28,
  "low_risk": 110,
  "analysis_time": "2.3s",
  "model_accuracy": "81.5%"
}
```

#### Sample Data
```http
GET /api/mvp/sample
```
Load demo student data for testing and demonstration.

**Response**: Array of student objects with complete feature set (31 features for ML model compatibility).

#### Analytics
```http
GET /api/mvp/stats
```
Get system analytics and usage statistics.

**Response**:
```json
{
  "total_students": 1250,
  "total_predictions": 1150,
  "total_interventions": 89,
  "risk_distribution": {
    "high": 125,
    "medium": 350,
    "low": 775
  },
  "intervention_success_rate": 73.2
}
```

### GPT-Enhanced Analysis (`/api/mvp/gpt-insights/*`)

#### Check Cached Insights
```http
POST /api/mvp/gpt-insights/check
```
Check if GPT insights exist in cache for a student.

**Request Body**:
```json
{
  "student_id": "1309",
  "institution_id": 1
}
```

**Response**:
```json
{
  "has_cached": true,
  "insight_id": 30,
  "cache_hits": 1,
  "last_accessed": "2025-08-29T16:24:04Z"
}
```

#### Generate GPT Insights
```http
POST /api/mvp/gpt-insights/generate
```
Generate new GPT analysis for a student using actual database data.

**Request Body**:
```json
{
  "student_id": "1309",
  "institution_id": 1,
  "bypass_cache": false
}
```

**Response**:
```json
{
  "success": true,
  "insight_id": 31,
  "formatted_html": "<div class='gpt-insight'>...</div>",
  "tokens_used": 1247,
  "generation_time_ms": 3456,
  "cached": false
}
```

### Intervention Management (`/api/interventions/*`)

#### Create Intervention
```http
POST /api/interventions
```
Create a new intervention for a student.

**Request Body**:
```json
{
  "student_id": 1309,
  "intervention_type": "academic_support",
  "title": "Math Tutoring Program",
  "description": "Weekly 1-on-1 math tutoring sessions",
  "priority": "medium",
  "assigned_to": "Ms. Johnson",
  "due_date": "2025-09-15"
}
```

**Response**:
```json
{
  "id": 45,
  "status": "pending",
  "created_at": "2025-08-29T16:30:00Z",
  "message": "Intervention created successfully"
}
```

#### Get Student Interventions
```http
GET /api/interventions/student/{student_id}
```
Retrieve all interventions for a specific student.

**Response**:
```json
[
  {
    "id": 45,
    "intervention_type": "academic_support",
    "title": "Math Tutoring Program",
    "status": "in_progress",
    "priority": "medium",
    "assigned_to": "Ms. Johnson",
    "created_at": "2025-08-29T16:30:00Z",
    "due_date": "2025-09-15",
    "progress_notes": "Student showing improvement"
  }
]
```

#### Update Intervention Status
```http
PUT /api/interventions/{intervention_id}/status
```
Update the status of an intervention.

**Request Body**:
```json
{
  "status": "completed",
  "outcome": "Successful - student improved from D to B average",
  "outcome_notes": "Consistent attendance, great progress"
}
```

### Integration Endpoints

#### Canvas LMS (`/api/lms/*`)
- Gradebook import and processing
- Assignment synchronization
- Grade passback functionality

#### PowerSchool SIS (`/api/sis/*`)
- Student information system integration
- Bulk student data import
- Attendance and grade synchronization

#### Google Classroom (`/api/google/*`)
- OAuth 2.0 authentication flow
- Assignment and grade integration
- Class roster management

## Data Models

### Student
```json
{
  "id": 1309,
  "student_id": "STU001309",
  "name": "Anonymous Student",
  "grade_level": 9,
  "current_gpa": 2.85,
  "attendance_rate": 0.87,
  "risk_score": 0.65,
  "risk_category": "Medium Risk",
  "created_at": "2025-08-27T19:30:00Z"
}
```

### Prediction
```json
{
  "id": 234,
  "student_id": 1309,
  "risk_score": 0.65,
  "risk_category": "Medium Risk",
  "success_probability": 0.35,
  "confidence": 0.82,
  "model_version": "k12_ultra_20250730",
  "created_at": "2025-08-27T19:30:00Z"
}
```

### Intervention
```json
{
  "id": 45,
  "student_id": 1309,
  "intervention_type": "academic_support",
  "title": "Math Tutoring Program",
  "description": "Weekly tutoring sessions",
  "status": "in_progress",
  "priority": "medium",
  "assigned_to": "Ms. Johnson",
  "due_date": "2025-09-15",
  "outcome": null,
  "created_at": "2025-08-29T16:30:00Z"
}
```

### GPT Insight
```json
{
  "id": 30,
  "student_id": "1309",
  "risk_level": "Medium Risk",
  "data_hash": "7ff50b9f",
  "formatted_html": "<div>Personalized recommendations...</div>",
  "gpt_model": "gpt-5-nano",
  "tokens_used": 1247,
  "is_cached": true,
  "cache_hits": 1,
  "created_at": "2025-08-27T19:38:38Z"
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Invalid or missing API key
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-08-29T16:30:00Z"
}
```

## Rate Limiting

- **Default**: 100 requests per minute per API key
- **GPT Endpoints**: 10 requests per minute (due to processing cost)
- **Headers**: Rate limit information included in response headers

## Caching

### GPT Insights Caching
- **Database-backed**: Cached insights stored in `gpt_insights` table
- **Cache Invalidation**: Automatic invalidation when student data changes
- **Performance**: Cache hits tracked for optimization
- **TTL**: No explicit TTL, invalidated by data changes

### Response Caching
- **Student Data**: 5-minute cache for frequently accessed students
- **Analytics**: 15-minute cache for dashboard statistics
- **Model Results**: 1-hour cache for prediction results

## Usage Examples

### Python Example
```python
import requests

# Configuration
API_KEY = "your-api-key"
BASE_URL = "http://localhost:8001"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Upload and analyze student data
with open('gradebook.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        f"{BASE_URL}/api/mvp/analyze",
        files=files,
        headers=headers
    )
    analysis = response.json()

# Generate GPT insights for a student
insight_request = {
    "student_id": "1309",
    "institution_id": 1
}
response = requests.post(
    f"{BASE_URL}/api/mvp/gpt-insights/generate",
    json=insight_request,
    headers=headers
)
insights = response.json()
```

### JavaScript Example
```javascript
const API_KEY = 'your-api-key';
const BASE_URL = 'http://localhost:8001';

// Check for cached GPT insights
async function checkGPTInsights(studentId, institutionId) {
  const response = await fetch(`${BASE_URL}/api/mvp/gpt-insights/check`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      student_id: studentId,
      institution_id: institutionId
    })
  });
  
  return await response.json();
}

// Create intervention
async function createIntervention(studentId, interventionData) {
  const response = await fetch(`${BASE_URL}/api/interventions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      student_id: studentId,
      ...interventionData
    })
  });
  
  return await response.json();
}
```

## Development and Testing

### Interactive Documentation
Visit `/docs` in your browser for interactive API documentation with Swagger UI.

### Health Check
```http
GET /health
```
Returns system health status including database connectivity and model availability.

### API Testing
The system includes comprehensive API tests:
- **Backend Tests**: `python -m pytest tests/api/`
- **Integration Tests**: `npm test`
- **Security Tests**: Tests for authentication and authorization

## Production Considerations

### Security
- Always use HTTPS in production
- Rotate API keys regularly
- Implement rate limiting based on your usage patterns
- Monitor for unusual API usage patterns

### Performance
- Consider implementing Redis for improved caching
- Use database connection pooling for high-traffic scenarios
- Monitor GPT API usage to manage costs
- Implement proper logging and monitoring

### Monitoring
- Track API response times
- Monitor error rates
- Set up alerts for system health
- Log all API interactions for audit purposes