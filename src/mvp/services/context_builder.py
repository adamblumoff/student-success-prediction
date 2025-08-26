#!/usr/bin/env python3
"""
Context Builder Service

Builds rich, formatted context from database and input data for GPT-OSS analysis.
Handles prompt engineering, data formatting, and context optimization for educational AI.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mvp.logging_config import get_logger

logger = get_logger(__name__)

class ContextBuilder:
    """Service for building rich context for GPT-OSS educational analysis."""
    
    def __init__(self):
        """Initialize context builder with educational templates."""
        
        # Grade-level specific context templates
        self.grade_contexts = {
            "elementary": {
                "grades": ["K", "1", "2", "3", "4", "5"],
                "focus_areas": ["reading_foundation", "math_basics", "social_skills", "classroom_behavior"],
                "typical_interventions": ["reading_support", "math_tutoring", "behavior_plan", "family_engagement"],
                "key_metrics": ["reading_level", "math_fluency", "attendance", "classroom_participation"],
                "developmental_considerations": "Focus on foundational skills, concrete thinking, need for structure"
            },
            "middle": {
                "grades": ["6", "7", "8"], 
                "focus_areas": ["academic_transition", "peer_relationships", "study_skills", "emotional_regulation"],
                "typical_interventions": ["study_skills_training", "peer_mentoring", "counseling", "academic_support"],
                "key_metrics": ["gpa_trend", "assignment_completion", "social_adjustment", "extracurricular_engagement"],
                "developmental_considerations": "Adolescent transition, peer influence critical, identity formation"
            },
            "high": {
                "grades": ["9", "10", "11", "12"],
                "focus_areas": ["graduation_requirements", "college_career_prep", "credit_recovery", "independence"],
                "typical_interventions": ["credit_recovery", "career_counseling", "college_prep", "internships"],
                "key_metrics": ["credits_earned", "graduation_track", "post_secondary_readiness", "attendance"],
                "developmental_considerations": "Future planning critical, increasing independence, adult transition prep"
            }
        }
        
        # Risk level context templates
        self.risk_contexts = {
            "Low": {
                "typical_profile": "Student meeting or exceeding expectations",
                "focus": "Enrichment and continued growth",
                "timeline": "Regular monitoring, quarterly check-ins",
                "resources": "Minimal additional resources needed"
            },
            "Medium": {
                "typical_profile": "Student showing some areas of concern but generally on track", 
                "focus": "Targeted support in specific areas",
                "timeline": "Bi-weekly monitoring, monthly progress reviews",
                "resources": "Moderate intervention resources needed"
            },
            "High": {
                "typical_profile": "Student at significant risk of academic failure or dropout",
                "focus": "Intensive, comprehensive support needed",
                "timeline": "Daily/weekly monitoring, immediate intervention",
                "resources": "Significant intervention resources and coordination required"
            }
        }
        
        # Educational domain templates
        self.educational_domains = {
            "academic": ["gpa", "grades", "test_scores", "assignment_completion", "study_skills"],
            "behavioral": ["discipline_incidents", "classroom_behavior", "social_skills", "emotional_regulation"],
            "engagement": ["attendance", "participation", "extracurricular", "parent_involvement"],
            "social_emotional": ["peer_relationships", "self_confidence", "motivation", "stress_management"]
        }
    
    def build_student_analysis_context(self, student_data: Dict[str, Any], 
                                     ml_results: Dict[str, Any],
                                     historical_data: Optional[Dict[str, Any]] = None,
                                     context_depth: str = "detailed") -> str:
        """
        Build comprehensive context for individual student analysis.
        
        Args:
            student_data: Current student data
            ml_results: Machine learning prediction results  
            historical_data: Historical student data if available
            context_depth: Level of context detail ("basic", "detailed", "comprehensive")
            
        Returns:
            Formatted context string for GPT analysis
        """
        context_sections = []
        
        # Header with analysis type
        context_sections.append(self._build_analysis_header(student_data, context_depth))
        
        # Student profile section
        context_sections.append(self._build_student_profile(student_data))
        
        # Current performance metrics
        context_sections.append(self._build_performance_metrics(student_data, ml_results))
        
        # Grade-level and developmental context
        context_sections.append(self._build_developmental_context(student_data))
        
        # Historical trends if available
        if historical_data and context_depth in ["detailed", "comprehensive"]:
            context_sections.append(self._build_historical_context(historical_data))
        
        # Risk assessment context
        context_sections.append(self._build_risk_context(ml_results))
        
        # Educational priorities and focus areas
        context_sections.append(self._build_educational_priorities(student_data, ml_results))
        
        # Comprehensive analysis request
        if context_depth == "comprehensive":
            context_sections.append(self._build_comprehensive_analysis_request())
        elif context_depth == "detailed":
            context_sections.append(self._build_detailed_analysis_request())
        else:
            context_sections.append(self._build_basic_analysis_request())
        
        return "\n\n".join(context_sections)
    
    def build_cohort_analysis_context(self, cohort_data: Dict[str, Any],
                                    context_focus: str = "patterns") -> str:
        """
        Build context for cohort-level analysis.
        
        Args:
            cohort_data: Aggregated cohort data
            context_focus: Analysis focus ("patterns", "interventions", "equity")
            
        Returns:
            Formatted context string for cohort GPT analysis
        """
        context_sections = []
        
        # Cohort overview
        context_sections.append(self._build_cohort_overview(cohort_data))
        
        # Demographics and populations
        context_sections.append(self._build_cohort_demographics(cohort_data))
        
        # Performance distribution
        context_sections.append(self._build_cohort_performance(cohort_data))
        
        # Intervention patterns
        context_sections.append(self._build_cohort_interventions(cohort_data))
        
        # Analysis request based on focus
        if context_focus == "patterns":
            context_sections.append(self._build_pattern_analysis_request())
        elif context_focus == "interventions":
            context_sections.append(self._build_intervention_analysis_request())
        elif context_focus == "equity":
            context_sections.append(self._build_equity_analysis_request())
        else:
            context_sections.append(self._build_general_cohort_request())
        
        return "\n\n".join(context_sections)
    
    def build_intervention_planning_context(self, student_data: Dict[str, Any],
                                          intervention_history: List[Dict[str, Any]],
                                          available_resources: Dict[str, Any] = None) -> str:
        """
        Build context specifically for intervention planning.
        
        Args:
            student_data: Student profile data
            intervention_history: Previous interventions and outcomes
            available_resources: School/district available resources
            
        Returns:
            Formatted context for intervention planning
        """
        context_sections = []
        
        # Intervention planning header
        context_sections.append("INTERVENTION PLANNING ANALYSIS")
        context_sections.append("Objective: Develop evidence-based, practical intervention strategy")
        
        # Student summary for intervention planning
        context_sections.append(self._build_intervention_student_summary(student_data))
        
        # Historical intervention analysis
        context_sections.append(self._build_intervention_history_analysis(intervention_history))
        
        # Available resources and constraints
        if available_resources:
            context_sections.append(self._build_resource_context(available_resources))
        
        # Intervention planning request
        context_sections.append(self._build_intervention_planning_request(student_data))
        
        return "\n\n".join(context_sections)
    
    def _build_analysis_header(self, student_data: Dict[str, Any], context_depth: str) -> str:
        """Build analysis header with key student information."""
        grade = student_data.get("grade_level", "Unknown")
        analysis_type = context_depth.upper()
        
        header_lines = [
            f"STUDENT SUCCESS ANALYSIS - {analysis_type}",
            f"Grade Level: {grade}",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Analysis Type: Educational Risk Assessment and Intervention Planning"
        ]
        
        return "\n".join(header_lines)
    
    def _build_student_profile(self, student_data: Dict[str, Any]) -> str:
        """Build anonymized student profile section."""
        profile_lines = ["STUDENT PROFILE:"]
        
        # Grade and educational context
        grade = student_data.get("grade_level", "Unknown")
        profile_lines.append(f"• Grade Level: {grade}")
        
        # Enrollment information
        if student_data.get("enrollment_status"):
            profile_lines.append(f"• Enrollment Status: {student_data['enrollment_status']}")
        
        # Special populations (important for intervention planning)
        special_populations = []
        if student_data.get("is_ell"):
            special_populations.append("English Language Learner")
        if student_data.get("has_iep"):
            special_populations.append("Individual Education Plan")
        if student_data.get("has_504"):
            special_populations.append("Section 504 Plan")
        if student_data.get("is_economically_disadvantaged"):
            special_populations.append("Economically Disadvantaged")
        
        if special_populations:
            profile_lines.append(f"• Special Populations: {', '.join(special_populations)}")
        else:
            profile_lines.append("• Special Populations: None identified")
        
        return "\n".join(profile_lines)
    
    def _build_performance_metrics(self, student_data: Dict[str, Any], ml_results: Dict[str, Any]) -> str:
        """Build current performance metrics section."""
        metrics_lines = ["CURRENT PERFORMANCE METRICS:"]
        
        # ML model results
        risk_score = ml_results.get("risk_score", 0)
        risk_category = ml_results.get("risk_category", "Unknown")
        success_prob = ml_results.get("success_probability", 0)
        
        metrics_lines.extend([
            f"• ML Risk Assessment: {risk_category} ({risk_score:.2f}/1.0)",
            f"• Success Probability: {success_prob:.1%}",
            f"• Model Confidence: {ml_results.get('confidence_score', 0):.2f}"
        ])
        
        # Academic metrics
        academic_metrics = []
        if student_data.get("current_gpa") is not None:
            gpa = student_data["current_gpa"]
            metrics_lines.append(f"• Current GPA: {gpa:.2f}")
            
        if student_data.get("attendance_rate") is not None:
            attendance = student_data["attendance_rate"]
            metrics_lines.append(f"• Attendance Rate: {attendance:.1%}")
            
        if student_data.get("assignment_completion") is not None:
            completion = student_data["assignment_completion"]
            metrics_lines.append(f"• Assignment Completion: {completion:.1%}")
            
        if student_data.get("discipline_incidents") is not None:
            incidents = student_data["discipline_incidents"]
            metrics_lines.append(f"• Discipline Incidents: {incidents}")
        
        return "\n".join(metrics_lines)
    
    def _build_developmental_context(self, student_data: Dict[str, Any]) -> str:
        """Build developmental and grade-level context."""
        grade = student_data.get("grade_level", "Unknown")
        grade_band = self._determine_grade_band(grade)
        
        context_lines = ["DEVELOPMENTAL & EDUCATIONAL CONTEXT:"]
        
        if grade_band in self.grade_contexts:
            grade_info = self.grade_contexts[grade_band]
            context_lines.extend([
                f"• Grade Band: {grade_band.title()} School ({grade})",
                f"• Key Focus Areas: {', '.join(grade_info['focus_areas'])}",
                f"• Typical Interventions: {', '.join(grade_info['typical_interventions'])}",
                f"• Developmental Considerations: {grade_info['developmental_considerations']}"
            ])
        else:
            context_lines.append(f"• Grade Level: {grade} (context not specified)")
        
        return "\n".join(context_lines)
    
    def _build_historical_context(self, historical_data: Dict[str, Any]) -> str:
        """Build historical trends and patterns section."""
        context_lines = ["HISTORICAL CONTEXT:"]
        
        # Intervention history
        if historical_data.get("intervention_history"):
            interventions = historical_data["intervention_history"]
            total = len(interventions)
            successful = sum(1 for i in interventions if i.get("outcome") == "successful")
            
            success_rate = (successful/total) if total > 0 else 0
            context_lines.extend([
                f"• Total Previous Interventions: {total}",
                f"• Successful Interventions: {successful} ({success_rate:.1%})"
            ])
            
            # Recent intervention types
            recent_types = [i.get("type", "Unknown") for i in interventions[:3]]
            if recent_types:
                context_lines.append(f"• Recent Intervention Types: {', '.join(recent_types)}")
        
        # Temporal trends
        if historical_data.get("temporal_trends"):
            trends = historical_data["temporal_trends"]
            if trends.get("trend_direction"):
                direction = trends["trend_direction"]
                context_lines.append(f"• Risk Trend: {direction.replace('_', ' ').title()}")
        
        # Peer context
        if historical_data.get("peer_context", {}).get("comparison_context"):
            context_lines.append(f"• Peer Comparison: {historical_data['peer_context']['comparison_context']}")
        
        return "\n".join(context_lines)
    
    def _build_risk_context(self, ml_results: Dict[str, Any]) -> str:
        """Build risk assessment context section."""
        risk_category = ml_results.get("risk_category", "Unknown")
        context_lines = ["RISK ASSESSMENT CONTEXT:"]
        
        if risk_category in self.risk_contexts:
            risk_info = self.risk_contexts[risk_category]
            context_lines.extend([
                f"• Risk Level: {risk_category}",
                f"• Typical Profile: {risk_info['typical_profile']}",
                f"• Focus Area: {risk_info['focus']}",
                f"• Recommended Timeline: {risk_info['timeline']}",
                f"• Resource Level: {risk_info['resources']}"
            ])
        else:
            context_lines.append(f"• Risk Level: {risk_category}")
        
        return "\n".join(context_lines)
    
    def _build_educational_priorities(self, student_data: Dict[str, Any], ml_results: Dict[str, Any]) -> str:
        """Build educational priorities based on data analysis."""
        context_lines = ["EDUCATIONAL PRIORITIES:"]
        
        # Determine priority areas based on available data
        priorities = []
        
        # Academic priorities
        if student_data.get("current_gpa", 4.0) < 2.0:
            priorities.append("Academic Recovery - GPA improvement critical")
        elif student_data.get("current_gpa", 4.0) < 3.0:
            priorities.append("Academic Support - GPA enhancement needed")
            
        # Attendance priorities
        if student_data.get("attendance_rate", 1.0) < 0.85:
            priorities.append("Attendance Intervention - Below acceptable threshold")
        elif student_data.get("attendance_rate", 1.0) < 0.95:
            priorities.append("Attendance Monitoring - Slight concern")
            
        # Assignment completion
        if student_data.get("assignment_completion", 1.0) < 0.70:
            priorities.append("Assignment Support - Significant completion issues")
        elif student_data.get("assignment_completion", 1.0) < 0.85:
            priorities.append("Study Skills - Moderate completion concerns")
            
        # Behavioral priorities
        if student_data.get("discipline_incidents", 0) > 3:
            priorities.append("Behavioral Support - Multiple incidents need addressing")
        elif student_data.get("discipline_incidents", 0) > 0:
            priorities.append("Behavioral Monitoring - Some incidents noted")
        
        # Risk-based priorities
        risk_category = ml_results.get("risk_category", "Low")
        if risk_category == "High":
            priorities.append("Intensive Support - High-risk student requires immediate attention")
        elif risk_category == "Medium":
            priorities.append("Targeted Support - Moderate risk requires focused intervention")
        
        if priorities:
            for i, priority in enumerate(priorities, 1):
                context_lines.append(f"{i}. {priority}")
        else:
            context_lines.append("• Continue current supports and enrichment opportunities")
        
        return "\n".join(context_lines)
    
    def _build_basic_analysis_request(self) -> str:
        """Build basic analysis request."""
        return """ANALYSIS REQUEST:
