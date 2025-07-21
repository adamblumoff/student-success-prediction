#!/usr/bin/env python3
"""
CLI Dashboard for Student Success Prediction

Command-line interface to demonstrate the student success prediction system
without requiring port forwarding or web browser access.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import time
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))
from models.intervention_system import InterventionRecommendationSystem

def print_header():
    """Print dashboard header"""
    print("=" * 80)
    print("🎓 STUDENT SUCCESS PREDICTION DASHBOARD")
    print("=" * 80)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def load_and_process_data():
    """Load and preprocess student data"""
    try:
        data_dir = Path("data/processed")
        df = pd.read_csv(data_dir / "student_features_engineered.csv")
        
        # Handle missing values
        df['registration_delay'] = df['registration_delay'].fillna(df['registration_delay'].median())
        df = df.fillna(0)
        
        print(f"✅ Loaded {len(df):,} student records")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def show_overview(df, risk_assessments):
    """Show course overview metrics"""
    print("\n📊 COURSE OVERVIEW")
    print("-" * 50)
    
    # Key metrics
    total_students = len(df)
    high_risk = len(risk_assessments[risk_assessments['risk_category'] == 'High Risk'])
    medium_risk = len(risk_assessments[risk_assessments['risk_category'] == 'Medium Risk'])
    low_risk = len(risk_assessments[risk_assessments['risk_category'] == 'Low Risk'])
    
    avg_risk = risk_assessments['risk_score'].mean()
    success_rate = (df['final_result'].isin(['Pass', 'Distinction']).sum() / len(df) * 100)
    
    print(f"👥 Total Students:      {total_students:,}")
    print(f"🚨 High Risk:           {high_risk:,} ({high_risk/total_students*100:.1f}%)")
    print(f"⚠️  Medium Risk:         {medium_risk:,} ({medium_risk/total_students*100:.1f}%)")
    print(f"✅ Low Risk:            {low_risk:,} ({low_risk/total_students*100:.1f}%)")
    print(f"📈 Average Risk Score:  {avg_risk:.3f}")
    print(f"🎯 Success Rate:        {success_rate:.1f}%")
    
    # Risk distribution
    print(f"\n📈 RISK DISTRIBUTION")
    print("-" * 30)
    risk_dist = risk_assessments['risk_category'].value_counts()
    for category, count in risk_dist.items():
        percentage = count / len(risk_assessments) * 100
        bar = "█" * int(percentage / 2)
        print(f"{category:12s}: {count:4d} ({percentage:5.1f}%) {bar}")

def show_at_risk_students(df, risk_assessments, limit=10):
    """Show highest risk students"""
    print(f"\n🚨 TOP {limit} HIGHEST RISK STUDENTS")
    print("-" * 60)
    
    # Get at-risk students
    at_risk = risk_assessments[risk_assessments['needs_intervention'] == True]
    at_risk_with_data = pd.concat([df.reset_index(drop=True), risk_assessments], axis=1)
    at_risk_with_data = at_risk_with_data[at_risk_with_data['needs_intervention'] == True]
    at_risk_with_data = at_risk_with_data.sort_values('risk_score', ascending=False)
    
    if len(at_risk_with_data) == 0:
        print("🎉 No students currently at high risk!")
        return
    
    print(f"Found {len(at_risk_with_data)} students needing intervention\n")
    
    for idx, (_, student) in enumerate(at_risk_with_data.head(limit).iterrows(), 1):
        print(f"{idx:2d}. Student {student['id_student']}")
        print(f"    Risk Score: {student['risk_score']:.3f} ({student['risk_category']})")
        print(f"    Final Result: {student['final_result']}")
        
        # Key risk factors
        risk_factors = []
        if student['early_avg_score'] < 50:
            risk_factors.append("Low assessment scores")
        if student['early_total_clicks'] < 500:
            risk_factors.append("Low VLE engagement")
        if student['early_submission_rate'] < 0.8:
            risk_factors.append("Poor submission rate")
        if student['num_of_prev_attempts'] > 0:
            risk_factors.append("Previous attempts")
        
        if risk_factors:
            print(f"    Risk Factors: {', '.join(risk_factors)}")
        print()

def show_intervention_recommendations(intervention_system, df, risk_assessments, limit=5):
    """Show intervention recommendations"""
    print(f"\n💡 INTERVENTION RECOMMENDATIONS (Top {limit})")
    print("-" * 60)
    
    # Get top at-risk students
    at_risk_with_data = pd.concat([df.reset_index(drop=True), risk_assessments], axis=1)
    at_risk_sample = at_risk_with_data[at_risk_with_data['needs_intervention'] == True].head(limit)
    
    if len(at_risk_sample) == 0:
        print("🎉 No students currently need interventions!")
        return
    
    # Generate recommendations
    recommendations = intervention_system.get_intervention_recommendations(at_risk_sample)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. 🎓 Student {rec['student_id']} - {rec['risk_level']} ({rec['priority']} Priority)")
        print(f"   Risk Score: {rec['risk_score']:.3f}")
        print(f"   Interventions:")
        
        for j, intervention in enumerate(rec['interventions'], 1):
            print(f"     {j}. {intervention['title']}")
            print(f"        Timeline: {intervention['timeline']}")
            print(f"        Resources: {', '.join(intervention['resources'])}")
            print(f"        Cost: {intervention['cost']}")
        print()

def show_feature_analysis(df, risk_assessments):
    """Show feature correlation analysis"""
    print("\n📊 FEATURE ANALYSIS")
    print("-" * 40)
    
    # Combine data
    combined_data = pd.concat([df.reset_index(drop=True), risk_assessments], axis=1)
    
    # Feature correlations with risk
    feature_cols = [col for col in combined_data.columns if col.startswith('early_') or col.endswith('_encoded')]
    
    if len(feature_cols) > 0:
        correlations = combined_data[feature_cols + ['risk_score']].corr()['risk_score'].sort_values(ascending=False)
        
        print("Top 10 features correlated with risk:")
        for i, (feature, corr) in enumerate(correlations.head(11).items(), 1):
            if feature != 'risk_score':  # Skip self-correlation
                print(f"{i:2d}. {feature:25s}: {corr:6.3f}")
    
    # Course-wise analysis
    print(f"\n📚 COURSE-WISE ANALYSIS")
    print("-" * 30)
    course_risk = combined_data.groupby('code_module').agg({
        'risk_score': 'mean',
        'needs_intervention': 'sum'
    }).round(3)
    
    for course, data in course_risk.iterrows():
        print(f"{course}: Avg Risk {data['risk_score']:.3f}, Need Intervention: {int(data['needs_intervention'])}")

def interactive_menu():
    """Show interactive menu"""
    print("\n🎮 INTERACTIVE OPTIONS")
    print("-" * 30)
    print("1. 📊 Show detailed course overview")
    print("2. 🚨 Show all at-risk students")
    print("3. 💡 Generate intervention report")
    print("4. 📈 Show feature analysis")
    print("5. 🔄 Refresh data")
    print("6. ❌ Exit")
    
    choice = input("\nSelect option (1-6): ").strip()
    return choice

def main():
    """Main CLI dashboard function"""
    print_header()
    
    # Load data and systems
    df = load_and_process_data()
    if df is None:
        return
    
    try:
        intervention_system = InterventionRecommendationSystem()
        print("✅ Intervention system loaded successfully")
    except Exception as e:
        print(f"❌ Error loading intervention system: {e}")
        return
    
    # Generate risk assessments
    print("🔄 Generating risk assessments...")
    risk_assessments = intervention_system.assess_student_risk(df)
    print("✅ Risk assessments completed")
    
    # Show main dashboard
    show_overview(df, risk_assessments)
    show_at_risk_students(df, risk_assessments, limit=5)
    show_intervention_recommendations(intervention_system, df, risk_assessments, limit=3)
    
    # Interactive menu
    while True:
        choice = interactive_menu()
        
        if choice == '1':
            show_overview(df, risk_assessments)
            show_feature_analysis(df, risk_assessments)
        elif choice == '2':
            show_at_risk_students(df, risk_assessments, limit=20)
        elif choice == '3':
            print("\n📝 Generating comprehensive intervention report...")
            at_risk_sample = pd.concat([df.reset_index(drop=True), risk_assessments], axis=1)
            at_risk_sample = at_risk_sample[at_risk_sample['needs_intervention'] == True].head(10)
            report = intervention_system.generate_intervention_report(at_risk_sample)
            print(report)
        elif choice == '4':
            show_feature_analysis(df, risk_assessments)
        elif choice == '5':
            print("🔄 Refreshing data...")
            df = load_and_process_data()
            if df is not None:
                risk_assessments = intervention_system.assess_student_risk(df)
                show_overview(df, risk_assessments)
        elif choice == '6':
            print("\n👋 Thanks for using the Student Success Prediction Dashboard!")
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()