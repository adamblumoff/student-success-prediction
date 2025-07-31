#!/usr/bin/env python3
"""
K-12 Intervention Recommendation System

Provides personalized, grade-appropriate intervention recommendations for K-12 students
based on their risk profile and specific needs assessment.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import K-12 explainable AI
from k12_explainable_ai import K12ExplainableAI

class K12InterventionSystem:
    """Comprehensive intervention recommendation system for K-12 students."""
    
    def __init__(self, models_dir: Optional[Path] = None):
        """Initialize the K-12 intervention system."""
        self.models_dir = models_dir or Path("results/models/k12")
        self.explainable_ai = K12ExplainableAI()
        
        # Load intervention templates and strategies
        self.intervention_strategies = self._load_intervention_strategies()
        
        # Grade band specific focus areas
        self.grade_band_priorities = {
            'elementary': {
                'primary_focus': ['reading_proficiency', 'attendance', 'behavior', 'family_engagement'],
                'interventions': ['reading_intervention', 'family_outreach', 'behavior_support', 'academic_tutoring'],
                'timeline': 'immediate'  # Elementary interventions need quick action
            },
            'middle': {
                'primary_focus': ['engagement_drop', 'peer_relationships', 'academic_transition', 'study_skills'],
                'interventions': ['engagement_activities', 'peer_mentoring', 'study_skills', 'counseling_support'],
                'timeline': 'short_term'  # Middle school interventions over semester
            },
            'high': {
                'primary_focus': ['graduation_requirements', 'credit_recovery', 'college_career_prep', 'attendance'],
                'interventions': ['credit_recovery', 'graduation_planning', 'career_counseling', 'intensive_tutoring'],
                'timeline': 'long_term'  # High school interventions across multiple years
            }
        }
        
        try:
            self.explainable_ai.load_latest_model()
            print("✅ K-12 Intervention System initialized with latest model")
        except FileNotFoundError:
            print("⚠️  No K-12 model found. Run train_k12_models.py first.")
    
    def _load_intervention_strategies(self) -> Dict:
        """Load comprehensive intervention strategies by category and grade level."""
        return {
            'academic_support': {
                'elementary': {
                    'reading_intervention': {
                        'name': 'Reading Intervention Program',
                        'description': 'Intensive small-group reading instruction targeting foundational skills',
                        'duration': '6-12 weeks',
                        'frequency': 'Daily 30-45 minutes',
                        'staff_required': 'Reading specialist or trained teacher',
                        'success_metrics': ['reading_level_improvement', 'fluency_gains', 'comprehension_scores'],
                        'cost_estimate': 'Low-Medium',
                        'evidence_base': 'High - extensive research support'
                    },
                    'math_support': {
                        'name': 'Math Facts and Concepts Support',
                        'description': 'Targeted instruction in essential math concepts and fact fluency',
                        'duration': '8-10 weeks',
                        'frequency': '3-4 times per week, 30 minutes',
                        'staff_required': 'Math teacher or instructional aide',
                        'success_metrics': ['math_fact_fluency', 'concept_mastery', 'problem_solving'],
                        'cost_estimate': 'Low',
                        'evidence_base': 'High'
                    }
                },
                'middle': {
                    'study_skills_training': {
                        'name': 'Study Skills and Organization Training',
                        'description': 'Systematic instruction in note-taking, time management, and study strategies',
                        'duration': '6-8 weeks',
                        'frequency': 'Weekly 45-minute sessions',
                        'staff_required': 'School counselor or learning specialist',
                        'success_metrics': ['improved_grades', 'assignment_completion', 'organization_skills'],
                        'cost_estimate': 'Low',
                        'evidence_base': 'Medium-High'
                    },
                    'peer_tutoring': {
                        'name': 'Cross-Age Peer Tutoring',
                        'description': 'High school students provide academic support to middle school students',
                        'duration': 'Ongoing',
                        'frequency': '2-3 times per week, 30 minutes',
                        'staff_required': 'Supervising teacher',
                        'success_metrics': ['academic_improvement', 'confidence_building', 'engagement'],
                        'cost_estimate': 'Very Low',
                        'evidence_base': 'High'
                    }
                },
                'high': {
                    'credit_recovery': {
                        'name': 'Online Credit Recovery Program',
                        'description': 'Self-paced online courses to recover failed credits',
                        'duration': 'Variable (8-16 weeks)',
                        'frequency': 'Self-paced with weekly check-ins',
                        'staff_required': 'Certified teacher for oversight',
                        'success_metrics': ['credits_earned', 'course_completion', 'graduation_progress'],
                        'cost_estimate': 'Medium',
                        'evidence_base': 'Medium'
                    },
                    'intensive_tutoring': {
                        'name': 'High-Dosage Tutoring',
                        'description': 'Individualized or small group intensive academic support',
                        'duration': 'Full semester',
                        'frequency': 'Daily 50-minute sessions',
                        'staff_required': 'Certified teacher or trained tutor',
                        'success_metrics': ['grade_improvement', 'test_scores', 'course_passing'],
                        'cost_estimate': 'High',
                        'evidence_base': 'Very High'
                    }
                }
            },
            'attendance_support': {
                'universal': {
                    'attendance_intervention': {
                        'name': 'Tiered Attendance Intervention',
                        'description': 'Progressive interventions from family outreach to formal truancy procedures',
                        'tiers': {
                            'tier_1': 'Family contact and barrier assessment',
                            'tier_2': 'Attendance contract and support services',
                            'tier_3': 'Formal truancy intervention and legal referral'
                        },
                        'staff_required': 'Attendance coordinator, social worker',
                        'success_metrics': ['attendance_rate_improvement', 'chronic_absenteeism_reduction'],
                        'cost_estimate': 'Medium',
                        'evidence_base': 'High'
                    }
                }
            },
            'behavioral_support': {
                'elementary': {
                    'pbis_support': {
                        'name': 'Positive Behavioral Interventions and Supports',
                        'description': 'School-wide positive behavior system with individual supports',
                        'duration': 'Ongoing',
                        'frequency': 'Daily implementation',
                        'staff_required': 'PBIS coach, teachers',
                        'success_metrics': ['behavior_incidents', 'office_referrals', 'classroom_engagement'],
                        'cost_estimate': 'Medium',
                        'evidence_base': 'Very High'
                    }
                },
                'middle': {
                    'restorative_practices': {
                        'name': 'Restorative Justice Practices',
                        'description': 'Conflict resolution and relationship-building approaches',
                        'duration': 'Ongoing',
                        'frequency': 'As needed with weekly circles',
                        'staff_required': 'Trained facilitator',
                        'success_metrics': ['suspension_reduction', 'relationship_quality', 'school_climate'],
                        'cost_estimate': 'Low-Medium',
                        'evidence_base': 'Medium'
                    }
                },
                'high': {
                    'counseling_support': {
                        'name': 'Individual and Group Counseling',
                        'description': 'Mental health and behavioral support services',
                        'duration': 'Variable',
                        'frequency': 'Weekly or bi-weekly sessions',
                        'staff_required': 'School counselor or therapist',
                        'success_metrics': ['behavioral_improvement', 'emotional_regulation', 'academic_engagement'],
                        'cost_estimate': 'Medium-High',
                        'evidence_base': 'High'
                    }
                }
            },
            'engagement_support': {
                'middle': {
                    'mentoring_program': {
                        'name': 'Adult Mentoring Program',
                        'description': 'Caring adult provides regular support and guidance',
                        'duration': 'Full school year',
                        'frequency': 'Weekly 30-minute meetings',
                        'staff_required': 'Program coordinator',
                        'success_metrics': ['engagement_improvement', 'relationship_quality', 'academic_progress'],
                        'cost_estimate': 'Low-Medium',
                        'evidence_base': 'High'
                    }
                },
                'high': {
                    'work_based_learning': {
                        'name': 'Work-Based Learning Program',
                        'description': 'Real-world work experience connected to career interests',
                        'duration': 'Semester or full year',
                        'frequency': 'Several hours per week',
                        'staff_required': 'Career coordinator',
                        'success_metrics': ['engagement_improvement', 'career_readiness', 'graduation_rates'],
                        'cost_estimate': 'Medium',
                        'evidence_base': 'Medium-High'
                    }
                }
            },
            'family_engagement': {
                'universal': {
                    'family_liaison': {
                        'name': 'Family Liaison Services',
                        'description': 'Dedicated staff to connect families with school and community resources',
                        'duration': 'Ongoing',
                        'frequency': 'Regular contact as needed',
                        'staff_required': 'Family liaison or social worker',
                        'success_metrics': ['family_engagement', 'resource_connection', 'student_stability'],
                        'cost_estimate': 'Medium',
                        'evidence_base': 'Medium'
                    }
                }
            }
        }
    
    def assess_student_risk(self, student_data: Dict) -> Dict:
        """Comprehensive risk assessment for K-12 student."""
        # Get prediction and explanation from explainable AI
        explanation_result = self.explainable_ai.predict_with_explanation(student_data)
        
        # Extract key information
        prediction = explanation_result['prediction']
        explanation = explanation_result['explanation']
        grade_band = explanation_result['grade_band']
        
        # Calculate comprehensive risk assessment
        risk_assessment = {
            'overall_risk': {
                'category': prediction['risk_category'],
                'score': prediction['risk_score'],
                'probability': prediction['success_probability'],
                'confidence': explanation['confidence_indicators']['model_confidence']
            },
            'risk_factors': explanation['key_insights']['risk_factors'],
            'protective_factors': explanation['key_insights']['protective_factors'],
            'grade_band': grade_band,
            'priority_areas': self._identify_priority_areas(
                explanation['key_insights']['risk_factors'], grade_band
            )
        }
        
        return risk_assessment
    
    def generate_intervention_plan(self, student_data: Dict, risk_assessment: Optional[Dict] = None) -> Dict:
        """Generate comprehensive intervention plan for student."""
        if risk_assessment is None:
            risk_assessment = self.assess_student_risk(student_data)
        
        grade_band = risk_assessment['grade_band']
        risk_category = risk_assessment['overall_risk']['category']
        risk_factors = risk_assessment['risk_factors']
        
        # Determine intervention intensity
        intervention_intensity = self._determine_intensity(risk_category, len(risk_factors))
        
        # Select appropriate interventions
        recommended_interventions = self._select_interventions(
            risk_factors, grade_band, intervention_intensity
        )
        
        # Create implementation timeline
        implementation_plan = self._create_implementation_timeline(
            recommended_interventions, grade_band, intervention_intensity
        )
        
        # Calculate resource requirements
        resource_requirements = self._calculate_resources(recommended_interventions)
        
        # Generate monitoring plan
        monitoring_plan = self._create_monitoring_plan(risk_factors, grade_band)
        
        intervention_plan = {
            'student_info': {
                'student_id': student_data.get('student_id', 'Unknown'),
                'grade_level': student_data.get('grade_level', 0),
                'grade_band': grade_band,
                'risk_category': risk_category
            },
            'intervention_summary': {
                'intensity': intervention_intensity,
                'focus_areas': [factor['category'] for factor in risk_factors[:3]],
                'estimated_duration': implementation_plan['total_duration'],
                'staff_required': resource_requirements['staff_count']
            },
            'recommended_interventions': recommended_interventions,
            'implementation_plan': implementation_plan,
            'resource_requirements': resource_requirements,
            'monitoring_plan': monitoring_plan,
            'expected_outcomes': self._define_expected_outcomes(
                recommended_interventions, grade_band
            )
        }
        
        return intervention_plan
    
    def _identify_priority_areas(self, risk_factors: List[Dict], grade_band: str) -> List[str]:
        """Identify priority intervention areas based on risk factors and grade band."""
        priority_areas = []
        
        # Map risk factors to intervention categories
        for factor in risk_factors[:3]:  # Top 3 risks
            category = factor['category'].lower()
            if 'academic' in category:
                priority_areas.append('academic_support')
            elif 'attendance' in category or 'engagement' in category:
                priority_areas.append('attendance_support')
            elif 'behavior' in category or 'disciplinary' in category:
                priority_areas.append('behavioral_support')
            elif 'warning' in category:
                # Determine specific warning type
                factor_name = factor['factor'].lower()
                if 'attendance' in factor_name:
                    priority_areas.append('attendance_support')
                elif 'academic' in factor_name or 'grade' in factor_name:
                    priority_areas.append('academic_support')
                else:
                    priority_areas.append('behavioral_support')
        
        # Add grade-band specific priorities
        band_priorities = self.grade_band_priorities[grade_band]['primary_focus']
        for priority in band_priorities:
            if 'reading' in priority or 'academic' in priority:
                if 'academic_support' not in priority_areas:
                    priority_areas.append('academic_support')
            elif 'attendance' in priority or 'engagement' in priority:
                if 'attendance_support' not in priority_areas:
                    priority_areas.append('attendance_support')
        
        return list(set(priority_areas))[:4]  # Limit to 4 priority areas
    
    def _determine_intensity(self, risk_category: str, num_risk_factors: int) -> str:
        """Determine intervention intensity based on risk level."""
        if risk_category == 'High Risk' or num_risk_factors >= 4:
            return 'Intensive'
        elif risk_category == 'Medium Risk' or num_risk_factors >= 2:
            return 'Targeted'
        else:
            return 'Universal'
    
    def _select_interventions(self, risk_factors: List[Dict], grade_band: str, 
                            intensity: str) -> List[Dict]:
        """Select appropriate interventions based on risk profile."""
        selected_interventions = []
        
        # Map risk factors to intervention categories
        needed_categories = set()
        for factor in risk_factors:
            if 'Academic' in factor['category']:
                needed_categories.add('academic_support')
            elif 'Attendance' in factor['category'] or 'Engagement' in factor['category']:
                needed_categories.add('attendance_support')
            elif 'behavior' in factor['factor'].lower() or 'disciplinary' in factor['factor'].lower():
                needed_categories.add('behavioral_support')
        
        # Always consider family engagement for K-12
        needed_categories.add('family_engagement')
        
        # Select interventions from each needed category
        for category in needed_categories:
            if category in self.intervention_strategies:
                category_interventions = self.intervention_strategies[category]
                
                # Check for grade-band specific interventions first
                if grade_band in category_interventions:
                    interventions = category_interventions[grade_band]
                elif 'universal' in category_interventions:
                    interventions = category_interventions['universal']
                else:
                    continue
                
                # Select best intervention from category
                for intervention_key, intervention_data in interventions.items():
                    intervention_info = intervention_data.copy()
                    intervention_info['category'] = category
                    intervention_info['key'] = intervention_key
                    intervention_info['priority'] = self._calculate_priority(
                        intervention_data, intensity, risk_factors
                    )
                    selected_interventions.append(intervention_info)
        
        # Sort by priority and evidence base
        selected_interventions.sort(
            key=lambda x: (x['priority'], self._evidence_score(x['evidence_base'])), 
            reverse=True
        )
        
        # Limit based on intensity
        if intensity == 'Intensive':
            return selected_interventions[:5]
        elif intensity == 'Targeted':
            return selected_interventions[:3]
        else:
            return selected_interventions[:2]
    
    def _calculate_priority(self, intervention: Dict, intensity: str, 
                          risk_factors: List[Dict]) -> float:
        """Calculate priority score for intervention."""
        priority_score = 0.0
        
        # Evidence base weight
        evidence_weight = {
            'Very High': 1.0,
            'High': 0.8,
            'Medium-High': 0.6,
            'Medium': 0.4,
            'Low': 0.2
        }
        priority_score += evidence_weight.get(intervention.get('evidence_base', 'Medium'), 0.4)
        
        # Cost consideration (lower cost = higher priority for resource constraints)
        cost_weight = {
            'Very Low': 1.0,
            'Low': 0.8,
            'Low-Medium': 0.6,
            'Medium': 0.4,
            'Medium-High': 0.2,
            'High': 0.1
        }
        priority_score += cost_weight.get(intervention.get('cost_estimate', 'Medium'), 0.4)
        
        # Intensity match
        if intensity == 'Intensive':
            priority_score += 0.5
        
        return priority_score
    
    def _evidence_score(self, evidence_base: str) -> float:
        """Convert evidence base to numeric score."""
        scores = {
            'Very High': 5.0,
            'High': 4.0,
            'Medium-High': 3.0,
            'Medium': 2.0,
            'Low': 1.0
        }
        return scores.get(evidence_base, 2.0)
    
    def _create_implementation_timeline(self, interventions: List[Dict], 
                                      grade_band: str, intensity: str) -> Dict:
        """Create implementation timeline for interventions."""
        timeline = {
            'phase_1_immediate': [],  # 0-2 weeks
            'phase_2_short_term': [],  # 2-8 weeks
            'phase_3_ongoing': [],     # 8+ weeks
            'total_duration': '12-16 weeks'
        }
        
        for intervention in interventions:
            duration = intervention.get('duration', '4-6 weeks')
            
            # Categorize based on urgency and duration
            if 'immediate' in duration.lower() or intervention['category'] == 'attendance_support':
                timeline['phase_1_immediate'].append({
                    'intervention': intervention['name'],
                    'start_time': 'Within 1 week',
                    'duration': duration
                })
            elif any(term in duration.lower() for term in ['weeks', 'short']):
                timeline['phase_2_short_term'].append({
                    'intervention': intervention['name'],
                    'start_time': 'Weeks 2-3',
                    'duration': duration
                })
            else:
                timeline['phase_3_ongoing'].append({
                    'intervention': intervention['name'],
                    'start_time': 'Week 4',
                    'duration': duration
                })
        
        # Adjust total duration based on intensity
        if intensity == 'Intensive':
            timeline['total_duration'] = '16-24 weeks'
        elif intensity == 'Targeted':
            timeline['total_duration'] = '12-16 weeks'
        else:
            timeline['total_duration'] = '8-12 weeks'
        
        return timeline
    
    def _calculate_resources(self, interventions: List[Dict]) -> Dict:
        """Calculate resource requirements for interventions."""
        staff_roles = set()
        cost_levels = []
        
        for intervention in interventions:
            staff_required = intervention.get('staff_required', 'Teacher')
            cost_estimate = intervention.get('cost_estimate', 'Medium')
            
            staff_roles.add(staff_required)
            cost_levels.append(cost_estimate)
        
        # Estimate overall cost
        cost_weights = {'Very Low': 1, 'Low': 2, 'Low-Medium': 3, 'Medium': 4, 'Medium-High': 5, 'High': 6}
        avg_cost = np.mean([cost_weights.get(cost, 4) for cost in cost_levels])
        
        if avg_cost <= 2:
            overall_cost = 'Low'
        elif avg_cost <= 4:
            overall_cost = 'Medium'
        else:
            overall_cost = 'High'
        
        return {
            'staff_count': len(staff_roles),
            'staff_roles': list(staff_roles),
            'overall_cost': overall_cost,
            'estimated_cost_range': f'${len(interventions) * 500}-${len(interventions) * 2000} per student'
        }
    
    def _create_monitoring_plan(self, risk_factors: List[Dict], grade_band: str) -> Dict:
        """Create monitoring and evaluation plan."""
        monitoring_plan = {
            'frequency': 'Bi-weekly progress reviews',
            'key_metrics': [],
            'data_collection': [],
            'review_schedule': {
                'initial_review': '2 weeks after implementation',
                'progress_reviews': 'Every 4 weeks',
                'comprehensive_review': '12 weeks'
            },
            'success_criteria': []
        }
        
        # Add metrics based on risk factors
        for factor in risk_factors:
            if 'Academic' in factor['category']:
                monitoring_plan['key_metrics'].extend(['grades', 'assignment_completion', 'test_scores'])
                monitoring_plan['data_collection'].extend(['grade_reports', 'teacher_observations'])
            elif 'Attendance' in factor['category']:
                monitoring_plan['key_metrics'].extend(['attendance_rate', 'tardiness', 'early_dismissals'])
                monitoring_plan['data_collection'].extend(['attendance_records', 'daily_tracking'])
            elif 'behavior' in factor['factor'].lower():
                monitoring_plan['key_metrics'].extend(['office_referrals', 'suspensions', 'classroom_behavior'])
                monitoring_plan['data_collection'].extend(['behavior_tracking', 'teacher_reports'])
        
        # Remove duplicates and add grade-band specific metrics
        monitoring_plan['key_metrics'] = list(set(monitoring_plan['key_metrics']))
        monitoring_plan['data_collection'] = list(set(monitoring_plan['data_collection']))
        
        # Add success criteria
        if grade_band == 'elementary':
            monitoring_plan['success_criteria'] = [
                'Improvement in reading level',
                'Attendance rate above 95%',
                'Reduction in behavior incidents'
            ]
        elif grade_band == 'middle':
            monitoring_plan['success_criteria'] = [
                'Passing all core classes',
                'Improved engagement measures',
                'Positive teacher feedback'
            ]
        else:  # high school
            monitoring_plan['success_criteria'] = [
                'On-track for graduation',
                'Credit recovery progress',
                'Attendance improvement'
            ]
        
        return monitoring_plan
    
    def _define_expected_outcomes(self, interventions: List[Dict], grade_band: str) -> Dict:
        """Define expected outcomes and ROI for interventions."""
        return {
            'short_term_outcomes': [
                'Improved daily attendance',
                'Better classroom engagement',
                'Reduced behavioral incidents'
            ],
            'medium_term_outcomes': [
                'Improved academic performance',
                'Stronger school connection',
                'Better family engagement'
            ],
            'long_term_outcomes': [
                'On-track for grade promotion',
                'Reduced risk of dropout',
                'Improved post-secondary readiness'
            ],
            'roi_estimate': {
                'cost_per_student': f'${len(interventions) * 1000}-${len(interventions) * 3000}',
                'potential_savings': 'Reduced special education referrals, lower dropout costs',
                'graduation_impact': 'Increased likelihood of graduation by 15-25%'
            }
        }
    
    def generate_family_communication(self, intervention_plan: Dict) -> Dict:
        """Generate family-friendly communication about the intervention plan."""
        student_info = intervention_plan['student_info']
        grade_level = student_info['grade_level']
        
        communication = {
            'parent_letter': {
                'subject': f"Support Plan for Your Grade {grade_level} Student",
                'opening': f"We want to share some exciting news about additional support we're providing for your child's success in Grade {grade_level}.",
                'plan_summary': f"Based on our assessment, we've developed a personalized plan to help your child thrive academically and socially.",
                'interventions_explained': [],
                'family_role': [
                    "Attend regular progress meetings",
                    "Support interventions at home",
                    "Communicate regularly with school staff"
                ],
                'contact_info': "Please contact your child's teacher or school counselor with any questions."
            },
            'quick_reference': {
                'what_this_means': "Your child will receive extra support to ensure success",
                'how_long': intervention_plan['implementation_plan']['total_duration'],
                'who_will_help': intervention_plan['resource_requirements']['staff_roles'],
                'how_to_help_at_home': self._generate_home_support_tips(student_info['grade_band'])
            }
        }
        
        # Translate intervention plans to family-friendly language
        for intervention in intervention_plan['recommended_interventions']:
            family_description = {
                'what': intervention['name'],
                'why': f"To help with {intervention['category'].replace('_', ' ')}",
                'when': intervention.get('frequency', 'Regular sessions'),
                'benefit': f"This will help your child {self._get_intervention_benefit(intervention)}"
            }
            communication['parent_letter']['interventions_explained'].append(family_description)
        
        return communication
    
    def _generate_home_support_tips(self, grade_band: str) -> List[str]:
        """Generate grade-appropriate home support tips for families."""
        tips = {
            'elementary': [
                "Read with your child daily for 15-20 minutes",
                "Create a quiet homework space",
                "Establish consistent bedtime routine",
                "Communicate regularly with your child's teacher",
                "Celebrate small achievements and effort"
            ],
            'middle': [
                "Help your child organize assignments and due dates",
                "Encourage participation in school activities",
                "Monitor homework completion without doing it for them",
                "Talk about their day and any challenges",
                "Support good study habits and time management"
            ],
            'high': [
                "Discuss graduation requirements and career goals",
                "Support college and career exploration",
                "Encourage regular attendance and punctuality",
                "Help them balance work, school, and activities",
                "Stay involved while promoting independence"
            ]
        }
        
        return tips.get(grade_band, tips['middle'])
    
    def _get_intervention_benefit(self, intervention: Dict) -> str:
        """Get family-friendly benefit description for intervention."""
        benefits = {
            'academic_support': 'improve their grades and understanding of key concepts',
            'attendance_support': 'develop better school attendance habits',
            'behavioral_support': 'build positive relationships and self-regulation skills',
            'engagement_support': 'feel more connected to school and learning',
            'family_engagement': 'strengthen the home-school partnership'
        }
        
        return benefits.get(intervention['category'], 'achieve greater success in school')

def main():
    """Test the K-12 Intervention System."""
    print("🎯 K-12 Intervention System Testing")
    print("=" * 50)
    
    # Initialize system
    intervention_system = K12InterventionSystem()
    
    # Test with sample at-risk student
    sample_student = {
        'student_id': 'TEST_INTERVENTION_001',
        'grade_level': 5,
        'current_gpa': 2.1,
        'attendance_rate': 0.82,
        'chronic_absenteeism': 1,
        'behavior_score': 0.75,
        'course_failures_total': 2,
        'free_reduced_lunch': 1,
        'ell_status': 1,
        'parent_engagement_level': 0,
        'has_disciplinary_issues': 1,
        'reading_below_proficient': 1
    }
    
    print(f"\n📊 Assessing Student: {sample_student['student_id']}")
    print(f"Grade Level: {sample_student['grade_level']}")
    
    # Assess risk
    risk_assessment = intervention_system.assess_student_risk(sample_student)
    print(f"Risk Category: {risk_assessment['overall_risk']['category']}")
    print(f"Success Probability: {risk_assessment['overall_risk']['probability']:.1%}")
    
    # Generate intervention plan
    intervention_plan = intervention_system.generate_intervention_plan(sample_student, risk_assessment)
    
    print(f"\n🎯 Intervention Plan Summary:")
    print(f"Intensity: {intervention_plan['intervention_summary']['intensity']}")
    print(f"Duration: {intervention_plan['intervention_summary']['estimated_duration']}")
    print(f"Staff Required: {intervention_plan['intervention_summary']['staff_required']}")
    
    print(f"\n📋 Recommended Interventions:")
    for i, intervention in enumerate(intervention_plan['recommended_interventions'], 1):
        print(f"{i}. {intervention['name']}")
        print(f"   Category: {intervention['category'].replace('_', ' ').title()}")
        print(f"   Duration: {intervention.get('duration', 'Ongoing')}")
        print(f"   Evidence: {intervention.get('evidence_base', 'Medium')}")
    
    print(f"\n📅 Implementation Timeline:")
    timeline = intervention_plan['implementation_plan']
    if timeline['phase_1_immediate']:
        print("Phase 1 (Immediate):")
        for item in timeline['phase_1_immediate']:
            print(f"  • {item['intervention']}")
    
    # Generate family communication
    family_comm = intervention_system.generate_family_communication(intervention_plan)
    
    print(f"\n👨‍👩‍👧‍👦 Family Communication:")
    print(f"Letter Subject: {family_comm['parent_letter']['subject']}")
    print(f"Key Message: {family_comm['parent_letter']['opening']}")
    
    print(f"\n🏠 Home Support Tips:")
    for tip in family_comm['quick_reference']['how_to_help_at_home'][:3]:
        print(f"  • {tip}")
    
    print(f"\n🎉 K-12 Intervention System testing complete!")

if __name__ == "__main__":
    main()