Please provide a concise educational analysis focusing on:
1. Primary risk factors and protective factors
2. Top 3 intervention priorities with specific strategies
3. Expected timeline for improvement
4. Key success indicators to monitor

Keep recommendations practical and implementable in a K-12 setting."""
    
    def _build_detailed_analysis_request(self) -> str:
        """Build detailed analysis request."""
        return """ANALYSIS REQUEST:
Please provide a comprehensive educational analysis including:
1. Detailed risk and protective factor analysis
2. Evidence-based intervention strategies with rationale
3. Implementation timeline with specific milestones
4. Resource requirements and staff coordination needs
5. Family engagement and communication strategies
6. Progress monitoring plan with data collection points
7. Short-term (30-60 days) and long-term (semester/year) goals

Focus on actionable, research-based recommendations appropriate for the grade level and school context."""
    
    def _build_comprehensive_analysis_request(self) -> str:
        """Build comprehensive analysis request."""
        return """ANALYSIS REQUEST:
Please provide an in-depth educational analysis including:
1. Holistic student profile considering academic, behavioral, social-emotional factors
2. Comprehensive intervention strategy with primary and supplementary approaches
3. Detailed implementation plan with timeline, responsibilities, and resources
4. Multi-tiered support recommendations (classroom, intervention, intensive)
5. Family partnership and engagement strategies
6. Peer and classroom context considerations
7. Professional development needs for supporting staff
8. Data collection and progress monitoring systems
9. Risk mitigation and contingency planning
10. Long-term success pathway with graduation/post-secondary considerations

