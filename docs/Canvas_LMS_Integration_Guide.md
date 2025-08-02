# Canvas LMS Integration Guide

## Overview

The Student Success Prediction system now includes full Canvas LMS integration, allowing educators to connect directly to their Canvas courses and generate real-time student risk predictions based on actual gradebook data.

## Features

### ✅ Complete Integration
- **Real-time data sync** from Canvas gradebooks
- **Automatic grade processing** and feature engineering
- **K-12 Ultra-Advanced predictions** (81.5% AUC)
- **Interactive web interface** with progress tracking
- **Secure token management** and error handling

### 🎨 Canvas API Capabilities
- Connect to any Canvas instance (school, district, organization)
- Fetch course lists with enrollment data
- Process assignments, grades, and submission data
- Calculate attendance patterns and engagement metrics
- Generate comprehensive student risk profiles

## Getting Started

### 1. Obtain Canvas API Token

**For Educators:**
1. Log in to your Canvas account
2. Go to **Account → Settings**
3. Scroll to **Approved Integrations**
4. Click **+ New Access Token**
5. Enter purpose: "Student Success Prediction"
6. Set expiry date (optional, recommended 90 days)
7. Click **Generate Token**
8. **Copy and save the token securely**

**Required Permissions:**
- Read course data
- Read student enrollments  
- Read assignment data
- Read submission data
- Read grade data

### 2. Connect to Canvas

1. **Start the MVP server:**
   ```bash
   python3 run_mvp.py
   ```

2. **Open web interface:**
   Navigate to http://localhost:8001

3. **Find Canvas LMS Integration section:**
   Scroll down to the Canvas integration area

4. **Enter credentials:**
   - **Canvas URL:** Your school's Canvas instance (e.g., `https://yourschool.instructure.com`)
   - **Access Token:** The token you generated above

5. **Test connection:**
   Click "🔗 Connect to Canvas" to verify credentials

### 3. Select and Analyze Course

1. **Choose course:**
   - Browse available courses
   - Select course with students you want to analyze
   - View course metadata (term, student count, etc.)

2. **Sync and analyze:**
   - Click "📊 Sync & Analyze Course"
   - Watch real-time progress updates
   - View comprehensive results

## API Endpoints

### Canvas Connection Test
```http
POST /api/lms/canvas/connect
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "base_url": "https://yourschool.instructure.com",
  "access_token": "your-canvas-token"
}
```

### Get Courses List
```http
POST /api/lms/canvas/courses
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "base_url": "https://yourschool.instructure.com",
  "access_token": "your-canvas-token"
}
```

### Sync Course Data
```http
POST /api/lms/canvas/sync
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "base_url": "https://yourschool.instructure.com",
  "access_token": "your-canvas-token",
  "course_id": "12345"
}
```

## Data Processing

### Canvas Data Extraction
The system automatically extracts and processes:

**Core Academic Data:**
- Assignment scores and completion rates
- Overall grade/GPA calculation
- Late submission patterns
- Missing assignment tracking

**Engagement Metrics:**
- Course activity levels
- Login patterns (when available)
- Submission timeliness
- Assignment quality indicators

**Derived Features (Generated Automatically):**
- Academic momentum and trends
- Risk factor accumulation
- Protective factor identification
- Grade-level appropriate expectations

### Grade Level Detection
The system intelligently estimates student grade levels from:
- Course names (e.g., "9th Grade English", "Algebra I")
- Course codes (e.g., "ENG9", "ALG1") 
- Default: Grade 7 (middle school) if no patterns found

## Results and Analysis

### Individual Student Predictions
Each student receives:
- **Risk Category:** Low Risk, Moderate Risk, High Risk
- **Risk Probability:** Numerical score (0.0-1.0)
- **Confidence Level:** Prediction certainty
- **Key Risk Factors:** Specific areas of concern
- **Actionable Recommendations:** Intervention suggestions

### Class-Level Summary
- Total students analyzed
- Risk distribution breakdown
- Class average GPA and attendance
- Data source confirmation (Canvas real-time)
- Sync timestamp for accountability

