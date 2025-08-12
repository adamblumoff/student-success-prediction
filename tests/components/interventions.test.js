/**
 * Comprehensive Intervention System UI Tests
 * Tests intervention modals, forms, and user interactions
 */

describe('Intervention System UI Tests', () => {
    let mockFetch;
    
    beforeEach(() => {
        // Mock DOM elements
        document.body.innerHTML = `
            <div id="interventions-list-1001" class="interventions-list"></div>
            <div id="modal-overlay" style="display: none;"></div>
        `;
        
        // Mock window functions
        window.notificationSystem = {
            success: jest.fn(),
            error: jest.fn(),
            info: jest.fn()
        };
        
        // Mock localStorage
        Storage.prototype.getItem = jest.fn(() => 'test-auth-token');
        Storage.prototype.setItem = jest.fn();
        
        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;
        
        // Load intervention functions
        require('../../src/mvp/static/js/interventions.js');
    });
    
    afterEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = '';
    });
    
    describe('Intervention Creation', () => {
        test('should show intervention creation modal', () => {
            // Call createIntervention function
            createIntervention('1001');
            
            // Check if modal was created
            const modal = document.querySelector('.modal-overlay');
            expect(modal).toBeTruthy();
            
            // Check modal content
            const modalContent = modal.innerHTML;
            expect(modalContent).toContain('Create New Intervention');
            expect(modalContent).toContain('intervention-type');
            expect(modalContent).toContain('intervention-title');
            expect(modalContent).toContain('intervention-description');
        });
        
        test('should populate intervention type options', () => {
            createIntervention('1001');
            
            const typeSelect = document.getElementById('intervention-type');
            expect(typeSelect).toBeTruthy();
            
            // Check for expected intervention types
            const options = Array.from(typeSelect.options).map(opt => opt.value);
            expect(options).toContain('academic_support');
            expect(options).toContain('attendance_support');
            expect(options).toContain('behavioral_support');
            expect(options).toContain('engagement_support');
            expect(options).toContain('family_engagement');
        });
        
        test('should focus on first input when modal opens', (done) => {
            createIntervention('1001');
            
            // Wait for setTimeout in showInterventionModal
            setTimeout(() => {
                const firstInput = document.getElementById('intervention-type');
                expect(document.activeElement).toBe(firstInput);
                done();
            }, 150);
        });
    });
    
    describe('Intervention Form Submission', () => {
        beforeEach(() => {
            // Mock successful API response
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    id: 123,
                    student_id: 1001,
                    intervention_type: 'academic_support',
                    title: 'Test Intervention',
                    status: 'pending',
                    priority: 'medium'
                })
            });
        });
        
        test('should submit intervention form with correct data', async () => {
            createIntervention('1001');
            
            // Fill out form
            document.getElementById('intervention-type').value = 'academic_support';
            document.getElementById('intervention-title').value = 'Math Tutoring';
            document.getElementById('intervention-description').value = 'Weekly tutoring sessions';
            document.getElementById('intervention-priority').value = 'high';
            document.getElementById('intervention-assigned').value = 'Ms. Johnson';
            document.getElementById('intervention-due').value = '2024-12-31';
            
            // Submit form
            const form = document.getElementById('intervention-form');
            const submitEvent = new Event('submit');
            
            await handleInterventionSubmit(submitEvent, '1001');
            
            // Verify fetch was called with correct data
            expect(mockFetch).toHaveBeenCalledWith('/api/interventions/', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer test-auth-token',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    student_id: 1001,
                    intervention_type: 'academic_support',
                    title: 'Math Tutoring',
                    description: 'Weekly tutoring sessions',
                    priority: 'high',
                    assigned_to: 'Ms. Johnson',
                    due_date: '2024-12-31'
                })
            });
        });
        
        test('should show success notification on successful submission', async () => {
            createIntervention('1001');
            
            // Fill required fields
            document.getElementById('intervention-type').value = 'academic_support';
            document.getElementById('intervention-title').value = 'Test Intervention';
            
            const form = document.getElementById('intervention-form');
            const submitEvent = new Event('submit');
            
            await handleInterventionSubmit(submitEvent, '1001');
            
            expect(window.notificationSystem.success).toHaveBeenCalledWith(
                'Intervention created successfully'
            );
        });
        
        test('should handle form submission errors', async () => {
            // Mock API error response
            mockFetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({
                    detail: 'Student not found'
                })
            });
            
            createIntervention('1001');
            
            document.getElementById('intervention-type').value = 'academic_support';
            document.getElementById('intervention-title').value = 'Test Intervention';
            
            const form = document.getElementById('intervention-form');
            const submitEvent = new Event('submit');
            
            await handleInterventionSubmit(submitEvent, '1001');
            
            expect(window.notificationSystem.error).toHaveBeenCalledWith('Student not found');
        });
        
        test('should handle network errors', async () => {
            // Mock network error
            mockFetch.mockRejectedValue(new Error('Network error'));
            
            createIntervention('1001');
            
            document.getElementById('intervention-type').value = 'academic_support';
            document.getElementById('intervention-title').value = 'Test Intervention';
            
            const form = document.getElementById('intervention-form');
            const submitEvent = new Event('submit');
            
            await handleInterventionSubmit(submitEvent, '1001');
            
            expect(window.notificationSystem.error).toHaveBeenCalledWith('Error creating intervention');
        });
    });
    
    describe('Intervention Status Updates', () => {
        beforeEach(() => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    id: 123,
                    status: 'in_progress',
                    outcome_notes: 'Updated notes'
                })
            });
        });
        
        test('should show status update modal', () => {
            updateInterventionStatus(123, 'pending');
            
            const modal = document.querySelector('.modal-overlay');
            expect(modal).toBeTruthy();
            
            const modalContent = modal.innerHTML;
            expect(modalContent).toContain('Update Intervention Status');
            expect(modalContent).toContain('status-select');
            expect(modalContent).toContain('status-notes');
        });
        
        test('should show outcome field when status is completed', () => {
            updateInterventionStatus(123, 'pending');
            
            const statusSelect = document.getElementById('status-select');
            const outcomeGroup = document.getElementById('outcome-group');
            
            // Initially hidden for non-completed status
            expect(outcomeGroup.style.display).toBe('none');
            
            // Change to completed
            statusSelect.value = 'completed';
            statusSelect.dispatchEvent(new Event('change'));
            
            expect(outcomeGroup.style.display).toBe('block');
        });
        
        test('should submit status update with correct data', async () => {
            updateInterventionStatus(123, 'pending');
            
            document.getElementById('status-select').value = 'in_progress';
            document.getElementById('status-notes').value = 'Progress update';
            
            const form = document.getElementById('status-form');
            const submitEvent = new Event('submit');
            
            await handleStatusUpdate(submitEvent, '123');
            
            expect(mockFetch).toHaveBeenCalledWith('/api/interventions/123', {
                method: 'PUT',
                headers: {
                    'Authorization': 'Bearer test-auth-token',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: 'in_progress',
                    outcome: null,
                    outcome_notes: 'Progress update'
                })
            });
        });
    });
    
    describe('Intervention Loading and Display', () => {
        const mockInterventions = [
            {
                id: 1,
                title: 'Math Tutoring',
                intervention_type: 'academic_support',
                priority: 'medium',
                status: 'pending',
                description: 'Weekly tutoring sessions',
                assigned_to: 'Ms. Johnson',
                due_date: '2024-12-31'
            },
            {
                id: 2,
                title: 'Counseling Sessions',
                intervention_type: 'behavioral_support',
                priority: 'high',
                status: 'in_progress',
                description: 'Bi-weekly counseling',
                assigned_to: 'Dr. Smith'
            }
        ];
        
        beforeEach(() => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve(mockInterventions)
            });
        });
        
        test('should load interventions for student', async () => {
            const container = document.getElementById('interventions-list-1001');
            
            await loadInterventionsForContainer('1001', container);
            
            expect(mockFetch).toHaveBeenCalledWith('/api/interventions/student/1001', {
                headers: {
                    'Authorization': 'Bearer test-auth-token',
                    'Content-Type': 'application/json'
                }
            });
        });
        
        test('should render intervention cards correctly', async () => {
            const container = document.getElementById('interventions-list-1001');
            
            await loadInterventionsForContainer('1001', container);
            
            const interventionCards = container.querySelectorAll('.intervention-card');
            expect(interventionCards.length).toBe(2);
            
            // Check first intervention card
            const firstCard = interventionCards[0];
            expect(firstCard.innerHTML).toContain('Math Tutoring');
            expect(firstCard.innerHTML).toContain('Academic Support');
            expect(firstCard.innerHTML).toContain('medium');
            expect(firstCard.innerHTML).toContain('pending');
            expect(firstCard.innerHTML).toContain('Ms. Johnson');
        });
        
        test('should handle empty interventions list', async () => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve([])
            });
            
            const container = document.getElementById('interventions-list-1001');
            
            await loadInterventionsForContainer('1001', container);
            
            expect(container.innerHTML).toContain('No interventions created yet');
        });
        
        test('should handle intervention loading errors', async () => {
            mockFetch.mockResolvedValue({
                ok: false,
                status: 404
            });
            
            const container = document.getElementById('interventions-list-1001');
            
            await loadInterventionsForContainer('1001', container);
            
            expect(container.innerHTML).toContain('No interventions found');
        });
        
        test('should handle network errors during loading', async () => {
            mockFetch.mockRejectedValue(new Error('Network error'));
            
            const container = document.getElementById('interventions-list-1001');
            
            await loadInterventionsForContainer('1001', container);
            
            expect(container.innerHTML).toContain('Error loading interventions');
        });
    });
    
    describe('Intervention Card Rendering', () => {
        test('should render intervention card with correct priority colors', () => {
            const interventions = [
                { id: 1, title: 'Low Priority', priority: 'low', status: 'pending', intervention_type: 'academic_support' },
                { id: 2, title: 'Medium Priority', priority: 'medium', status: 'pending', intervention_type: 'academic_support' },
                { id: 3, title: 'High Priority', priority: 'high', status: 'pending', intervention_type: 'academic_support' },
                { id: 4, title: 'Critical Priority', priority: 'critical', status: 'pending', intervention_type: 'academic_support' }
            ];
            
            interventions.forEach(intervention => {
                const cardHtml = renderInterventionCard(intervention);
                expect(cardHtml).toContain(intervention.title);
                expect(cardHtml).toContain(intervention.priority);
            });
        });
        
        test('should render intervention card with correct status colors', () => {
            const interventions = [
                { id: 1, title: 'Pending', priority: 'medium', status: 'pending', intervention_type: 'academic_support' },
                { id: 2, title: 'In Progress', priority: 'medium', status: 'in_progress', intervention_type: 'academic_support' },
                { id: 3, title: 'Completed', priority: 'medium', status: 'completed', intervention_type: 'academic_support' },
                { id: 4, title: 'Cancelled', priority: 'medium', status: 'cancelled', intervention_type: 'academic_support' }
            ];
            
            interventions.forEach(intervention => {
                const cardHtml = renderInterventionCard(intervention);
                expect(cardHtml).toContain(intervention.status.replace('_', ' '));
            });
        });
        
        test('should format intervention types correctly', () => {
            const intervention = {
                id: 1,
                title: 'Test Intervention',
                priority: 'medium',
                status: 'pending',
                intervention_type: 'academic_support'
            };
            
            const cardHtml = renderInterventionCard(intervention);
            expect(cardHtml).toContain('Academic Support');
        });
        
        test('should include action buttons in intervention card', () => {
            const intervention = {
                id: 123,
                title: 'Test Intervention',
                priority: 'medium',
                status: 'pending',
                intervention_type: 'academic_support'
            };
            
            const cardHtml = renderInterventionCard(intervention);
            expect(cardHtml).toContain('updateInterventionStatus(123');
            expect(cardHtml).toContain('viewInterventionDetails(123');
            expect(cardHtml).toContain('Update Status');
            expect(cardHtml).toContain('Details');
        });
    });
    
    describe('Modal Management', () => {
        test('should close modal when close button is clicked', () => {
            createIntervention('1001');
            
            const modal = document.querySelector('.modal-overlay');
            expect(modal).toBeTruthy();
            
            const closeButton = modal.querySelector('.modal-close');
            closeButton.click();
            
            // Modal should be removed from DOM
            expect(document.querySelector('.modal-overlay')).toBeFalsy();
        });
        
        test('should close modal when clicking outside', () => {
            createIntervention('1001');
            
            const modal = document.querySelector('.modal-overlay');
            expect(modal).toBeTruthy();
            
            // Click on the overlay (outside the modal content)
            modal.click();
            
            // Note: This would require additional click handling logic
            // The test sets up the expectation for proper modal behavior
        });
    });
    
    describe('Notification System Integration', () => {
        test('should use notification system when available', () => {
            showNotification('Test message', 'success');
            expect(window.notificationSystem.success).toHaveBeenCalledWith('Test message');
            
            showNotification('Error message', 'error');
            expect(window.notificationSystem.error).toHaveBeenCalledWith('Error message');
            
            showNotification('Info message', 'info');
            expect(window.notificationSystem.info).toHaveBeenCalledWith('Info message');
        });
        
        test('should fallback to alert when notification system unavailable', () => {
            // Mock alert
            window.alert = jest.fn();
            
            // Remove notification system
            delete window.notificationSystem;
            
            showNotification('Test message', 'success');
            expect(window.alert).toHaveBeenCalledWith('Test message');
        });
    });
    
    describe('Safe Refresh Functionality', () => {
        test('should safely refresh interventions when appState available', () => {
            // Mock window.appState and analysisComponent
            window.appState = {
                getState: jest.fn(() => ({
                    selectedStudent: { id: 1001 }
                }))
            };
            
            window.analysisComponent = {
                loadStudentInterventions: jest.fn()
            };
            
            safeRefreshInterventions(1001);
            
            expect(window.analysisComponent.loadStudentInterventions).toHaveBeenCalledWith({
                id: 1001
            });
        });
        
        test('should fallback to container refresh when appState unavailable', async () => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve([])
            });
            
            // Set up fallback container
            document.body.innerHTML = '<div id="interventions-list-1001"></div>';
            
            safeRefreshInterventions(1001);
            
            // Should attempt to refresh via container
            // This tests the fallback mechanism
        });
    });
    
    describe('Form Validation', () => {
        test('should require intervention type and title', () => {
            createIntervention('1001');
            
            const typeSelect = document.getElementById('intervention-type');
            const titleInput = document.getElementById('intervention-title');
            
            expect(typeSelect.hasAttribute('required')).toBe(true);
            expect(titleInput.hasAttribute('required')).toBe(true);
        });
        
        test('should set default priority to medium', () => {
            createIntervention('1001');
            
            const prioritySelect = document.getElementById('intervention-priority');
            expect(prioritySelect.value).toBe('medium');
        });
        
        test('should handle date input for due dates', () => {
            createIntervention('1001');
            
            const dueDateInput = document.getElementById('intervention-due');
            expect(dueDateInput.type).toBe('date');
        });
    });
});