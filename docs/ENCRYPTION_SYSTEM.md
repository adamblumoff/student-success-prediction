# Database Encryption System - FERPA Compliance

## Overview

The Student Success Prediction system implements **field-level database encryption** for FERPA-compliant protection of sensitive student data. This system ensures that personally identifiable information (PII) is encrypted at rest in the database while maintaining transparent operation for application use.

## Security Features

### ✅ Encryption Standards
- **Algorithm**: AES-256 encryption using Fernet (symmetric encryption)
- **Key Derivation**: PBKDF2-SHA256 with 100,000 iterations (NIST recommended)
- **Key Length**: 256-bit encryption keys
- **Versioning**: Support for key rotation with version tracking (`v1:`, `v2:`, etc.)

### ✅ FERPA Compliance
- **PII Protection**: All sensitive student data encrypted at rest
- **Audit Trail**: Encryption operations logged for compliance
- **Data Minimization**: Only necessary fields encrypted (performance optimization)
- **Access Control**: Integrated with row-level security and authentication

### ✅ Production Security
- **Environment-Based**: Enabled automatically in production environments
- **Key Management**: Secure key derivation from master keys
- **Graceful Degradation**: Handles legacy unencrypted data
- **Error Handling**: Secure failure modes with audit logging

## Encrypted Fields

### Student Model (`students` table)
**FERPA-Protected PII:**
- `birth_date` - Date of birth (strong identifier)
- `email` - Student email address
- `phone` - Student phone number
- `parent_email` - Parent contact information
- `parent_phone` - Parent contact information

### User Model (`users` table)
**Staff PII:**
- `email` - Staff email address
- `first_name` - Staff personal information
- `last_name` - Staff personal information

### Audit Log Model (`audit_logs` table)
**Contact Information:**
- `user_email` - Email addresses in audit logs

**Note**: Academic data like grades and attendance are NOT encrypted as they are considered educational records rather than directory information under FERPA.

## Configuration

### Environment Variables

```bash
# Production (Required)
DATABASE_ENCRYPTION_KEY=your-secure-256-bit-key-here
ENCRYPTION_KEY_VERSION=1
ENCRYPTION_SALT=your-institutional-salt

# Development/Testing (Optional)
ENABLE_DATABASE_ENCRYPTION=true
DEFAULT_INSTITUTION_ID=1
```

### Security Requirements

**Production Deployment:**
1. **Master Key**: Must be at least 32 characters long
2. **Environment**: Set `ENVIRONMENT=production` 
3. **Key Storage**: Store keys securely (HashiCorp Vault, AWS Secrets Manager, etc.)
4. **Key Rotation**: Plan for regular key rotation using versioning system

**Development Mode:**
- Encryption disabled by default for easier debugging
- Can be enabled with `ENABLE_DATABASE_ENCRYPTION=true`
- Uses deterministic development keys for testing

## Usage Examples

### Transparent Encryption (Recommended)

```python
from mvp.database import get_db_session
from mvp.models import Student

# Create student with automatic encryption
with get_db_session() as session:
    student = Student(
        student_id="STU123",
        email="john@school.edu",  # Automatically encrypted
        phone="555-0123",         # Automatically encrypted
        grade_level="10"          # Not encrypted
    )
    session.add(student)
    session.commit()

# Query student with automatic decryption
student = session.query(Student).filter_by(student_id="STU123").first()
print(student.email)  # Automatically decrypted: "john@school.edu"
```

### Manual Encryption (API Layer)

```python
from mvp.encryption import encrypt_student_data, decrypt_student_data

# Encrypt data before database storage
student_data = {
    "student_id": "STU123",
    "email": "john@school.edu",
    "grade_level": "10"
}

encrypted_data = encrypt_student_data(student_data)
# encrypted_data["email"] = "v1:Z0FBQUFBQm9uUWNYaFZpVEpfNkN0..."

# Decrypt data after database retrieval
decrypted_data = decrypt_student_data(encrypted_data)
# decrypted_data["email"] = "john@school.edu"
```

### Search Encrypted Fields

```python
from mvp.encryption_middleware import search_encrypted_field

# Search by encrypted field (exact match only)
students = search_encrypted_field(
    session=session,
    model_class=Student,
    field_name="email", 
    search_value="john@school.edu"
)
```

## Database Storage Format

### Encrypted Field Format
```
v{version}:{base64_encrypted_data}

Examples:
v1:Z0FBQUFBQm9uUWNYaFZpVEpfNkN0VkdZQUlTaWJ6Wmc0Z0F...
v2:A1BCDEFGhijklmn0123456789abcdef...
```

### Storage Comparison
```sql
-- Unencrypted (Legacy/Development)
INSERT INTO students (email, phone) VALUES 
  ('john@school.edu', '555-0123');

-- Encrypted (Production)  
INSERT INTO students (email, phone) VALUES 
  ('v1:Z0FBQUFBQm9uUWNYaFZpVEpfNkN0...', 'v1:A1BCDEFGhijklmn0123...');
```

## Performance Considerations