### Enhanced Recommendations
Grade-appropriate intervention suggestions:
- **Elementary (K-5):** Reading support, family engagement
- **Middle School (6-8):** Transition support, peer relationships
- **High School (9-12):** Credit recovery, graduation planning

## Security and Privacy

### Data Protection
- **Secure token storage:** Encrypted in production
- **API rate limiting:** Respects Canvas rate limits (3000/hour)
- **No persistent storage** of sensitive Canvas data
- **Session-based connections:** Tokens not stored long-term

### Compliance Considerations
- **FERPA Compliant:** No permanent student data storage
- **Local Processing:** All predictions generated locally
- **Audit Trail:** Database logs prediction sessions
- **Access Control:** API key authentication required

## Troubleshooting

### Common Issues

**❌ "Canvas connection failed"**
- Verify Canvas URL format: `https://yourschool.instructure.com`
- Check access token validity and permissions
- Ensure Canvas instance is accessible
- Confirm token hasn't expired

**❌ "No courses found"**
- Verify you have teacher/instructor role in Canvas courses
- Check that courses are active/available
- Ensure proper Canvas permissions for course access

**❌ "Rate limit exceeded"**
- Canvas allows 3000 API calls per hour
- Wait for rate limit reset (shows remaining calls in UI)
- For large courses, process in smaller batches

**❌ "Sync failed during processing"**
- Check Canvas course has gradebook data
- Verify students have assignment submissions
- Ensure course has active enrollments

### Support

**Error Codes:**
- `401`: Invalid Canvas credentials
- `403`: Insufficient Canvas permissions  
- `429`: Canvas rate limit exceeded
- `500`: Server processing error

**Debug Mode:**
Set `DEVELOPMENT_MODE=true` in environment for detailed logging.

## Advanced Usage

### Batch Processing
For districts with multiple courses:
1. Connect once to Canvas instance
2. Process courses individually for detailed analysis
3. Export results for district-level reporting
4. Schedule regular sync for ongoing monitoring

### Integration with SIS
While Canvas provides gradebook data, consider integrating with Student Information Systems for:
- Attendance data (more comprehensive than Canvas activity)
- Behavioral incident tracking
- Special population flags (IEP, ELL, 504 plans)
- Multi-year academic history

### Automation Possibilities
- **Scheduled Sync:** Automatic daily/weekly course analysis
- **Alert System:** Email notifications for new high-risk students
- **Dashboard Integration:** Real-time district dashboards
- **Parent Communication:** Automated progress reports

## Performance

### Processing Speed
- **Connection Test:** <2 seconds
- **Course List:** <5 seconds  
- **Single Course Sync:** 30-60 seconds (depending on size)
- **Predictions:** <100ms per student
- **Large Courses:** Up to 500 students supported

### Scalability
- **Concurrent Users:** Multiple teachers can connect simultaneously
- **Multiple Courses:** No limit on courses per teacher
- **District Scale:** Supports school district implementations
- **Database Storage:** PostgreSQL for production scalability

## Future Enhancements

### Planned Features
1. **Google Classroom Integration** - Additional LMS support
2. **Schoology Integration** - K-12 focused platform
3. **Automated Scheduling** - Regular sync automation
4. **Parent Portal** - Family-facing dashboards
5. **Intervention Tracking** - Follow-up on recommendations

### API Extensions
- Webhook support for real-time Canvas updates
- Bulk export for district reporting
- Integration with intervention management systems
- Advanced analytics and trend reporting

---

## Quick Start Summary

1. **Get Canvas token** → Account Settings → New Access Token
2. **Start server** → `python3 run_mvp.py`
3. **Open browser** → http://localhost:8001
4. **Connect Canvas** → Enter URL + token
5. **Select course** → Choose from course list  
6. **Analyze** → Click sync and view results

**Need Help?** Check the troubleshooting section or run the test suite: `python3 test_canvas_integration.py`

---

*The Canvas LMS integration leverages the ultra-advanced K-12 model (81.5% AUC) to provide accurate, real-time student success predictions directly from your Canvas gradebook data.*