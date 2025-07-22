# Production Deployment Guide

## 🚀 Overview

This guide covers deploying the Student Success Prediction API to production environments using Docker containers, PostgreSQL database, and comprehensive monitoring.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended  
- **Disk**: 20GB available space
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### Software Dependencies
```bash
# Install Docker (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🔧 Configuration

### 1. Environment Setup

Copy the environment template:
```bash
cp .env.example .env.production
```

Update the production environment file:
```bash
# Required variables
DATABASE_URL=postgresql://student_user:SECURE_PASSWORD@postgres:5432/student_success_db
API_KEY=your-secure-api-key-here
JWT_SECRET=your-jwt-secret-key-here

# Optional but recommended
SENTRY_DSN=your-sentry-dsn
SMTP_SERVER=smtp.gmail.com
SLACK_WEBHOOK_URL=your-slack-webhook
```

### 2. SSL/TLS Certificates

For production HTTPS:
```bash
# Create SSL directory
mkdir -p deployment/ssl

# Option A: Use Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/ssl/key.pem

# Option B: Self-signed certificates (development only)
openssl req -x509 -newkey rsa:4096 -keyout deployment/ssl/key.pem -out deployment/ssl/cert.pem -days 365 -nodes
```

### 3. Database Configuration

The system uses PostgreSQL with automatic fallback to SQLite:

**PostgreSQL (Recommended for Production)**:
- Automatic schema creation
- Connection pooling
- Performance indexes
- Monitoring integration

**SQLite (Development/Testing)**:
- Automatic fallback if PostgreSQL unavailable
- No additional setup required
- Limited concurrent connections

## 🚁 Deployment Options

### Quick Start (Automated)

Use the deployment script for fully automated setup:

```bash
# Development deployment
./scripts/deploy.sh development deploy

# Production deployment  
./scripts/deploy.sh production deploy

# Staging deployment
./scripts/deploy.sh staging deploy
```

### Manual Deployment

For more control over the deployment process:

#### 1. Build Images
```bash
docker build -t student-success-api:latest .
```

#### 2. Start Database
```bash
docker-compose up -d postgres
```

#### 3. Setup Database Schema
```bash
python scripts/setup_production_db.py
```

#### 4. Start Application Services
```bash
# Development
docker-compose up -d api redis

# Production (with monitoring)
docker-compose --profile production up -d
```

## 📊 Service Architecture

### Core Services
- **API**: FastAPI application server (Port 8000)
- **PostgreSQL**: Primary database (Port 5432)
- **Redis**: Caching and session storage (Port 6379)
- **Nginx**: Reverse proxy and load balancer (Ports 80/443)

### Monitoring Stack (Production)
- **Prometheus**: Metrics collection (Port 9090)
- **Grafana**: Dashboards and visualization (Port 3000)
- **Node Exporter**: System metrics
- **PostgreSQL Exporter**: Database metrics

## 🔍 Health Checks & Monitoring

### Built-in Health Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/status

# Kubernetes-style probes
curl http://localhost:8000/health/live     # Liveness
curl http://localhost:8000/health/ready    # Readiness  
curl http://localhost:8000/health/startup  # Startup
```

### Prometheus Metrics

Available at `http://localhost:8001/metrics`:
- API request count and duration
- Prediction statistics by risk category  
- Database connection pool metrics
- System resource utilization
- Model inference performance

### Monitoring Dashboards

Access Grafana at `http://localhost:3000` (admin/admin):
- **API Performance**: Request rates, response times, error rates
- **System Resources**: CPU, memory, disk usage
- **Database Health**: Connection counts, query performance
- **ML Model Metrics**: Prediction accuracy, inference times
- **Business Metrics**: Risk distribution, intervention rates

## 🔒 Security Configuration

### API Security
- **Authentication**: Bearer token with configurable keys
- **Rate Limiting**: Configurable per endpoint (default: 60/min)
- **CORS**: Configurable allowed origins
- **Request Validation**: Pydantic models with constraints

### Database Security
- **Connection Encryption**: SSL/TLS for PostgreSQL connections
- **User Isolation**: Dedicated database user with minimal privileges
- **Connection Pooling**: Prevents connection exhaustion attacks

### Infrastructure Security
- **Reverse Proxy**: Nginx with security headers
- **SSL Termination**: TLS 1.2/1.3 with strong ciphers
- **Container Security**: Non-root user, minimal base images
- **Secret Management**: Environment-based configuration

## 📈 Scaling Configuration

### Horizontal Scaling

Scale API containers:
```bash
# Scale to 4 API instances
docker-compose up -d --scale api=4

# Update Nginx upstream configuration
# Edit deployment/nginx.conf to include all instances
```

