# Student Success Prediction MVP

## Quick Start

1. **Start the MVP application:**
   ```bash
   python3 run_mvp.py
   ```

2. **Open your web browser and go to:**
   ```
   http://localhost:8001
   ```

3. **Try the demo:**
   - Click "Load Sample Data" to see the system in action
   - Or upload your own CSV file with student data

## Features

### For Educators
- **Simple Interface**: Clean, focused design for busy educators
- **Risk Identification**: Automatically identifies students at risk of dropping out
- **Actionable Insights**: Specific intervention recommendations for each student
- **Progress Tracking**: Track which interventions you've tried and their effectiveness

### Technical Features
- **Machine Learning**: 89.4% AUC accuracy using gradient boosting
- **Real-time Analysis**: Process student data instantly
- **SQLite Database**: Simple, reliable data storage
- **Responsive Design**: Works on desktop and mobile devices

## Using Your Own Data

### Required CSV Format
Your CSV file should have at least these columns:
- `id_student` - Unique student identifier

### Optional Columns (for better predictions)
- `early_avg_score` - Average assessment score
- `early_total_clicks` - Online engagement clicks
- `early_active_days` - Days active in the system
- `studied_credits` - Number of credits enrolled

### Example Upload Process
1. Click the upload area or drag your CSV file
2. Wait for analysis (usually < 5 seconds)
3. Review at-risk students in the results
4. Click on any student for detailed recommendations
5. Track your intervention efforts

## Understanding Results

### Risk Categories
- **High Risk** (Red): Immediate intervention needed
- **Medium Risk** (Orange): Monitor closely, proactive support
- **Low Risk** (Green): Regular check-ins sufficient

### Intervention Types
- **Critical**: Immediate 1-on-1 meetings, advisor connections
- **High**: Check-in emails, tutoring support
- **Medium**: Study groups, additional resources

## Troubleshooting

### Common Issues
1. **CSV upload fails**: Ensure file has `id_student` column
2. **No data shows**: Try the "Load Sample Data" button first
3. **Page won't load**: Check that port 8001 is available

### Getting Help
- API documentation: http://localhost:8001/docs
- Health check: http://localhost:8001/health

## Next Steps

This MVP demonstrates core functionality. For production deployment:
1. Set up PostgreSQL database
2. Add user authentication
3. Configure for your institution's data format
4. Scale for larger student populations

---

**Built for educators who want to help every student succeed.** 🎓