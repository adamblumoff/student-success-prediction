/**
 * Main Entry Point for Student Success Predictor
 * Initializes the modular application
 */

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Initializing Modern Student Success App');
  const app = new StudentSuccessApp();
  window.modernApp = app;
  console.log('✅ Modern app initialized and attached to window.modernApp');
  
  // Initialize delete all students button
  initializeDeleteAllStudents();
});

// Delete All Students Functionality
function initializeDeleteAllStudents() {
  const deleteButton = document.getElementById('delete-all-students');
  
  if (deleteButton) {
    deleteButton.addEventListener('click', async (e) => {
      e.preventDefault();
      
      // Confirm deletion with user
      const confirmed = confirm(
        '⚠️ WARNING: This will permanently delete ALL students from the database!\n\n' +
        'This action cannot be undone. Are you absolutely sure you want to continue?'
      );
      
      if (!confirmed) {
        return;
      }
      
      // Double confirmation for safety
      const doubleConfirmed = confirm(
        '🚨 FINAL WARNING: You are about to delete ALL student data!\n\n' +
        'Click OK to proceed with permanent deletion, or Cancel to abort.'
      );
      
      if (!doubleConfirmed) {
        return;
      }
      
      try {
        // Disable button and show loading state
        deleteButton.disabled = true;
        deleteButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Deleting...</span>';
        
        // Make API call to delete all students
        const response = await fetch('/api/mvp/students/all', {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}`
          }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
          // Success - show results
          alert(`✅ Success!\n\n${result.message}\n\nDeleted:\n- ${result.deleted_count} students\n- ${result.predictions_deleted} predictions\n- ${result.interventions_deleted} interventions\n- ${result.gpt_insights_deleted} GPT insights`);
          
          // Refresh the current tab to show empty state
          if (window.modernApp && window.modernApp.components.dashboard) {
            window.modernApp.components.dashboard.refreshData();
          }
          
          // Clear any displayed student data
          const studentList = document.getElementById('student-list');
          if (studentList) {
            studentList.innerHTML = '<p class="no-students">No students found. Upload data to begin analysis.</p>';
          }
          
        } else {
          // Error from API
          throw new Error(result.detail || result.message || 'Unknown error occurred');
        }
        
      } catch (error) {
        console.error('Error deleting students:', error);
        alert(`❌ Error deleting students:\n\n${error.message}\n\nPlease try again or check the console for details.`);
      } finally {
        // Re-enable button
        deleteButton.disabled = false;
        deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i> <span>Delete All Students</span>';
      }
    });
    
    console.log('✅ Delete all students button initialized');
  }
}