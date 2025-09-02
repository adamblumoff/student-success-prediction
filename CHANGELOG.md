# Changelog

All notable changes to the Student Success Prediction System are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Production] - 2025-09-01

### 🚀 Deployment
- Deployed to Railway with PostgreSQL database
- Configured auto-deployment on push to master branch
- Set up comprehensive environment variables for production

### 🔒 Security Enhancements
- Implemented `SecurityManager` class for environment-specific security policies
- Fixed Railway HTTPS detection to prevent production startup errors
- Added comprehensive GitHub Actions CI pipeline replacing bypassable pre-push hooks
- Ensured FERPA compliance with encryption and audit logging
- All security tests passing with comprehensive validation

### 🐛 Bug Fixes
- **Duplicate Student Prevention**: Added database-level `UniqueConstraint` on `(institution_id, student_id)`
- **Sample Data Loading**: Simplified logic by removing 75+ lines of complex duplicate cleanup code
- **CSV Re-uploads**: Fixed to use PostgreSQL `ON CONFLICT DO NOTHING` for proper upserts
- **Missing Dependencies**: Added `werkzeug>=2.3.0`, `cryptography>=41.0.0`, and `bcrypt>=4.0.0`
- **Database Test**: Updated to expect `IntegrityError` for duplicate attempts

### 🔧 CI/CD Improvements
- GPT AI and integration tests now run on all branches (not just dev/PR)
- Upgraded deprecated GitHub Actions from v3 to v4
- Added proper environment variables for test execution
- Fixed Python path issues in CI scripts

### 📊 Demo Reliability
- Sample data now loads consistently every time
- CSV files can be re-uploaded safely without creating duplicates
- Database state remains clean and consistent
- Demo presentations are 100% reliable

## [Development] - 2025-08-31

### ✨ Features
- GPT-enhanced AI insights with database persistence
- Smart caching system with automatic invalidation
- Real-time notification system for at-risk students
- Bulk intervention management capabilities

### 🎯 Model Performance
- K-12 Ultra-Advanced Model: 81.5% AUC (Neural Network with Stacking Ensemble)
- K-12 Advanced Model: 77.7% AUC (Extra Trees with Feature Selection)
- Original K-12 Model: 74.3% AUC (Logistic Regression)

### 🏗️ Architecture
- Modular API structure with focused routers
- Hybrid database support (PostgreSQL/SQLite)
- Async database operations for performance
- Comprehensive audit logging system

## [MVP] - 2025-08-30

### 🎓 Initial Release
- K-12 student success prediction system
- Canvas LMS and generic CSV support
- Explainable AI with risk factor identification
- Intervention tracking and management
- Web-based educator interface

### 📚 Core Features
- File upload and processing (10MB limit)
- Risk prediction with confidence scores
- Individual student explanations
- Dashboard analytics
- API documentation at `/docs`

## Notes

### Versioning Strategy
- **Production**: Stable releases deployed to Railway
- **Development**: Active development with feature additions
- **MVP**: Minimum viable product for educational demonstration

### Breaking Changes
- Database schema now enforces unique constraint on `(institution_id, student_id)`
- Security policies are strictly enforced in production environment
- HTTPS is required for production deployments

### Migration Notes
For existing deployments:
1. Update environment variables in Railway dashboard
2. Ensure `werkzeug` dependency is installed
3. Database migration will automatically apply unique constraints
4. Review and update any custom student import logic