### Vertical Scaling

Update resource limits in `docker-compose.yml`:
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 4g
        cpus: '2.0'
      reservations:
        memory: 2g
        cpus: '1.0'
```

### Database Scaling

For high-load scenarios:
- **Connection Pooling**: Increase pool size (DB_POOL_SIZE=50)
- **Read Replicas**: Add PostgreSQL read replicas
- **Caching**: Increase Redis cache size and TTL

## 🔄 Maintenance & Operations

### Regular Tasks

**Daily**:
```bash
# Check service health
./scripts/deploy.sh production status

# Review logs for errors
docker-compose logs --since=24h api | grep ERROR
```

**Weekly**:
```bash
# Create database backup
./scripts/deploy.sh production backup

# Update and restart services
git pull
./scripts/deploy.sh production restart
```

**Monthly**:
```bash
# Clean up old images and containers
./scripts/deploy.sh production cleanup

# Review and rotate logs
docker system prune -f
```

### Log Management

Logs are automatically managed with rotation:
- **Application Logs**: `/app/logs/api.log` (10MB rotation)
- **Access Logs**: Nginx access logs
- **Database Logs**: PostgreSQL logs
- **System Logs**: Container logs via Docker

### Backup Strategy

**Database Backups**:
- Automated daily backups at 2 AM
- 30-day retention (production), 7-day (staging)
- Compressed SQL dumps with timestamps

**Application Backups**:
- Model artifacts backed up with deployments
- Configuration files in version control
- SSL certificates backed up securely

## 🚨 Troubleshooting

### Common Issues

**API Not Starting**:
```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing environment variables
# - Database connection failure  
# - Model files not found
# - Port already in use
```

**Database Connection Errors**:
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Reset database connection
docker-compose restart postgres
sleep 30
docker-compose restart api
```

**Performance Issues**:
```bash
# Check resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U student_user -c "SELECT * FROM pg_stat_activity;"

# Scale if needed
docker-compose up -d --scale api=3
```

### Emergency Procedures

**Complete System Failure**:
1. Stop all services: `docker-compose down`
2. Check disk space: `df -h`
3. Check system resources: `top`, `free -h`
4. Restart services: `./scripts/deploy.sh production deploy`
5. Verify health: `curl http://localhost:8000/health`

**Data Recovery**:
1. Stop API: `docker-compose stop api`
2. Restore from backup: `gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U student_user student_success_db`
3. Restart API: `docker-compose start api`

## 🌐 Cloud Deployment

### AWS Deployment

Using ECS with RDS:
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance --db-instance-identifier student-success-db \
  --db-instance-class db.t3.medium --engine postgres --master-username student_user

# Deploy to ECS
aws ecs create-cluster --cluster-name student-success-cluster
# Use provided task definition and service configuration
```

### Google Cloud Platform

Using Cloud Run with Cloud SQL:
```bash
# Create Cloud SQL instance
gcloud sql instances create student-success-db --database-version=POSTGRES_13

# Deploy to Cloud Run
gcloud run deploy student-success-api --source . --region us-central1
```

### Azure Deployment

Using Container Instances with PostgreSQL:
```bash
# Create PostgreSQL server
az postgres server create --name student-success-db --resource-group myResourceGroup

# Deploy container
az container create --resource-group myResourceGroup --name student-success-api \
  --image student-success-api:latest
```

## 📞 Support & Monitoring

### Alerting Configuration

**Critical Alerts** (immediate response):
- API down (health check failing)
- Database connection lost
- Error rate > 10%
- CPU/Memory > 90%

**Warning Alerts** (within 1 hour):
- Response time > 1s average
- Error rate > 5%
- Disk usage > 80%
- Prediction accuracy drop

### Contact Information

- **On-call Engineer**: Configure PagerDuty/OpsGenie
- **Slack Notifications**: #student-success-alerts
- **Email Alerts**: admin@your-organization.com
- **Dashboard URL**: https://grafana.your-organization.com

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Deploy production
./scripts/deploy.sh production deploy

# Check status
./scripts/deploy.sh production status

# View logs
./scripts/deploy.sh production logs

# Create backup
./scripts/deploy.sh production backup

# Run tests
./scripts/deploy.sh production test
```

### Important URLs
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8001/metrics
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

### Configuration Files
- **Environment**: `.env.production`
- **Database Schema**: `scripts/schema.sql`
- **Nginx Config**: `deployment/nginx.conf`
- **Docker Compose**: `docker-compose.yml`
- **Prometheus**: `deployment/prometheus.yml`