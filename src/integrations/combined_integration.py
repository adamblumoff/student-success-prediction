#!/usr/bin/env python3
"""
Combined Canvas LMS + PowerSchool SIS Integration

This module provides the ultimate K-12 student success prediction by combining:
- Canvas LMS: Real-time gradebook, assignment completion, engagement
- PowerSchool SIS: Demographics, attendance, discipline, multi-year history

The result is the most comprehensive student risk analysis available.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import asyncio
from dataclasses import dataclass

from integrations.canvas_lms import CanvasLMSIntegration, CanvasConfig
from integrations.powerschool_sis import PowerSchoolSISIntegration, PowerSchoolConfig

logger = logging.getLogger(__name__)

@dataclass
class CombinedConfig:
    """Configuration for combined Canvas + PowerSchool integration"""
    # Canvas LMS
    canvas_url: str
    canvas_token: str
    
    # PowerSchool SIS
    powerschool_url: str
    powerschool_client_id: str
    powerschool_client_secret: str
    
    # Matching configuration
    student_id_field: str = 'sis_user_id'  # Field in Canvas that matches PowerSchool
    
class CombinedIntegration:
    """Ultimate integration combining Canvas LMS and PowerSchool SIS data"""
    
    def __init__(self, config: CombinedConfig):
        self.config = config
        
        # Initialize individual integrations
        canvas_config = CanvasConfig(
            base_url=config.canvas_url,
            access_token=config.canvas_token
        )
        self.canvas = CanvasLMSIntegration(canvas_config)
        
        ps_config = PowerSchoolConfig(
            base_url=config.powerschool_url,
            client_id=config.powerschool_client_id,
            client_secret=config.powerschool_client_secret
        )
        self.powerschool = PowerSchoolSISIntegration(ps_config)
        
        self.connection_status = {
            'canvas': False,
            'powerschool': False
        }
    
    def test_connections(self) -> Dict[str, Any]:
        """Test connections to both Canvas and PowerSchool"""
        try:
            # Test Canvas connection
            canvas_result = self.canvas.test_connection()
            self.connection_status['canvas'] = (canvas_result['status'] == 'success')
            
            # Test PowerSchool connection
            ps_result = self.powerschool.test_connection()
            self.connection_status['powerschool'] = (ps_result['status'] == 'success')
            
            return {
                'status': 'success' if all(self.connection_status.values()) else 'partial',
                'canvas': canvas_result,
                'powerschool': ps_result,
                'integration_ready': all(self.connection_status.values())
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'canvas': {'status': 'error'},
                'powerschool': {'status': 'error'},
                'integration_ready': False
            }
    
    def get_matching_courses_and_schools(self) -> Dict[str, Any]:
        """Get courses from Canvas and schools from PowerSchool for matching"""
        try:
            if not all(self.connection_status.values()):
                raise Exception("Both Canvas and PowerSchool must be connected")
            
            # Get Canvas courses
            canvas_courses = self.canvas.get_courses()
            
            # Get PowerSchool schools
            ps_schools = self.powerschool.get_schools()
            
            return {
                'status': 'success',
                'canvas_courses': canvas_courses,
                'powerschool_schools': ps_schools,
                'matching_suggestions': self._suggest_course_school_matches(canvas_courses, ps_schools)
            }
            
        except Exception as e:
            logger.error(f"Error getting courses and schools: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _suggest_course_school_matches(self, courses: List[Dict], schools: List[Dict]) -> List[Dict]:
        """Suggest matching between Canvas courses and PowerSchool schools"""
        suggestions = []
        
        for course in courses:
            course_name = course.get('name', '').lower()
            
            # Simple matching heuristics
            best_match = None
            best_score = 0
            
            for school in schools:
                school_name = school.get('name', '').lower()
                
                # Calculate simple similarity score
                score = 0
                common_words = set(course_name.split()) & set(school_name.split())
                score += len(common_words) * 2
                
                # Boost score for grade level matches
                if any(grade in course_name for grade in ['elementary', 'middle', 'high']):
                    if 'elementary' in course_name and school.get('high_grade', 12) <= 5:
                        score += 3
                    elif 'middle' in course_name and 6 <= school.get('low_grade', 0) <= 8:
                        score += 3
                    elif 'high' in course_name and school.get('low_grade', 0) >= 9:
                        score += 3
                
                if score > best_score:
                    best_score = score
                    best_match = school
            
            if best_match and best_score > 0:
                suggestions.append({
                    'canvas_course': course,
                    'powerschool_school': best_match,
                    'confidence': min(best_score / 5.0, 1.0)
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:5]  # Top 5 suggestions
    
    def sync_combined_data(self, canvas_course_id: str, powerschool_school_id: str, 
                          grade_levels: List[int] = None) -> Dict[str, Any]:
        """
        Perform combined sync of Canvas course and PowerSchool school data.
        This is the ultimate student success analysis combining both systems.
        """
        try:
            if not all(self.connection_status.values()):
                raise Exception("Both Canvas and PowerSchool must be connected")
            
            logger.info(f"Starting combined sync: Canvas course {canvas_course_id} + PowerSchool school {powerschool_school_id}")
            
            # Step 1: Get Canvas gradebook data
            canvas_gradebook = self.canvas.get_course_gradebook(canvas_course_id)
            logger.info(f"Retrieved {len(canvas_gradebook)} students from Canvas")
            
            # Step 2: Get PowerSchool comprehensive data
            ps_gradebook = self.powerschool.create_enhanced_gradebook(powerschool_school_id, grade_levels)
            logger.info(f"Retrieved {len(ps_gradebook)} students from PowerSchool")
            
            # Step 3: Match and merge student data
            combined_data = self._match_and_merge_student_data(canvas_gradebook, ps_gradebook)
            logger.info(f"Successfully matched {len(combined_data)} students")
            
            if combined_data.empty:
                return {
                    'status': 'warning',
                    'message': 'No matching students found between Canvas and PowerSchool',
                    'canvas_students': len(canvas_gradebook),
                    'powerschool_students': len(ps_gradebook),
                    'matched_students': 0,
                    'predictions': []
                }
            
            # Step 4: Generate enhanced predictions
            from models.k12_ultra_predictor import K12UltraPredictor
            predictor = K12UltraPredictor()
            predictions = predictor.predict_from_gradebook(combined_data)
            
            # Step 5: Enhance predictions with combined insights
            enhanced_predictions = self._enhance_predictions_with_combined_data(predictions, combined_data)
            
            # Step 6: Generate comprehensive analysis
            analysis_result = self._generate_combined_analysis(enhanced_predictions, combined_data)
            
            return {
                'status': 'success',
                'canvas_course_id': canvas_course_id,
                'powerschool_school_id': powerschool_school_id,
                'data_sources': ['canvas_lms', 'powerschool_sis'],
                'students_processed': len(combined_data),
                'canvas_students': len(canvas_gradebook),
                'powerschool_students': len(ps_gradebook),
                'matched_students': len(combined_data),
                'match_rate': len(combined_data) / max(len(canvas_gradebook), 1),
                'predictions': enhanced_predictions,
                'analysis': analysis_result,
                'sync_timestamp': datetime.now().isoformat(),
                'data_quality': self._assess_combined_data_quality(combined_data)
            }
            
        except Exception as e:
            logger.error(f"Combined sync error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'canvas_course_id': canvas_course_id,
                'powerschool_school_id': powerschool_school_id
            }
    
    def _match_and_merge_student_data(self, canvas_df: pd.DataFrame, ps_df: pd.DataFrame) -> pd.DataFrame:
        """Match Canvas and PowerSchool students and merge their data"""
        if canvas_df.empty or ps_df.empty:
            return pd.DataFrame()
        
        # Try multiple matching strategies
        matched_data = []
        
        # Strategy 1: Match by SIS User ID (if available in Canvas)
        if 'sis_user_id' in canvas_df.columns:
            canvas_with_sis = canvas_df[canvas_df['sis_user_id'].notna()]
            for _, canvas_student in canvas_with_sis.iterrows():
                sis_id = str(canvas_student['sis_user_id'])
                
                # Look for match in PowerSchool by various ID fields
                ps_match = ps_df[
                    (ps_df['student_id'] == sis_id) |
                    (ps_df['state_id'] == sis_id) |
                    (ps_df['local_id'] == sis_id)
                ]
                
                if not ps_match.empty:
                    combined_student = self._merge_student_records(canvas_student, ps_match.iloc[0])
                    matched_data.append(combined_student)
        
        # Strategy 2: Match by name (fuzzy matching)
        if len(matched_data) < len(canvas_df) * 0.5:  # If low match rate, try name matching
            matched_ids = set(d.get('student_id', '') for d in matched_data)
            
            for _, canvas_student in canvas_df.iterrows():
                if canvas_student.get('student_id', '') in matched_ids:
                    continue  # Already matched
                
                canvas_name = str(canvas_student.get('name', '')).lower().strip()
                if not canvas_name:
                    continue
                
                # Find best name match in PowerSchool
                best_match = None
                best_score = 0
                
                for _, ps_student in ps_df.iterrows():
                    ps_name = f"{ps_student.get('first_name', '')} {ps_student.get('last_name', '')}".lower().strip()
                    
                    # Simple name matching score
                    canvas_words = set(canvas_name.split())
                    ps_words = set(ps_name.split())
                    
                    if canvas_words and ps_words:
                        score = len(canvas_words & ps_words) / len(canvas_words | ps_words)
                        if score > best_score and score > 0.6:  # 60% similarity threshold
                            best_score = score
                            best_match = ps_student
                
                if best_match is not None:
                    combined_student = self._merge_student_records(canvas_student, best_match)
                    matched_data.append(combined_student)
        
        if not matched_data:
            return pd.DataFrame()
        
        return pd.DataFrame(matched_data)
    
    def _merge_student_records(self, canvas_record: pd.Series, ps_record: pd.Series) -> Dict:
        """Merge Canvas and PowerSchool student records into comprehensive profile"""
        # Start with PowerSchool data (more comprehensive)
        merged = ps_record.to_dict()
        
        # Overlay with Canvas data, prioritizing Canvas for academic performance
        canvas_dict = canvas_record.to_dict()
        
        # Academic data - prioritize Canvas (more current)
        merged.update({
            # Use Canvas gradebook data for current performance
            'current_grade_canvas': canvas_dict.get('current_grade', merged.get('current_gpa', 0) * 25),
            'assignment_completion_canvas': canvas_dict.get('assignment_completion', 0.8),
            'late_submission_rate_canvas': canvas_dict.get('late_submission_rate', 0.1),
            'missing_assignments_canvas': canvas_dict.get('missing_assignments', 0),
            'points_earned_canvas': canvas_dict.get('points_earned', 0),
            'points_possible_canvas': canvas_dict.get('points_possible', 0),
            
            # Canvas engagement data
            'canvas_course_id': canvas_dict.get('canvas_course_id'),
            'last_canvas_sync': canvas_dict.get('last_sync'),
            
            # Combined identifiers
            'canvas_student_id': canvas_dict.get('student_id'),
            'canvas_email': canvas_dict.get('email'),
            
            # Data source tracking
            'has_canvas_data': True,
            'has_powerschool_data': True,
            'data_sources': 'canvas_lms,powerschool_sis'
        })
        
        # Calculate combined GPA (Canvas current + PowerSchool historical)
        canvas_gpa = canvas_dict.get('current_gpa', 0)
        ps_gpa = merged.get('current_gpa', 0)
        
        if canvas_gpa > 0 and ps_gpa > 0:
            # Weight Canvas more heavily (more recent)
            merged['combined_gpa'] = (canvas_gpa * 0.7) + (ps_gpa * 0.3)
        else:
            merged['combined_gpa'] = max(canvas_gpa, ps_gpa)
        
        # Use combined GPA as current_gpa for predictions
        merged['current_gpa'] = merged['combined_gpa']
        
        return merged
    
    def _enhance_predictions_with_combined_data(self, predictions: List[Dict], combined_data: pd.DataFrame) -> List[Dict]:
        """Enhance predictions with insights from combined Canvas + PowerSchool data"""
        enhanced_predictions = []
        
        for prediction in predictions:
            student_id = prediction.get('student_id')
            student_data = combined_data[combined_data['student_id'] == student_id]
            
            if student_data.empty:
                enhanced_predictions.append(prediction)
                continue
            
            student_row = student_data.iloc[0]
            
            # Add combined data insights
            prediction['combined_insights'] = {
                'data_completeness': self._calculate_data_completeness(student_row),
                'canvas_performance': self._analyze_canvas_performance(student_row),
                'powerschool_context': self._analyze_powerschool_context(student_row),
                'risk_factor_triangulation': self._triangulate_risk_factors(student_row),
                'intervention_priority': self._calculate_intervention_priority(student_row, prediction)
            }
            
            # Enhanced risk factors from multiple sources
            combined_risk_factors = []
            combined_protective_factors = []
            
            # Canvas-specific risk factors
            if student_row.get('late_submission_rate_canvas', 0) > 0.3:
                combined_risk_factors.append("High late submission rate (Canvas)")
            
            if student_row.get('assignment_completion_canvas', 1.0) < 0.7:
                combined_risk_factors.append("Low assignment completion (Canvas)")
            
            # PowerSchool-specific risk factors
            if student_row.get('attendance_rate', 1.0) < 0.85:
                combined_risk_factors.append("Chronic absenteeism (PowerSchool official)")
            
            if student_row.get('discipline_incidents', 0) > 2:
                combined_risk_factors.append("Multiple discipline incidents (PowerSchool)")
            
            if student_row.get('economic_disadvantaged', False):
                combined_risk_factors.append("Economic disadvantage (PowerSchool)")
            
            # Combined protective factors
            if student_row.get('assignment_completion_canvas', 0) > 0.9:
                combined_protective_factors.append("High assignment completion (Canvas)")
            
            if student_row.get('iep_status', False):
                combined_protective_factors.append("IEP support services (PowerSchool)")
            
            if student_row.get('attendance_rate', 0) > 0.95:
                combined_protective_factors.append("Excellent attendance (PowerSchool)")
            
            prediction['combined_risk_factors'] = combined_risk_factors
            prediction['combined_protective_factors'] = combined_protective_factors
            
            # Data source attribution
            prediction['data_sources'] = {
                'canvas_lms': True,
                'powerschool_sis': True,
                'integration_type': 'combined'
            }
            
            enhanced_predictions.append(prediction)
        
        return enhanced_predictions
    
    def _calculate_data_completeness(self, student_row: pd.Series) -> Dict[str, Any]:
        """Calculate how complete the combined data is for this student"""
        canvas_fields = ['current_grade_canvas', 'assignment_completion_canvas', 'points_earned_canvas']
        ps_fields = ['attendance_rate', 'discipline_incidents', 'economic_disadvantaged', 'current_gpa']
        
        canvas_completeness = sum(1 for field in canvas_fields if pd.notna(student_row.get(field))) / len(canvas_fields)
        ps_completeness = sum(1 for field in ps_fields if pd.notna(student_row.get(field))) / len(ps_fields)
        
        return {
            'canvas_completeness': canvas_completeness,
            'powerschool_completeness': ps_completeness,
            'overall_completeness': (canvas_completeness + ps_completeness) / 2,
            'has_both_sources': canvas_completeness > 0 and ps_completeness > 0
        }
    
    def _analyze_canvas_performance(self, student_row: pd.Series) -> Dict[str, Any]:
        """Analyze Canvas-specific performance metrics"""
        return {
            'assignment_completion': student_row.get('assignment_completion_canvas', 0),
            'late_submission_rate': student_row.get('late_submission_rate_canvas', 0),
            'missing_assignments': student_row.get('missing_assignments_canvas', 0),
            'current_grade': student_row.get('current_grade_canvas', 0),
            'engagement_level': 'high' if student_row.get('assignment_completion_canvas', 0) > 0.9 else 
                              'medium' if student_row.get('assignment_completion_canvas', 0) > 0.7 else 'low'
        }
    
    def _analyze_powerschool_context(self, student_row: pd.Series) -> Dict[str, Any]:
        """Analyze PowerSchool-specific context"""
        return {
            'attendance_rate': student_row.get('attendance_rate', 0),
            'discipline_incidents': student_row.get('discipline_incidents', 0),
            'economic_disadvantaged': student_row.get('economic_disadvantaged', False),
            'special_programs': {
                'iep': student_row.get('iep_status', False),
                'ell': student_row.get('ell_status', False),
                'section_504': student_row.get('section_504', False)
            },
            'academic_history': {
                'cumulative_gpa': student_row.get('cumulative_gpa', 0),
                'credits_earned': student_row.get('credits_earned', 0),
                'credits_attempted': student_row.get('credits_attempted', 0)
            }
        }
    
    def _triangulate_risk_factors(self, student_row: pd.Series) -> Dict[str, Any]:
        """Triangulate risk factors across both systems"""
        # Academic risk triangulation
        canvas_grade = student_row.get('current_grade_canvas', 0) / 25.0  # Convert to GPA scale
        ps_gpa = student_row.get('current_gpa', 0)
        
        academic_consistency = abs(canvas_grade - ps_gpa) if canvas_grade > 0 and ps_gpa > 0 else 0
        
        # Engagement risk triangulation
        canvas_engagement = student_row.get('assignment_completion_canvas', 0)
        ps_attendance = student_row.get('attendance_rate', 0)
        
        engagement_alignment = abs(canvas_engagement - ps_attendance) if canvas_engagement > 0 and ps_attendance > 0 else 0
        
        return {
            'academic_consistency': academic_consistency,
            'engagement_alignment': engagement_alignment,
            'data_contradictions': academic_consistency > 0.5 or engagement_alignment > 0.3,
            'risk_confirmation': (canvas_grade < 2.0 and ps_gpa < 2.0) or (canvas_engagement < 0.7 and ps_attendance < 0.85)
        }
    
    def _calculate_intervention_priority(self, student_row: pd.Series, prediction: Dict) -> str:
        """Calculate intervention priority based on combined data"""
        risk_prob = prediction.get('risk_probability', 0)
        
        # High priority factors
        high_priority_factors = [
            student_row.get('attendance_rate', 1.0) < 0.8,  # Chronic absenteeism
            student_row.get('discipline_incidents', 0) > 3,  # Multiple incidents
            student_row.get('assignment_completion_canvas', 1.0) < 0.6,  # Very low completion
            student_row.get('suspensions', 0) > 0  # Any suspensions
        ]
        
        if risk_prob > 0.7 and sum(high_priority_factors) >= 2:
            return 'critical'
        elif risk_prob > 0.5 and sum(high_priority_factors) >= 1:
            return 'high'
        elif risk_prob > 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_combined_analysis(self, predictions: List[Dict], combined_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive analysis of combined data"""
        if not predictions:
            return {}
        
        analysis = {
            'data_source_analysis': {
                'canvas_coverage': sum(1 for _, row in combined_data.iterrows() if row.get('has_canvas_data', False)),
                'powerschool_coverage': sum(1 for _, row in combined_data.iterrows() if row.get('has_powerschool_data', False)),
                'complete_profiles': sum(1 for _, row in combined_data.iterrows() 
                                       if row.get('has_canvas_data', False) and row.get('has_powerschool_data', False))
            },
            
            'risk_analysis': {
                'critical_priority': sum(1 for p in predictions if p.get('combined_insights', {}).get('intervention_priority') == 'critical'),
                'high_priority': sum(1 for p in predictions if p.get('combined_insights', {}).get('intervention_priority') == 'high'),
                'medium_priority': sum(1 for p in predictions if p.get('combined_insights', {}).get('intervention_priority') == 'medium'),
                'low_priority': sum(1 for p in predictions if p.get('combined_insights', {}).get('intervention_priority') == 'low')
            },
            
            'data_quality_insights': {
                'avg_data_completeness': np.mean([p.get('combined_insights', {}).get('data_completeness', {}).get('overall_completeness', 0) for p in predictions]),
                'students_with_contradictions': sum(1 for p in predictions 
                                                  if p.get('combined_insights', {}).get('risk_factor_triangulation', {}).get('data_contradictions', False))
            }
        }
        
        return analysis
    
    def _assess_combined_data_quality(self, combined_data: pd.DataFrame) -> Dict[str, Any]:
        """Assess the quality of combined Canvas + PowerSchool data"""
        if combined_data.empty:
            return {}
        
        return {
            'total_students': len(combined_data),
            'canvas_data_available': sum(1 for _, row in combined_data.iterrows() if row.get('has_canvas_data', False)),
            'powerschool_data_available': sum(1 for _, row in combined_data.iterrows() if row.get('has_powerschool_data', False)),
            'attendance_data': combined_data['attendance_rate'].notna().sum(),
            'discipline_data': combined_data['discipline_incidents'].notna().sum(),
            'demographics_data': combined_data['economic_disadvantaged'].notna().sum(),
            'special_programs_data': sum(1 for _, row in combined_data.iterrows() 
                                       if any([row.get('iep_status', False), row.get('ell_status', False), row.get('section_504', False)])),
            'canvas_engagement_data': combined_data['assignment_completion_canvas'].notna().sum(),
            'data_completeness_score': combined_data.notna().sum().sum() / (len(combined_data) * len(combined_data.columns))
        }

