# Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Student Success Prediction System using Docker in both development and production environments.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Development Deployment](#development-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Scaling and Performance](#scaling-and-performance)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)

## Quick Start

### Development
```bash
# Clone and setup
git clone <repository-url>
cd student-success-prediction

# Copy environment file
cp .env.development .env

# Deploy with single command
./deploy.sh --environment development
```

### Production with Neon Database
```bash
# Copy and configure production environment
cp .env.production .env
nano .env  # Configure your Neon database URL and API keys

# Deploy to production
./deploy.sh --environment production
```

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 2GB RAM, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Internet access for Docker images and database

### Software Dependencies
- **Docker**: Version 20.10 or newer
- **Docker Compose**: Version 2.0 or newer
- **curl**: For health checks
- **bash**: For deployment scripts

### Installation Commands

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reboot or logout/login to apply group changes
```

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker

# Or download from: https://www.docker.com/products/docker-desktop
```

**Windows:**
```bash
# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop
# Ensure WSL2 is enabled
```

## Environment Configuration

### Development Environment

```bash
# Copy development template
cp .env.development .env
```

**Development .env contents:**
```env
# Local Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/student_success

# Development API Configuration
MVP_API_KEY=dev-key-change-me

# Application Settings
PORT=8001
SQL_DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Production Environment

```bash
# Copy production template
cp .env.production .env
nano .env  # Edit with your configuration
```

**Production .env requirements:**
```env
# Neon Database Configuration (REQUIRED)
DATABASE_URL=postgresql://username:password@your-host/database?sslmode=require

# Secure API Key (REQUIRED - change from default)
MVP_API_KEY=your-secure-production-key-min-32-chars

# Application Settings
PORT=8001
SQL_DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Email Notifications (Optional but recommended)
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# SSL Configuration (for custom domains)
ACME_EMAIL=admin@your-domain.com
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | SQLite fallback | Yes (Production) |
| `MVP_API_KEY` | API authentication key | dev-key-change-me | Yes |
| `PORT` | Application port | 8001 | No |
| `SQL_DEBUG` | Enable SQL query logging | false | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO | No |
| `ENVIRONMENT` | Environment type (development/production) | production | No |
| `EMAIL_USER` | SMTP username for alerts | None | No |
| `EMAIL_PASSWORD` | SMTP password/app password | None | No |
| `SMTP_SERVER` | SMTP server hostname | smtp.gmail.com | No |
| `SMTP_PORT` | SMTP server port | 587 | No |

## Development Deployment

### Using Docker Compose

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Run tests
docker compose -f docker-compose.dev.yml --profile testing up test

# Stop environment
docker compose -f docker-compose.dev.yml down
```

### Development Services

The development environment includes:

1. **Application** (Port 8001)
   - Hot reloading enabled
   - Debug logging
   - Source code mounted as volume

2. **PostgreSQL Database** (Port 5432)
   - Local database for testing
   - Persistent data storage
   - Health checks enabled

3. **pgAdmin** (Port 5050)
   - Database management interface
   - Login: admin@localhost.com / admin

### Development Workflow

```bash
# 1. Start development environment
./deploy.sh --environment development

# 2. Access application
curl http://localhost:8001/health

# 3. View application
open http://localhost:8001

# 4. Run tests
docker compose -f docker-compose.dev.yml --profile testing up test

# 5. View logs
docker compose -f docker-compose.dev.yml logs -f app

# 6. Access database
open http://localhost:5050  # pgAdmin

# 7. Stop environment
docker compose -f docker-compose.dev.yml down
```

## Production Deployment

### Prerequisites Checklist

- [ ] Neon database created and accessible
- [ ] `.env` file configured with production values
- [ ] Secure API key generated (minimum 32 characters)
- [ ] Email credentials configured (optional)
- [ ] Domain name configured (optional)
- [ ] SSL certificates ready (optional)

### Deployment Methods

#### Method 1: Automated Deployment Script (Recommended)

```bash
# Full deployment with tests
./deploy.sh --environment production

# Quick deployment (skip tests)
./deploy.sh --environment production --skip-tests

# Build only (no deployment)
./deploy.sh --environment production --build-only
```

#### Method 2: Manual Docker Compose

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### Production Services

1. **Application Container**
   - Optimized Python runtime
   - Non-root user for security
   - Health checks enabled
   - Resource limits configured

2. **Health Monitor Container**
   - Continuous system monitoring
   - Automated alerting
   - Email notifications
   - Performance tracking

3. **Traefik Reverse Proxy** (Optional)
   - SSL termination
   - Automatic HTTPS certificates
   - Load balancing
   - Domain routing

### Production Architecture

```
Internet → Traefik (Port 80/443) → Application (Port 8001) → Neon Database
                                 → Monitor Container
```

### Verification Steps

After deployment, verify the system is working:

```bash
# 1. Health check
curl http://localhost:8001/health

# 2. API documentation
curl http://localhost:8001/docs

# 3. Upload test
curl -X POST http://localhost:8001/api/mvp/sample \
  -H "Authorization: Bearer your-api-key"

# 4. Container status
docker compose -f docker-compose.prod.yml ps

# 5. Resource usage
docker stats

# 6. Application logs
docker compose -f docker-compose.prod.yml logs app
```

## Monitoring and Maintenance

### Built-in Monitoring

The production deployment includes comprehensive monitoring:

```bash
# View monitor logs
docker compose -f docker-compose.prod.yml logs monitor

# Manual health check
docker compose -f docker-compose.prod.yml exec app python3 scripts/system_health_monitor.py

