# Security Guide for Student Success Prediction System

## Overview

This document outlines the security measures implemented in the Student Success Prediction System and provides guidance for secure deployment and operation.

## Security Features Implemented

### 🔐 Authentication & Authorization

**Multi-tier API Key System**
- **Admin Access**: Full system access including configuration changes
- **Teacher Access**: Can upload files and analyze student data
- **Read-only Access**: Can view sample data and system status

**JWT Token Support**
- Secure token-based authentication
- Configurable expiration times
- IP-based validation (optional)

**Brute Force Protection**
- Failed authentication attempt tracking
- Automatic IP lockout after 5 failed attempts
- 15-minute lockout duration

### 🛡️ File Upload Security

**Comprehensive File Validation**
- File size limits (10MB maximum)
- MIME type validation using python-magic
- Filename sanitization and path traversal prevention
- CSV structure validation (max 10,000 rows, 100 columns)

**CSV Injection Prevention**
- Detection of formula injection patterns (`=`, `+`, `-`, `@`)
- Automatic sanitization of dangerous content
- Removal of script tags and command injection attempts
- Safe handling of suspicious cells

**Secure File Processing**
- Content hash calculation for audit trails
- Temporary file handling with automatic cleanup
- Unicode encoding validation and fallback

### 🚦 Rate Limiting & DDoS Protection

**Endpoint-Specific Rate Limits**
- Default: 100 requests per hour
- File uploads: 10 per hour
- Data analysis: 50 per hour
- Authentication: 5 attempts per 5 minutes

**Client Identification**
- IP-based tracking with User-Agent fingerprinting
- Support for X-Forwarded-For headers (proxy support)
- Sliding window rate limiting

### 🌐 Web Security

**Security Headers**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` for HTTPS
- `Content-Security-Policy` to prevent XSS
- `Referrer-Policy` for privacy

**CORS Configuration**
- Configurable allowed origins (no wildcard in production)
- Restricted HTTP methods (GET, POST only)
- Credential support with proper origin validation

**Host Validation**
- Trusted host middleware
- Configurable allowed hosts list

### 🗄️ Database Security

**SQL Injection Prevention**
- SQLAlchemy ORM with parameterized queries
- No direct SQL string concatenation
- Input validation before database operations

**Database Access Control**
- Connection pooling with limits
- Prepared statements for all queries
- Transaction management with rollback on errors

### 📝 Logging & Monitoring

**Security Event Logging**
- Failed authentication attempts with IP tracking
- File upload attempts and validation failures
- Rate limit violations
- Suspicious activity detection

**Data Privacy in Logs**
- No sensitive data (passwords, tokens) in logs
- Sanitized filenames and content descriptions
- Hash-based file identification

### 🔍 Input Validation

**Comprehensive Data Validation**
- Pydantic models for API request validation
- Type checking and range validation
- String length limits and pattern matching
- Nested object validation

**Gradebook Processing Security**
- Format detection without code execution
- Safe pandas operations with error handling
- Memory usage limits for large datasets
- Timeout protection for processing operations

## Security Configuration

### Environment Variables

Copy `.env.security` to `.env` and configure:

```bash
# Essential security settings
JWT_SECRET_KEY=your-256-bit-secret-key
ADMIN_API_KEY=admin-secure-random-key
TEACHER_API_KEY=teacher-secure-random-key
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com
DEVELOPMENT_MODE=false
```

### Production Deployment Checklist

#### 🔴 Critical (Must Complete Before Production)

- [ ] Generate strong, unique API keys (32+ characters)
- [ ] Set secure JWT secret key (256-bit minimum)
- [ ] Configure ALLOWED_HOSTS and ALLOWED_ORIGINS
- [ ] Set DEVELOPMENT_MODE=false
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Use strong database credentials
- [ ] Remove default/demo credentials

#### 🟡 Important (Complete Within 1 Week)

- [ ] Set up security monitoring and alerting
- [ ] Configure log aggregation and analysis
- [ ] Implement database backups with encryption
- [ ] Set up firewall rules and network segmentation
- [ ] Configure reverse proxy (Nginx) with security headers
- [ ] Set up vulnerability scanning

#### 🟢 Recommended (Complete Within 1 Month)

- [ ] Implement Web Application Firewall (WAF)
- [ ] Set up intrusion detection system (IDS)
- [ ] Configure security incident response procedures
- [ ] Implement data encryption at rest
- [ ] Set up penetration testing schedule
- [ ] Create security training program

## Security Best Practices

### For Developers

1. **Never commit secrets** to version control
2. **Validate all input** at API boundaries
3. **Use parameterized queries** for database operations
4. **Log security events** without exposing sensitive data
5. **Keep dependencies updated** with security patches
6. **Follow principle of least privilege** for access control

### For System Administrators

1. **Regular security updates** for OS and dependencies
2. **Network segmentation** between components
3. **Monitoring and alerting** for suspicious activities
4. **Regular backups** with tested restore procedures
5. **Access logging and audit trails**
6. **Incident response plan** and procedures

### For End Users

1. **Use strong, unique API keys**
2. **Rotate keys regularly** (quarterly recommended)
3. **Monitor usage logs** for suspicious activity
4. **Report security incidents** immediately
5. **Keep client applications updated**

## Vulnerability Reporting

If you discover a security vulnerability, please:

1. **Do not** create a public GitHub issue
2. **Email** security@yourdomain.com with details
3. **Include** steps to reproduce the issue
4. **Allow** reasonable time for response and fix
5. **Follow** responsible disclosure principles

## Security Monitoring

### Key Metrics to Monitor

- Failed authentication attempts per IP
- Rate limit violations and patterns
- File upload sizes and types
- Database query patterns and performance
- Error rates and exception patterns
- Memory and CPU usage anomalies

### Alerting Thresholds

- **Critical**: Multiple failed auth attempts from same IP
- **Critical**: Large file uploads outside business hours
- **Warning**: Unusual traffic patterns or volume
- **Warning**: High error rates or slow response times
- **Info**: New IP addresses accessing the system

## Compliance Considerations

### Data Protection

- **FERPA Compliance**: Educational records protection
- **GDPR Considerations**: EU student data handling
- **COPPA Requirements**: Under-13 student data protection
- **State Privacy Laws**: Local educational privacy requirements

### Audit Requirements

- **Access Logging**: Who accessed what data when
- **Data Retention**: How long data is stored
- **Data Deletion**: Secure data removal procedures
- **Change Tracking**: System configuration changes

## Security Testing

### Automated Testing

- **Dependency scanning**: `pip audit` for vulnerable packages
- **Static code analysis**: Security linting and code review
- **Unit tests**: Security function validation
- **Integration tests**: End-to-end security flow testing

### Manual Testing

- **Penetration testing**: Quarterly external assessment
- **Code review**: Security-focused peer review
- **Configuration review**: Security setting validation
- **Incident simulation**: Response procedure testing

## Updates and Maintenance

### Regular Tasks

- **Weekly**: Dependency update review
- **Monthly**: Security log analysis
- **Quarterly**: Penetration testing
- **Annually**: Full security audit

### Emergency Procedures

1. **Immediate**: Disable affected services
2. **Within 1 hour**: Assess impact and containment
3. **Within 4 hours**: Implement fixes and patches
4. **Within 24 hours**: Complete incident report
5. **Within 1 week**: Update procedures and training

---

**Remember**: Security is an ongoing process, not a one-time implementation. Regular reviews and updates are essential for maintaining a secure system.

For questions or concerns about security, contact: security@yourdomain.com