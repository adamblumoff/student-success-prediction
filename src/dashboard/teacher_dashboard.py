#!/usr/bin/env python3
"""
Teacher Dashboard for Student Success Prediction

Interactive Streamlit dashboard for educators to monitor student progress,
identify at-risk students, and get intervention recommendations.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import warnings
warnings.filterwarnings('ignore')

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))
from models.intervention_system import InterventionRecommendationSystem

# Page configuration
st.set_page_config(
    page_title="Student Success Prediction Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem;
    }
    .risk-high { color: #d62728; font-weight: bold; }
    .risk-medium { color: #ff7f0e; font-weight: bold; }
    .risk-low { color: #2ca02c; font-weight: bold; }
    .intervention-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load student data and cache it"""
    try:
        data_dir = Path("data/processed")
        df = pd.read_csv(data_dir / "student_features_engineered.csv")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_resource
def load_intervention_system():
    """Load intervention system and cache it"""
    try:
        return InterventionRecommendationSystem()
    except Exception as e:
        st.error(f"Error loading intervention system: {e}")
        return None

def create_risk_gauge(risk_score, title):
    """Create a risk gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def display_intervention_recommendations(recommendations):
    """Display intervention recommendations in a formatted way"""
    for rec in recommendations:
        if rec['risk_level'] != 'Low Risk':
            with st.expander(f"🚨 Student {rec['student_id']} - {rec['risk_level']} ({rec['priority']} Priority)"):
                st.write(f"**Risk Score:** {rec['risk_score']:.3f}")
                
                for i, intervention in enumerate(rec['interventions'], 1):
                    st.markdown(f"""
                    <div class="intervention-card">
                        <h4>📋 {intervention['title']}</h4>
                        <p><strong>Type:</strong> {intervention['type']}</p>
                        <p><strong>Timeline:</strong> {intervention['timeline']}</p>
                        <p><strong>Resources:</strong> {', '.join(intervention['resources'])}</p>
                        <p><strong>Cost:</strong> {intervention['cost']}</p>
                    </div>
                    """, unsafe_allow_html=True)

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Student Success Prediction Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load data and systems
    df = load_data()
    intervention_system = load_intervention_system()
    
    if df is None or intervention_system is None:
        st.error("Failed to load required components. Please check your setup.")
        return
    
    # Sidebar filters
    st.sidebar.header("📋 Dashboard Filters")
    
    # Course selection
    courses = df['code_module'].unique()
    selected_course = st.sidebar.selectbox("Select Course", ['All'] + list(courses))
    
    # Presentation selection
    presentations = df['code_presentation'].unique()
    selected_presentation = st.sidebar.selectbox("Select Presentation", ['All'] + list(presentations))
    
    # Filter data
    filtered_df = df.copy()
    if selected_course != 'All':
        filtered_df = filtered_df[filtered_df['code_module'] == selected_course]
    if selected_presentation != 'All':
        filtered_df = filtered_df[filtered_df['code_presentation'] == selected_presentation]
    
    # Generate risk assessments
    risk_assessments = intervention_system.assess_student_risk(filtered_df)
    combined_data = pd.concat([filtered_df.reset_index(drop=True), risk_assessments], axis=1)
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎯 At-Risk Students", "💡 Interventions", "📊 Analytics"])
    
    with tab1:
        st.header("📈 Course Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Students", len(filtered_df))
            
        with col2:
            high_risk = len(risk_assessments[risk_assessments['risk_category'] == 'High Risk'])
            st.metric("High Risk Students", high_risk, delta=f"{high_risk/len(filtered_df)*100:.1f}%")
            
        with col3:
            avg_risk = risk_assessments['risk_score'].mean()
            st.metric("Average Risk Score", f"{avg_risk:.3f}")
            
        with col4:
            success_rate = (filtered_df['final_result'].isin(['Pass', 'Distinction']).sum() / len(filtered_df) * 100)
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Risk distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Risk Distribution")
            risk_dist = risk_assessments['risk_category'].value_counts()
            fig = px.pie(values=risk_dist.values, names=risk_dist.index, 
                        color_discrete_map={'Low Risk': 'green', 'Medium Risk': 'orange', 'High Risk': 'red'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Risk Score Distribution")
            fig = px.histogram(risk_assessments, x='risk_score', nbins=30, 
                             title="Distribution of Risk Scores")
            fig.add_vline(x=0.5, line_dash="dash", line_color="red", 
                         annotation_text="Intervention Threshold")
            st.plotly_chart(fig, use_container_width=True)
        
        # Outcome vs Risk
        st.subheader("Actual Outcomes vs Predicted Risk")
        outcome_risk = combined_data.groupby(['final_result', 'risk_category']).size().reset_index(name='count')
        fig = px.bar(outcome_risk, x='final_result', y='count', color='risk_category',
                    color_discrete_map={'Low Risk': 'green', 'Medium Risk': 'orange', 'High Risk': 'red'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("🎯 At-Risk Students")
        
        # Filter at-risk students
        at_risk_students = combined_data[combined_data['needs_intervention'] == True].copy()
        at_risk_students = at_risk_students.sort_values('risk_score', ascending=False)
        
        st.write(f"**Found {len(at_risk_students)} students needing intervention**")
        
        if len(at_risk_students) > 0:
            # Top 10 highest risk students
            st.subheader("🚨 Highest Risk Students")
            
            top_risk = at_risk_students.head(10)
            
            for idx, student in top_risk.iterrows():
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.write(f"**Student {student['id_student']}**")
                    risk_class = 'risk-high' if student['risk_score'] > 0.7 else 'risk-medium'
                    st.markdown(f'<p class="{risk_class}">Risk: {student["risk_score"]:.3f}</p>', 
                               unsafe_allow_html=True)
                
                with col2:
                    # Key risk factors
                    st.write("**Key Risk Factors:**")
                    if student['early_avg_score'] < 50:
                        st.write("• Low assessment scores")
                    if student['early_total_clicks'] < 500:
                        st.write("• Low VLE engagement")
                    if student['early_submission_rate'] < 0.8:
                        st.write("• Poor submission rate")
                    if student['num_of_prev_attempts'] > 0:
                        st.write("• Previous attempts")
                
                with col3:
                    gauge_fig = create_risk_gauge(student['risk_score'], "Risk Level")
                    st.plotly_chart(gauge_fig, use_container_width=True)
                
                st.markdown("---")
        else:
            st.success("🎉 No students currently at high risk!")
    
    with tab3:
        st.header("💡 Intervention Recommendations")
        
        # Select number of students to analyze
        num_students = st.slider("Number of students to analyze", 1, 50, 10)
        
        # Get top at-risk students
        at_risk_sample = combined_data[combined_data['needs_intervention'] == True].head(num_students)
        
        if len(at_risk_sample) > 0:
            st.write(f"**Generating recommendations for {len(at_risk_sample)} students...**")
            
            # Generate recommendations
            recommendations = intervention_system.get_intervention_recommendations(at_risk_sample)
            
            # Display recommendations
            display_intervention_recommendations(recommendations)
            
            # Summary statistics
            st.subheader("📊 Intervention Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                critical_count = sum(1 for r in recommendations if r['priority'] == 'Critical')
                st.metric("Critical Priority", critical_count)
            
            with col2:
                high_count = sum(1 for r in recommendations if r['priority'] == 'High')
                st.metric("High Priority", high_count)
            
            with col3:
                total_interventions = sum(len(r['interventions']) for r in recommendations)
                st.metric("Total Interventions", total_interventions)
        else:
            st.info("No students currently need interventions.")
    
    with tab4:
        st.header("📊 Advanced Analytics")
        
        # Feature correlations with risk
        st.subheader("Feature Correlation with Risk")
        feature_cols = [col for col in combined_data.columns if col.startswith('early_') or col.endswith('_encoded')]
        
        if len(feature_cols) > 0:
            correlations = combined_data[feature_cols + ['risk_score']].corr()['risk_score'].sort_values(ascending=False)
            
            fig = px.bar(x=correlations.values[1:11], y=correlations.index[1:11], 
                        orientation='h', title="Top 10 Features Correlated with Risk")
            st.plotly_chart(fig, use_container_width=True)
        
        # Engagement vs Performance
        st.subheader("Engagement vs Assessment Performance")
        if 'early_total_clicks' in combined_data.columns and 'early_avg_score' in combined_data.columns:
            fig = px.scatter(combined_data, x='early_total_clicks', y='early_avg_score', 
                           color='risk_category', size='risk_score',
                           color_discrete_map={'Low Risk': 'green', 'Medium Risk': 'orange', 'High Risk': 'red'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Time series analysis placeholder
        st.subheader("📈 Trend Analysis")
        st.info("Time series analysis of student progress would be implemented here with more temporal data.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>📊 Student Success Prediction Dashboard | Built with Streamlit & Machine Learning</p>
        <p>🎯 Helping educators identify at-risk students and provide timely interventions</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()