Ensure all recommendations are evidence-based, culturally responsive, and aligned with educational best practices."""
    
    def _build_cohort_overview(self, cohort_data: Dict[str, Any]) -> str:
        """Build cohort overview section."""
        overview_lines = ["COHORT OVERVIEW:"]
        
        overview_lines.extend([
            f"• Institution ID: {cohort_data.get('institution_id', 'Unknown')}",
            f"• Total Students: {cohort_data.get('total_students', 0)}",
            f"• Grade Level Filter: {cohort_data.get('grade_level_filter', 'All grades')}",
            f"• Analysis Date: {datetime.now().strftime('%Y-%m-%d')}"
        ])
        
        return "\n".join(overview_lines)
    
    def _build_cohort_demographics(self, cohort_data: Dict[str, Any]) -> str:
        """Build cohort demographics section."""
        demo_lines = ["COHORT DEMOGRAPHICS:"]
        
        if cohort_data.get("demographics"):
            demographics = cohort_data["demographics"]
            
            # Grade distribution
            if demographics.get("grade_levels"):
                grades = demographics["grade_levels"]
                grade_summary = [f"{grade}: {count}" for grade, count in grades.items()]
                demo_lines.append(f"• Grade Distribution: {', '.join(grade_summary)}")
            
            # Special populations
            if demographics.get("special_populations"):
                special = demographics["special_populations"]
                total = demographics.get("total_count", 1)
                
                demo_lines.extend([
                    f"• English Language Learners: {special.get('ell_count', 0)} ({special.get('ell_count', 0)/total:.1%})",
                    f"• Students with IEPs: {special.get('iep_count', 0)} ({special.get('iep_count', 0)/total:.1%})",
                    f"• Students with 504 Plans: {special.get('section_504_count', 0)} ({special.get('section_504_count', 0)/total:.1%})",
                    f"• Economically Disadvantaged: {special.get('economically_disadvantaged_count', 0)} ({special.get('economically_disadvantaged_count', 0)/total:.1%})"
                ])
        
        return "\n".join(demo_lines)
    
    def _build_cohort_performance(self, cohort_data: Dict[str, Any]) -> str:
        """Build cohort performance distribution section."""
        perf_lines = ["PERFORMANCE DISTRIBUTION:"]
        
        if cohort_data.get("risk_distribution"):
            risk_dist = cohort_data["risk_distribution"]
            categories = risk_dist.get("category_distribution", {})
            total_with_predictions = risk_dist.get("total_with_predictions", 0)
            
            if total_with_predictions > 0:
                high_pct = (categories.get("High", 0) / total_with_predictions) * 100
                med_pct = (categories.get("Medium", 0) / total_with_predictions) * 100
                low_pct = (categories.get("Low", 0) / total_with_predictions) * 100
                
                perf_lines.extend([
                    f"• High Risk: {categories.get('High', 0)} students ({high_pct:.1f}%)",
                    f"• Medium Risk: {categories.get('Medium', 0)} students ({med_pct:.1f}%)",
                    f"• Low Risk: {categories.get('Low', 0)} students ({low_pct:.1f}%)",
                    f"• Average Risk Score: {risk_dist.get('average_risk_score', 0):.2f}"
                ])
            else:
                perf_lines.append("• No prediction data available")
        
        return "\n".join(perf_lines)
    
    def _build_cohort_interventions(self, cohort_data: Dict[str, Any]) -> str:
        """Build cohort intervention patterns section."""
        interv_lines = ["INTERVENTION PATTERNS:"]
        
        if cohort_data.get("intervention_patterns"):
            patterns = cohort_data["intervention_patterns"]
            
            interv_lines.extend([
                f"• Total Interventions: {patterns.get('total_interventions', 0)}",
                f"• Students with Interventions: {patterns.get('students_with_interventions', 0)}"
            ])
            
            # Most common intervention types
            if patterns.get("intervention_types"):
                types = patterns["intervention_types"]
                top_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:3]
                type_summary = [f"{itype}: {count}" for itype, count in top_types]
                interv_lines.append(f"• Top Intervention Types: {', '.join(type_summary)}")
            
            # Success rates
            if patterns.get("success_rates"):
                success_rates = patterns["success_rates"]
                rate_summary = []
                for itype, rates in success_rates.items():
                    if rates.get("total", 0) > 0:
                        pct = rates.get("percentage", 0)
                        rate_summary.append(f"{itype}: {pct:.0f}%")
                
                if rate_summary:
                    interv_lines.append(f"• Success Rates: {', '.join(rate_summary)}")
        
        return "\n".join(interv_lines)
    
    def _build_pattern_analysis_request(self) -> str:
        """Build pattern analysis request."""
        return """ANALYSIS REQUEST - PATTERN IDENTIFICATION:
