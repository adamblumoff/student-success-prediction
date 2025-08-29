/**
 * K-12 Educational Dashboard Redesign Tests (TDD Implementation)
 * 
 * Based on comprehensive TDD agent analysis:
 * - Educational Appropriateness Agent: Grade-level content validation
 * - FERPA Security Audit Agent: Student data protection requirements  
 * - Test Coverage Quality Agent: K-12 specific testing patterns
 * - GPT AI Validation Agent: Emma Johnson format compliance
 * 
 * GREEN Phase: Testing actual K12Dashboard implementation
 */

// Import the actual K12Dashboard implementation
const K12Dashboard = require('../../src/mvp/static/js/components/k12-dashboard.js');

describe('K-12 Educational Dashboard Redesign', () => {
  let dashboard;
  let mockStudentData;
  let mockAuthenticatedUser;

  beforeEach(() => {
    // Mock K-12 student data with proper grade-level context
    mockStudentData = [
      {
        student_id: 'elem_001',
        grade_level: 3,
        risk_category: 'Needs Additional Support', // Educational terminology instead of "High Risk"
        reading_level: 2.8,
        interventions: ['Reading Support Program'],
        special_populations: { has_iep: true }, // Should be privacy-protected
        last_updated: '2025-01-15T10:30:00Z'
      },
      {
        student_id: 'middle_001', 
        grade_level: 7,
        risk_category: 'Monitor Progress',
        study_skills_rating: 2.3,
        interventions: ['Study Skills Workshop'],
        behavioral_concerns: ['Attendance'], 
        last_updated: '2025-01-15T10:30:00Z'
      },
      {
        student_id: 'high_001',
        grade_level: 11,
        risk_category: 'On Track',
        credits_earned: 18.5,
        college_readiness: true,
        interventions: [],
        last_updated: '2025-01-15T10:30:00Z'
      }
    ];

    mockAuthenticatedUser = {
      role: 'teacher',
      institution_id: 1,
      authorized_grades: [3, 4, 5], // Teacher should only see their grade levels
      name: 'Ms. Johnson'
    };
  });

  describe('Educational Appropriateness Requirements', () => {
    test('dashboard shows grade-appropriate terminology for elementary students', async () => {
      // RED: This test will fail - current dashboard uses "Risk Analysis" terminology
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData);
      await dashboard.render();

      const elementarySection = dashboard.element.querySelector('[data-grade-band="elementary"]');
      expect(elementarySection).toBeDefined();
      
      // Should use family-friendly language
      expect(elementarySection.textContent).toContain('Reading Progress');
      expect(elementarySection.textContent).toContain('Learning Support');
      expect(elementarySection.textContent).not.toContain('Risk Analysis');
      expect(elementarySection.textContent).not.toContain('Predictive Analytics');
    });

    test('dashboard adapts interface complexity for different grade levels', async () => {
      // Use authorized user for all grade levels for this test
      const allGradesUser = {
        ...mockAuthenticatedUser,
        authorized_grades: [3, 7, 11] // Can see all test students
      };
      
      dashboard = new K12Dashboard('#dashboard', allGradesUser, mockStudentData);
      await dashboard.render();

      const elementaryCard = document.querySelector('[data-student-grade="3"]');
      const highSchoolCard = document.querySelector('[data-student-grade="11"]');

      // Elementary should show simple visual indicators
      expect(elementaryCard).toBeDefined();
      expect(elementaryCard.querySelector('.simple-progress-bar')).toBeDefined();
      expect(elementaryCard.querySelector('.reading-level-display')).toBeDefined();

      // High school should show complex metrics
      expect(highSchoolCard).toBeDefined();
      expect(highSchoolCard.querySelector('.credit-tracking')).toBeDefined();
      expect(highSchoolCard.querySelector('.college-readiness-indicator')).toBeDefined();
    });

    test('intervention recommendations use school-appropriate language', async () => {
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData);
      await dashboard.render();
      
      const interventionCard = document.querySelector('[data-intervention-type="academic_support"]');
      
      expect(interventionCard).toBeDefined();
      expect(interventionCard.textContent).not.toContain('therapy');
      expect(interventionCard.textContent).not.toContain('clinical');
      expect(interventionCard.textContent).not.toContain('diagnosis');
      expect(interventionCard.textContent).toContain('Reading Support');
    });
  });

  describe('FERPA Compliance Requirements', () => {
    test('student PII is masked by default in dashboard display', async () => {
      // RED: This test will fail - current dashboard shows full student names
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData);
      await dashboard.render();

      const studentCards = document.querySelectorAll('.student-card');
      studentCards.forEach(card => {
        // Student names should be initials only or masked
        const nameElement = card.querySelector('.student-name');
        expect(nameElement.textContent).toMatch(/^[A-Z]\. [A-Z]\.$/); // "J. D." format
        expect(nameElement.textContent).not.toMatch(/^[A-Za-z]+ [A-Za-z]+$/); // Not "John Doe"
      });
    });

    test('special populations information is privacy-protected', async () => {
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData);
      await dashboard.render();
      
      const studentCard = document.querySelector('[data-student="elem_001"]');
      
      expect(studentCard).toBeDefined();
      // IEP status should not be directly visible in DOM
      expect(studentCard.innerHTML).not.toContain('has_iep');
      expect(studentCard.innerHTML).not.toContain('IEP');
      
      // Should have privacy-protected indicator only
      expect(studentCard.querySelector('.additional-support-indicator')).toBeDefined();
    });

    test('dashboard access is logged for FERPA audit trail', async () => {
      // RED: This test will fail - current dashboard lacks audit logging
      const mockAuditLogger = jest.fn();
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData, mockAuditLogger);
      
      await dashboard.render();
      await dashboard.viewStudentDetails('elem_001');

      expect(mockAuditLogger).toHaveBeenCalledWith({
        action: 'VIEW_STUDENT_DASHBOARD',
        user_id: mockAuthenticatedUser.name,
        student_id: 'elem_001',
        timestamp: expect.any(String),
        ferpa_compliant: true
      });
    });

    test('role-based access controls prevent unauthorized data viewing', async () => {
      // RED: This test will fail - current system may not enforce grade-level restrictions
      const unauthorizedUser = {
        role: 'teacher',
        institution_id: 1,
        authorized_grades: [9, 10, 11, 12] // High school teacher
      };

      dashboard = new K12Dashboard('#dashboard', unauthorizedUser, mockStudentData);
      await dashboard.render();

      // Should not see elementary student data
      const elementaryCard = document.querySelector('[data-student-grade="3"]');
      expect(elementaryCard).toBeNull();
      
      // Should see high school student data
      const highSchoolCard = document.querySelector('[data-student-grade="11"]');
      expect(highSchoolCard).toBeDefined();
    });
  });

  describe('GPT AI Emma Johnson Format Compliance', () => {
    test('dashboard GPT insights follow exact Emma Johnson format', async () => {
      // RED: This test will fail - current format validation is insufficient
      const mockGPTResponse = `1. **Reading Support Focus**
   - Schedule weekly reading intervention with certified reading specialist

2. **Family Engagement Strategy**
   - Send home weekly reading practice activities with progress tracking

3. **Progress Monitoring Plan**
   - Implement bi-weekly reading assessments to track improvement`;

      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData);
      const formattedInsight = dashboard.validateEmmaJohnsonFormat(mockGPTResponse);

      // Must have exactly 3 numbered recommendations
      const recommendationMatches = formattedInsight.match(/^\d\.\s\*\*.*\*\*$/gm);
      expect(recommendationMatches).toHaveLength(3);

      // Each recommendation must have exactly 1 bullet point
      const bulletMatches = formattedInsight.match(/^\s*-\s/gm);
      expect(bulletMatches).toHaveLength(3);

      // Must use educational terminology
      expect(formattedInsight).toContain('reading specialist');
      expect(formattedInsight.toLowerCase()).toContain('family engagement');
      expect(formattedInsight).not.toContain('therapy');
      expect(formattedInsight).not.toContain('clinical');
    });

    test('GPT integration protects student PII from external API calls', async () => {
      // RED: This test will fail - current system may not anonymize data
      const mockGPTService = jest.fn();
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData, null, mockGPTService);

      await dashboard.generateInsights('elem_001');

      // Verify no PII sent to GPT API
      const gptCallArgs = mockGPTService.mock.calls[0][0];
      expect(gptCallArgs.prompt).not.toContain('elem_001'); // No student ID
      expect(gptCallArgs.prompt).not.toContain('John Doe'); // No student name
      expect(gptCallArgs.studentData.student_id).toMatch(/^ANON_\d+$/); // Anonymized ID
    });
  });

  describe('Classroom Performance Requirements', () => {
    test('dashboard loads within 3 seconds for classroom use', async () => {
      // RED: This test will fail - current dashboard may be too slow for classroom
      const startTime = performance.now();
      
      dashboard = new K12Dashboard('#dashboard', mockAuthenticatedUser, mockStudentData);
      await dashboard.render();
      
      const loadTime = performance.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // 3 second requirement for classroom use
    });

    test('dashboard handles concurrent teacher access during conferences', async () => {
      // RED: This test will fail - current system not optimized for concurrent access
      const concurrentUsers = Array.from({ length: 10 }, (_, i) => ({
        ...mockAuthenticatedUser,
        name: `Teacher_${i}`,
        authorized_grades: [3, 4, 5]
      }));

      const dashboardPromises = concurrentUsers.map(user => {
        const userDashboard = new K12Dashboard('#dashboard', user, mockStudentData);
        return userDashboard.render();
      });

      const startTime = performance.now();
      await Promise.all(dashboardPromises);
      const totalTime = performance.now() - startTime;

      // All dashboards should load within 5 seconds even with concurrent access
      expect(totalTime).toBeLessThan(5000);
    });
  });

  // Add setup for DOM environment
  beforeAll(() => {
    // Ensure DOM environment is available
    if (typeof document === 'undefined') {
      const { JSDOM } = require('jsdom');
      const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
      global.document = dom.window.document;
      global.window = dom.window;
    }
  });

  afterEach(() => {
    // Clean up DOM after each test
    if (document.body) {
      document.body.innerHTML = '';
    }
  });
});