# Run tests
docker compose -f docker-compose.prod.yml exec app python3 scripts/run_automated_tests.py
```

### Log Management

```bash
# View application logs
docker compose -f docker-compose.prod.yml logs -f app

# Export logs
docker compose -f docker-compose.prod.yml logs app > app.log

# Rotate logs (prevent disk space issues)
docker system prune -f
```

### Backup Procedures

```bash
# Manual backup (if using local PostgreSQL)
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres student_success > backup.sql

# For Neon database
pg_dump "$DATABASE_URL" > backup.sql

# Backup application data
docker compose -f docker-compose.prod.yml exec app tar -czf /tmp/app_backup.tar.gz logs/ test_reports/ config/
```

### Update Procedures

```bash
# 1. Pull latest code
git pull origin main

# 2. Backup current deployment
./deploy.sh --environment production --build-only

# 3. Deploy with tests
./deploy.sh --environment production

# 4. Verify deployment
curl http://localhost:8001/health
```

## Scaling and Performance

### Horizontal Scaling

```yaml
# In docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3  # Run 3 instances
    ports:
      - "8001-8003:8001"  # Map to different ports
```

### Resource Optimization

```yaml
# Optimize container resources
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Application performance
docker compose -f docker-compose.prod.yml exec app python3 scripts/run_automated_tests.py --performance-only

# Database performance (for local PostgreSQL)
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs app

# Check container status
docker compose -f docker-compose.prod.yml ps

# Restart container
docker compose -f docker-compose.prod.yml restart app
```

#### 2. Database Connection Issues

```bash
# Test database connection
docker compose -f docker-compose.prod.yml exec app python3 -c "
import os
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    result = await conn.fetchval('SELECT 1')
    print('Database OK' if result == 1 else 'Database Error')
    await conn.close()

asyncio.run(test())
"
```

#### 3. Permission Issues

```bash
# Fix file permissions
sudo chown -R $(whoami):$(whoami) .
chmod +x deploy.sh scripts/*.sh
```

#### 4. Out of Memory

```bash
# Check memory usage
docker stats

# Increase container memory limit
# Edit docker-compose.prod.yml and increase memory limit

# Clean up unused resources
docker system prune -a
```

#### 5. Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :8001

# Kill conflicting process
sudo kill -9 $(lsof -t -i:8001)

# Or change port in .env file
echo "PORT=8002" >> .env
```

### Debugging Commands

```bash
# Enter container shell
docker compose -f docker-compose.prod.yml exec app bash

# Check environment variables
docker compose -f docker-compose.prod.yml exec app env

# Test application components
docker compose -f docker-compose.prod.yml exec app python3 -c "
from mvp.mvp_api import app
print('Application loaded successfully')
"

# Check disk space
docker compose -f docker-compose.prod.yml exec app df -h

# Check process list
docker compose -f docker-compose.prod.yml exec app ps aux
```

### Log Analysis

```bash
# Filter error logs
docker compose -f docker-compose.prod.yml logs app | grep ERROR

# Real-time error monitoring
docker compose -f docker-compose.prod.yml logs -f app | grep -i error

# Export logs for analysis
docker compose -f docker-compose.prod.yml logs app > production.log
```

## Security Considerations

### Container Security

1. **Non-root User**: Application runs as non-root user
2. **Read-only Filesystem**: Critical files are read-only
3. **Resource Limits**: CPU and memory limits prevent resource exhaustion
4. **Health Checks**: Automatic restart on health check failures

### Network Security

1. **Isolated Network**: Containers run in isolated Docker network
2. **Port Exposure**: Only necessary ports are exposed
3. **TLS Encryption**: HTTPS enabled with automatic certificates
4. **API Authentication**: All endpoints require API key authentication

### Data Security

1. **Environment Variables**: Sensitive data stored in environment variables
2. **Database Encryption**: Connection encrypted with SSL/TLS
3. **Log Sanitization**: Sensitive data filtered from logs
4. **Backup Encryption**: Database backups should be encrypted

### Security Checklist

- [ ] Change default API key
- [ ] Enable HTTPS/TLS
- [ ] Restrict database access
- [ ] Enable container health checks
- [ ] Set up log monitoring
- [ ] Configure backup encryption
- [ ] Review and update dependencies regularly
- [ ] Enable firewall rules
- [ ] Set up intrusion detection
- [ ] Regular security audits

### Security Updates

```bash
# Update base images
docker compose -f docker-compose.prod.yml pull

# Rebuild with latest security patches
docker compose -f docker-compose.prod.yml build --no-cache

# Check for vulnerabilities
docker scout cves student-success-prediction_app
```

## Advanced Configuration

### Custom Domain Setup

1. **Configure DNS**: Point domain to server IP
2. **Update Traefik labels**: Set domain in docker-compose.prod.yml
3. **SSL Certificates**: Automatic via Let's Encrypt

```yaml
labels:
  - "traefik.http.routers.student-success.rule=Host(`your-domain.com`)"
```

### Email Notifications

Configure SMTP settings in `.env`:

```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Use app password, not regular password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Load Balancing

For high-traffic deployments:

```yaml
services:
  app:
    deploy:
      replicas: 3
    labels:
      - "traefik.http.services.student-success.loadbalancer.server.port=8001"
```

### Persistent Storage

Configure persistent volumes for important data:

```yaml
volumes:
  app_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/student-success/logs
```

---

## Support and Maintenance

For deployment issues:

1. Check this documentation
2. Review container logs
3. Check system requirements
4. Verify environment configuration
5. Test database connectivity

For updates and maintenance:
- Monitor resource usage regularly
- Keep Docker images updated
- Backup data before updates
- Test updates in development first
- Follow security best practices

**Last Updated**: [Current Date]
**Version**: 2.0.0