Please analyze the cohort data and identify:
1. Key demographic and performance patterns
2. Students or subgroups at highest risk
3. Intervention effectiveness patterns
4. Systemic factors contributing to student outcomes
5. Recommendations for district-wide improvements
6. Early warning indicators for proactive identification
7. Successful practices that should be scaled

Focus on actionable insights for school and district leadership."""
    
    def _build_intervention_analysis_request(self) -> str:
        """Build intervention-focused analysis request."""
        return """ANALYSIS REQUEST - INTERVENTION EFFECTIVENESS:
Please analyze the intervention data and provide:
1. Most effective intervention strategies for this cohort
2. Intervention gaps or underutilized approaches
3. Resource allocation recommendations
4. Staff professional development priorities
5. Systematic intervention improvements needed
6. Timeline for implementing cohort-wide interventions
7. Success metrics for tracking intervention effectiveness

Focus on practical, evidence-based intervention strategies."""
    
    def _build_equity_analysis_request(self) -> str:
        """Build equity-focused analysis request."""
        return """ANALYSIS REQUEST - EQUITY ANALYSIS:
Please examine the cohort data for equity considerations:
1. Performance gaps between different student populations
2. Disproportionate representation in risk categories
3. Intervention access and effectiveness by student groups
4. Systemic barriers affecting specific populations
5. Culturally responsive intervention recommendations
6. Resource allocation equity assessment
7. Action steps for reducing educational inequities