def create_combined_integration(canvas_url: str, canvas_token: str,
                              powerschool_url: str, powerschool_client_id: str, 
                              powerschool_client_secret: str) -> CombinedIntegration:
    """Factory function to create combined Canvas + PowerSchool integration"""
    config = CombinedConfig(
        canvas_url=canvas_url,
        canvas_token=canvas_token,
        powerschool_url=powerschool_url,
        powerschool_client_id=powerschool_client_id,
        powerschool_client_secret=powerschool_client_secret
    )
    return CombinedIntegration(config)

# Example usage
def main():
    """Test combined integration functionality"""
    print("🚀 Testing Combined Canvas + PowerSchool Integration")
    print("=" * 60)
    
    # This would normally come from environment variables or UI
    canvas_url = "https://school.instructure.com"
    canvas_token = "canvas_access_token"
    ps_url = "https://district.powerschool.com"
    ps_client_id = "powerschool_client_id"
    ps_client_secret = "powerschool_client_secret"
    
    try:
        combined = create_combined_integration(
            canvas_url, canvas_token,
            ps_url, ps_client_id, ps_client_secret
        )
        
        # Test connections
        connection_test = combined.test_connections()
        print(f"Connection test: {connection_test['status']}")
        
        if connection_test['integration_ready']:
            print("✅ Both Canvas and PowerSchool connected successfully!")
            print("🎯 Ready for ultimate student success prediction")
            
            # Get matching suggestions
            matches = combined.get_matching_courses_and_schools()
            if matches['status'] == 'success' and matches['matching_suggestions']:
                print(f"📋 Found {len(matches['matching_suggestions'])} course-school matches")
                
                # Example combined sync
                suggestion = matches['matching_suggestions'][0]
                canvas_course_id = suggestion['canvas_course']['id']
                ps_school_id = suggestion['powerschool_school']['id']
                
                print(f"🔄 Testing combined sync...")
                sync_result = combined.sync_combined_data(canvas_course_id, ps_school_id)
                
                if sync_result['status'] == 'success':
                    print(f"✅ Combined analysis complete!")
                    print(f"   📊 {sync_result['students_processed']} students analyzed")
                    print(f"   📈 Match rate: {sync_result['match_rate']:.1%}")
                    print(f"   🎯 Priority interventions: {sync_result['analysis']['risk_analysis']['critical_priority']} critical")
        else:
            print("⚠️ Partial connection - check credentials")
    
    except Exception as e:
        print(f"❌ Combined integration test failed: {e}")

if __name__ == "__main__":
    main()