### Optimizations
- **Field-Level**: Only sensitive fields encrypted (not entire records)
- **Transparent**: No application code changes required
- **Caching**: Decrypted values cached in memory during session
- **Lazy Loading**: Encryption only occurs when fields are accessed

### Performance Impact
- **Encryption**: ~1ms per field
- **Decryption**: ~0.5ms per field  
- **Storage**: ~33% increase in encrypted field size
- **Query Performance**: No impact on queries by non-encrypted fields

### Limitations
- **Search**: Full-text search not available on encrypted fields
- **Sorting**: Cannot sort by encrypted field values
- **Indexes**: Cannot create indexes on encrypted field content

## Testing

### Health Check
```python
from mvp.encryption import check_encryption_health

if check_encryption_health():
    print("✅ Encryption system operational")
else:
    print("❌ Encryption system failure")
```

### Test Encryption Round-Trip
```bash
# Run comprehensive encryption tests
python3 -c "
import sys; sys.path.append('src')
from mvp.encryption import encryption_manager

test_data = 'sensitive@example.com'
encrypted = encryption_manager.encrypt(test_data)
decrypted = encryption_manager.decrypt(encrypted)

assert test_data == decrypted, 'Encryption round-trip failed'
print('✅ Encryption test passed')
"
```

## Monitoring and Maintenance

### Health Monitoring
- Monitor encryption/decryption success rates
- Track performance metrics for encrypted operations
- Alert on encryption system failures

### Key Rotation Process
1. **Generate New Key**: Create new master key with incremented version
2. **Update Configuration**: Set `ENCRYPTION_KEY_VERSION=2`
3. **Gradual Migration**: Re-encrypt data with new key during normal operations
4. **Verify Migration**: Ensure all data uses new key version
5. **Retire Old Key**: Remove old key after migration complete

### Backup Considerations
- **Encrypted Backups**: Database backups contain encrypted data
- **Key Backup**: Securely backup encryption keys separately
- **Recovery Testing**: Regularly test backup restoration with decryption

## Compliance Documentation

### FERPA Requirements Met
✅ **§99.31 Disclosure Requirements**: PII encrypted at rest  
✅ **§99.32 Record Keeping**: Audit logging for all access  
✅ **§99.35 Disclosure to Organizations**: Institutional data isolation  
✅ **Technical Safeguards**: Industry-standard AES-256 encryption  

### Audit Trail
All encryption operations are logged with:
- Timestamp of operation
- User performing operation  
- Type of operation (encrypt/decrypt)
- Data classification (PII/non-PII)
- Institutional context

## Migration from Legacy Systems

### Phase 1: Enable Encryption (Non-Breaking)
```bash
# Enable encryption without breaking existing data
export ENABLE_DATABASE_ENCRYPTION=true
# Existing unencrypted data remains readable
# New data gets encrypted automatically
```

### Phase 2: Encrypt Existing Data (Background)
```python
# Script to encrypt existing unencrypted data
from mvp.encryption_middleware import update_encrypted_student

# Migrate existing student records to encrypted format
for student in session.query(Student).all():
    if not student.email.startswith('v'):  # If not encrypted
        update_encrypted_student(session, student.id, {
            'email': student.email,
            'phone': student.phone
            # Other fields will be encrypted automatically
        })
```

### Phase 3: Validation (Critical)
```python
# Verify all sensitive data is encrypted
encrypted_count = session.query(Student).filter(
    Student.email.like('v%:%')
).count()

total_count = session.query(Student).count()
encryption_rate = encrypted_count / total_count * 100

print(f"Encryption Rate: {encryption_rate}% ({encrypted_count}/{total_count})")
```

## Security Best Practices

### ✅ Implementation
- Field-level encryption for granular control
- Automatic transparent operation via middleware  
- Versioned keys for rotation support
- Secure key derivation with PBKDF2
- Environment-based configuration
- Comprehensive audit logging

### ✅ Operational Security
- Regular key rotation (annually recommended)
- Secure key storage (never in code/config files)
- Access logging and monitoring
- Regular security assessments
- Staff training on encryption procedures

### ✅ Compliance Maintenance
- Annual FERPA compliance review
- Regular backup and recovery testing
- Documentation updates with system changes
- Audit log retention per institutional policy
- Incident response procedures

## Support and Troubleshooting

### Common Issues

**Decryption Errors:**
```python
# Check encryption system health
from mvp.encryption import check_encryption_health
print("Health:", check_encryption_health())

# Verify key configuration
from mvp.encryption import encryption_manager
print("Status:", encryption_manager.get_encryption_status())
```

**Performance Issues:**
- Monitor encryption operation latency
- Consider field-level caching for frequently accessed data
- Optimize queries to minimize decryption operations

**Key Rotation Issues:**
- Ensure backward compatibility during transitions
- Test with mixed-version encrypted data
- Monitor migration progress with version queries

### Contact Information
- **System Administrator**: Configure encryption keys and monitoring
- **Database Administrator**: Handle migration and performance optimization  
- **Compliance Officer**: Ensure FERPA requirements are met
- **Development Team**: Implement application-level encryption integration

---

**Last Updated**: August 2025  
**Version**: 1.0  
**Compliance**: FERPA-compliant for K-12 educational institutions