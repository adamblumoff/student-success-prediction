#!/bin/bash

# Production Deployment Script for Student Success Prediction System
# Handles secure deployment with validation, backups, and rollback capabilities

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.production.yml"
ENV_FILE="$SCRIPT_DIR/.env.production"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_FILE="$PROJECT_ROOT/logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$BACKUP_DIR"

# Function to validate environment
validate_environment() {
    info "Validating deployment environment..."
    
    # Check required files
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Production environment file not found: $ENV_FILE"
        error "Copy .env.production.template to .env.production and configure it"
        exit 1
    fi
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Source environment variables
    source "$ENV_FILE"
    
    # Validate critical environment variables
    local required_vars=(
        "ENVIRONMENT"
        "MVP_API_KEY"
        "SESSION_SECRET"
        "DATABASE_URL"
        "POSTGRES_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Validate environment is production
    if [[ "$ENVIRONMENT" != "production" ]]; then
        error "ENVIRONMENT must be set to 'production'"
        exit 1
    fi
    
    # Validate security settings
    if [[ "$DEVELOPMENT_MODE" == "true" ]]; then
        error "DEVELOPMENT_MODE must be 'false' in production"
        exit 1
    fi
    
    # Validate key lengths
    if [[ ${#MVP_API_KEY} -lt 32 ]]; then
        error "MVP_API_KEY must be at least 32 characters long"
        exit 1
    fi
    
    if [[ ${#SESSION_SECRET} -lt 32 ]]; then
        error "SESSION_SECRET must be at least 32 characters long"
        exit 1
    fi
    
    # Check for default/template values
    if [[ "$MVP_API_KEY" == *"REPLACE_WITH"* ]] || [[ "$SESSION_SECRET" == *"REPLACE_WITH"* ]]; then
        error "Default template values found in environment file. Please set secure values."
        exit 1
    fi
    
    success "Environment validation passed"
}

# Function to validate system resources
validate_system() {
    info "Validating system resources..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check disk space (minimum 5GB)
    local available_space
    available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local required_space=$((5 * 1024 * 1024))  # 5GB in KB
    
    if [[ "$available_space" -lt "$required_space" ]]; then
        error "Insufficient disk space. Required: 5GB, Available: $((available_space / 1024 / 1024))GB"
        exit 1
    fi
    
    # Check memory (minimum 2GB)
    local available_memory
    available_memory=$(free | awk 'NR==2 {print $7}')
    local required_memory=$((2 * 1024 * 1024))  # 2GB in KB
    
    if [[ "$available_memory" -lt "$required_memory" ]]; then
        warning "Low memory detected. Available: $((available_memory / 1024 / 1024))GB"
    fi
    
    success "System validation passed"
}

# Function to create database backup
backup_database() {
    info "Creating database backup..."
    
    if [[ "${SKIP_BACKUP:-false}" == "true" ]]; then
        warning "Skipping database backup as requested"
        return
    fi
    
    local backup_filename="db_backup_$(date +%Y%m%d_%H%M%S).sql"
    local backup_path="$BACKUP_DIR/$backup_filename"
    
    # Extract database credentials from DATABASE_URL
    local db_url="${DATABASE_URL:-}"
    if [[ -n "$db_url" ]]; then
        # Create backup using pg_dump (if PostgreSQL is accessible)
        if command -v pg_dump &> /dev/null; then
            if pg_dump "$db_url" > "$backup_path" 2>/dev/null; then
                success "Database backup created: $backup_filename"
                echo "$backup_path" > "$BACKUP_DIR/latest_backup.txt"
            else
                warning "Could not create database backup (database may not be accessible yet)"
            fi
        else
            warning "pg_dump not available, skipping database backup"
        fi
    else
        warning "DATABASE_URL not set, skipping database backup"
    fi
}

# Function to build and deploy
deploy() {
    info "Starting deployment..."
    
    # Pull latest images
    info "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Build application image
    info "Building application image..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build app
    
    # Stop existing services
    info "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # Start database services first
    info "Starting database services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
            success "Database is ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Database failed to start within timeout"
            exit 1
        fi
        
        info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Run database migrations
    info "Running database migrations..."
    cd "$PROJECT_ROOT"
    if command -v alembic &> /dev/null; then
        if ! alembic upgrade head; then
            error "Database migration failed"
            exit 1
        fi
    else
        warning "Alembic not available, skipping migrations"
    fi
    
    # Start application services
    info "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for application to be ready
    info "Waiting for application to be ready..."
    local app_ready=false
    max_attempts=30
    attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:${APP_PORT:-8000}/api/health/health >/dev/null 2>&1; then
            app_ready=true
            break
        fi
        
        info "Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ "$app_ready" == "true" ]]; then
        success "Application is ready"
    else
        error "Application failed to start within timeout"
        exit 1
    fi
}

# Function to run health checks
health_check() {
    info "Running post-deployment health checks..."
    
    local health_endpoints=(
        "http://localhost:${APP_PORT:-8000}/api/health/health"
        "http://localhost:${APP_PORT:-8000}/api/health/ready"
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        if curl -f "$endpoint" >/dev/null 2>&1; then
            success "Health check passed: $endpoint"
        else
            error "Health check failed: $endpoint"
            return 1
        fi
    done
    
    # Check SSL if enabled
    if [[ "${SSL_ENABLED:-false}" == "true" ]]; then
        if curl -f https://localhost/health >/dev/null 2>&1; then
            success "HTTPS health check passed"
        else
            warning "HTTPS health check failed"
        fi
    fi
    
    success "All health checks passed"
}

# Function to rollback deployment
rollback() {
    error "Deployment failed, initiating rollback..."
    
    # Stop current deployment
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # Restore database backup if available
    local latest_backup
    if [[ -f "$BACKUP_DIR/latest_backup.txt" ]]; then
        latest_backup=$(cat "$BACKUP_DIR/latest_backup.txt")
        if [[ -f "$latest_backup" ]]; then
            warning "Database rollback not implemented. Manual intervention may be required."
            warning "Latest backup available at: $latest_backup"
        fi
    fi
    
    error "Rollback completed. Check logs for details."
    exit 1
}

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-validation    Skip environment validation"
    echo "  --skip-backup       Skip database backup"
    echo "  --no-health-check   Skip post-deployment health checks"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Full deployment with all checks"
    echo "  $0 --skip-backup    # Deploy without creating backup"
}

# Main deployment function
main() {
    local skip_validation=false
    local skip_backup=false
    local skip_health_check=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-validation)
                skip_validation=true
                shift
                ;;
            --skip-backup)
                export SKIP_BACKUP=true
                shift
                ;;
            --no-health-check)
                skip_health_check=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    info "Starting production deployment of Student Success Prediction System"
    info "Deployment started at $(date)"
    
    # Validation phase
    if [[ "$skip_validation" == "false" ]]; then
        validate_environment
        validate_system
    else
        warning "Skipping environment validation as requested"
    fi
    
    # Backup phase
    backup_database
    
    # Deploy phase
    if deploy; then
        success "Deployment completed successfully"
    else
        rollback
    fi
    
    # Health check phase
    if [[ "$skip_health_check" == "false" ]]; then
        if ! health_check; then
            rollback
        fi
    else
        warning "Skipping health checks as requested"
    fi
    
    success "Production deployment completed successfully!"
    info "Application is available at: http://localhost:${APP_PORT:-8000}"
    
    if [[ "${SSL_ENABLED:-false}" == "true" ]]; then
        info "HTTPS is available at: https://localhost"
    fi
    
    info "View logs with: docker-compose -f $COMPOSE_FILE logs -f"
    info "Monitor with: docker-compose -f $COMPOSE_FILE ps"
}

# Set trap for cleanup on exit
trap 'error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"