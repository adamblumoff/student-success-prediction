#!/usr/bin/env python3
"""
Simple Streamlit Dashboard for Student Success Prediction
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Student Success Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/student_features_engineered.csv")
    df = df.fillna(0)
    return df

# Main app
def main():
    st.title("🎓 Student Success Prediction Dashboard")
    
    # Load data
    df = load_data()
    
    # Simple metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Students", len(df))
    
    with col2:
        success_rate = (df['final_result'].isin(['Pass', 'Distinction']).sum() / len(df) * 100)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        withdrawal_rate = (df['final_result'] == 'Withdrawn').sum() / len(df) * 100
        st.metric("Withdrawal Rate", f"{withdrawal_rate:.1f}%")
    
    # Outcome distribution
    st.subheader("📊 Student Outcomes")
    outcome_counts = df['final_result'].value_counts()
    fig = px.pie(values=outcome_counts.values, names=outcome_counts.index)
    st.plotly_chart(fig, use_container_width=True)
    
    # Course analysis
    st.subheader("📚 Course Analysis")
    course_outcomes = df.groupby('code_module')['final_result'].value_counts().unstack(fill_value=0)
    fig = px.bar(course_outcomes, title="Outcomes by Course")
    st.plotly_chart(fig, use_container_width=True)
    
    # Sample students
    st.subheader("👥 Sample Students")
    sample_students = df.sample(10)[['id_student', 'final_result', 'early_avg_score', 'early_total_clicks']]
    st.dataframe(sample_students)

if __name__ == "__main__":
    main()