Prioritize recommendations that address systemic inequities and promote educational justice."""
    
    def _build_general_cohort_request(self) -> str:
        """Build general cohort analysis request."""
        return """ANALYSIS REQUEST - COHORT OVERVIEW:
Please provide a comprehensive cohort analysis including:
1. Overall cohort strengths and areas for improvement
2. Priority intervention needs across the student population
3. Resource allocation recommendations
4. Professional development priorities for staff
5. Family and community engagement strategies
6. Data collection and monitoring recommendations
7. Short-term and long-term cohort goals

Focus on systematic improvements that will benefit the entire student population."""
    
    def _build_intervention_student_summary(self, student_data: Dict[str, Any]) -> str:
        """Build student summary focused on intervention planning."""
        summary_lines = ["STUDENT SUMMARY FOR INTERVENTION PLANNING:"]
        
        grade = student_data.get("grade_level", "Unknown")
        grade_band = self._determine_grade_band(grade)
        
        summary_lines.extend([
            f"• Grade: {grade} ({grade_band} school focus)",
            f"• Current Academic Status: {self._categorize_academic_status(student_data)}",
            f"• Primary Concern Areas: {self._identify_concern_areas(student_data)}",
            f"• Engagement Level: {self._assess_engagement_level(student_data)}"
        ])
        
        return "\n".join(summary_lines)
    
    def _build_intervention_history_analysis(self, intervention_history: List[Dict[str, Any]]) -> str:
        """Build intervention history analysis section."""
        history_lines = ["INTERVENTION HISTORY ANALYSIS:"]
        
        if not intervention_history:
            history_lines.append("• No previous interventions recorded")
            return "\n".join(history_lines)
        
        # Analyze intervention patterns
        total = len(intervention_history)
        successful = sum(1 for i in intervention_history if i.get("outcome") == "successful")
        
        # Identify what worked
        successful_types = [i.get("type") for i in intervention_history if i.get("outcome") == "successful"]
        if successful_types:
            unique_successful = list(set(successful_types))
            history_lines.append(f"• Successful Intervention Types: {', '.join(unique_successful)}")
        
        # Identify what didn't work
        unsuccessful_types = [i.get("type") for i in intervention_history if i.get("outcome") in ["unsuccessful", "no_response"]]
        if unsuccessful_types:
            unique_unsuccessful = list(set(unsuccessful_types))
            history_lines.append(f"• Less Effective Types: {', '.join(unique_unsuccessful)}")
        
        success_rate_pct = (successful/total) if total > 0 else 0
        history_lines.extend([
            f"• Success Rate: {successful}/{total} ({success_rate_pct:.1%})",
            f"• Most Recent Intervention: {intervention_history[0].get('type', 'Unknown') if intervention_history else 'None'}"
        ])
        
        return "\n".join(history_lines)
    
    def _build_resource_context(self, available_resources: Dict[str, Any]) -> str:
        """Build available resources context section."""
        resource_lines = ["AVAILABLE RESOURCES & CONSTRAINTS:"]
        
        if available_resources.get("staff_capacity"):
            resource_lines.append(f"• Staff Capacity: {available_resources['staff_capacity']}")
        
        if available_resources.get("intervention_programs"):
            programs = available_resources["intervention_programs"]
            resource_lines.append(f"• Available Programs: {', '.join(programs)}")
        
        if available_resources.get("time_constraints"):
            resource_lines.append(f"• Time Constraints: {available_resources['time_constraints']}")
        
        if available_resources.get("budget_considerations"):
            resource_lines.append(f"• Budget: {available_resources['budget_considerations']}")
        
        return "\n".join(resource_lines)
    
    def _build_intervention_planning_request(self, student_data: Dict[str, Any]) -> str:
        """Build intervention planning specific request."""
        grade = student_data.get("grade_level", "Unknown")
        grade_band = self._determine_grade_band(grade)
        
        return f"""INTERVENTION PLANNING REQUEST:
Please develop a comprehensive intervention plan considering:
1. Grade-appropriate interventions for {grade_band} school student
2. Evidence-based strategies matching historical success patterns
3. Realistic timeline and implementation steps
4. Staff roles and responsibilities
5. Family involvement and communication plan
6. Progress monitoring and data collection plan
7. Success criteria and milestone indicators
8. Backup strategies if primary interventions are ineffective

Ensure all recommendations are:
• Developmentally appropriate for grade {grade}
• Practically implementable with available resources
• Evidence-based with research support
• Culturally responsive and student-centered
• Aligned with educational best practices"""
    
    def _determine_grade_band(self, grade: str) -> str:
        """Determine elementary/middle/high school band from grade."""
        if not grade or grade == "Unknown":
            return "high"  # Default to high school
            
        if grade.upper() in ["K", "1", "2", "3", "4", "5"]:
            return "elementary"
        elif grade in ["6", "7", "8"]:
            return "middle"
        else:
            return "high"
    
    def _categorize_academic_status(self, student_data: Dict[str, Any]) -> str:
        """Categorize overall academic status."""
        gpa = student_data.get("current_gpa", 2.5)
        attendance = student_data.get("attendance_rate", 0.9)
        completion = student_data.get("assignment_completion", 0.8)
        
        if gpa >= 3.5 and attendance >= 0.95 and completion >= 0.90:
            return "Excelling"
        elif gpa >= 3.0 and attendance >= 0.90 and completion >= 0.80:
            return "Meeting Expectations"
        elif gpa >= 2.0 and attendance >= 0.80 and completion >= 0.60:
            return "Below Expectations"
        else:
            return "At Risk"
    
    def _identify_concern_areas(self, student_data: Dict[str, Any]) -> str:
        """Identify primary areas of concern."""
        concerns = []
        
        if student_data.get("current_gpa", 4.0) < 2.0:
            concerns.append("Academic Performance")
        if student_data.get("attendance_rate", 1.0) < 0.85:
            concerns.append("Attendance")
        if student_data.get("assignment_completion", 1.0) < 0.70:
            concerns.append("Assignment Completion")
        if student_data.get("discipline_incidents", 0) > 2:
            concerns.append("Behavior")
        
        return ", ".join(concerns) if concerns else "No major concerns identified"
    
    def _assess_engagement_level(self, student_data: Dict[str, Any]) -> str:
        """Assess overall student engagement level."""
        attendance = student_data.get("attendance_rate", 0.9)
        completion = student_data.get("assignment_completion", 0.8)
        
        engagement_score = (attendance + completion) / 2
        
        if engagement_score >= 0.90:
            return "High"
        elif engagement_score >= 0.75:
            return "Moderate"
        else:
            return "Low"
    
    def format_for_display(self, analysis_result: str, format_type: str = "web") -> str:
        """
        Format GPT analysis results for different display contexts.
        
        Args:
            analysis_result: Raw GPT analysis text
            format_type: Display format ("web", "report", "email", "mobile")
            
        Returns:
            Formatted analysis text
        """
        if format_type == "web":
            return self._format_for_web_display(analysis_result)
        elif format_type == "report":
            return self._format_for_report_display(analysis_result)
        elif format_type == "email":
            return self._format_for_email_display(analysis_result)
        elif format_type == "mobile":
            return self._format_for_mobile_display(analysis_result)
        else:
            return analysis_result  # Return raw text
    
    def _format_for_web_display(self, analysis_result: str) -> str:
        """Format analysis for web display with HTML-friendly formatting."""
        # Convert numbered lists to HTML
        formatted = analysis_result.replace("\n\n", "<br><br>")
        formatted = formatted.replace("\n", "<br>")
        
        # Add emphasis to key sections
        formatted = formatted.replace("RECOMMENDATIONS:", "<strong>RECOMMENDATIONS:</strong>")
        formatted = formatted.replace("PRIORITIES:", "<strong>PRIORITIES:</strong>")
        formatted = formatted.replace("TIMELINE:", "<strong>TIMELINE:</strong>")
        
        return formatted
    
    def _format_for_report_display(self, analysis_result: str) -> str:
        """Format analysis for formal report display."""
        # Add formal report structure
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        formatted = f"EDUCATIONAL ANALYSIS REPORT\nGenerated: {timestamp}\n\n"
        formatted += analysis_result
        formatted += f"\n\n---\nReport generated by AI-Enhanced Student Success Prediction System"
        
        return formatted
    
    def _format_for_email_display(self, analysis_result: str) -> str:
        """Format analysis for email communication."""
        # Simplify for email readability
        lines = analysis_result.split("\n")
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # Convert numbered lists to bullet points for email
                if line.strip()[0].isdigit() and ". " in line:
                    formatted_lines.append("• " + line.split(". ", 1)[1])
                else:
                    formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    def _format_for_mobile_display(self, analysis_result: str) -> str:
        """Format analysis for mobile display with shorter sections."""
        # Break into shorter sections for mobile reading
        paragraphs = analysis_result.split("\n\n")
        mobile_sections = []
        
        for paragraph in paragraphs:
            if len(paragraph) > 300:  # Split long paragraphs
                sentences = paragraph.split(". ")
                current_section = ""
                
                for sentence in sentences:
                    if len(current_section + sentence) > 250:
                        if current_section:
                            mobile_sections.append(current_section.strip())
                        current_section = sentence + ". "
                    else:
                        current_section += sentence + ". "
                
                if current_section:
                    mobile_sections.append(current_section.strip())
            else:
                mobile_sections.append(paragraph)
        
        return "\n\n".join(mobile_sections)