#!/bin/bash

# Production Deployment Script for Student Success Prediction API
# Usage: ./scripts/deploy.sh [environment] [command]
# Example: ./scripts/deploy.sh production deploy

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-development}
COMMAND=${2:-deploy}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Set Docker Compose command
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"
    fi
    
    log_success "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    log_info "Loading environment configuration for: $ENVIRONMENT"
    
    ENV_FILE="$PROJECT_ROOT/.env"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        ENV_FILE="$PROJECT_ROOT/.env.production"
    elif [ "$ENVIRONMENT" = "staging" ]; then
        ENV_FILE="$PROJECT_ROOT/.env.staging"
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file $ENV_FILE not found. Using defaults."
        if [ ! -f "$PROJECT_ROOT/.env.example" ]; then
            log_error "No .env.example found either. Please create environment configuration."
            exit 1
        fi
        log_info "Copying .env.example to $ENV_FILE"
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        log_warning "Please update $ENV_FILE with your actual configuration before proceeding."
        exit 1
    fi
    
    # Export environment variables
    set -a  # Mark all variables for export
    source "$ENV_FILE"
    set +a  # Stop marking variables for export
    
    log_success "Environment loaded from $ENV_FILE"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build main application image
    log_info "Building application image..."
    docker build -t student-success-api:$ENVIRONMENT .
    
    log_success "Docker images built successfully"
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    cd "$PROJECT_ROOT"
    
    # Start database container if not running
    $DOCKER_COMPOSE_CMD up -d postgres
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U ${POSTGRES_USER:-student_user} -d ${POSTGRES_DB:-student_success_db} &> /dev/null; then
            log_success "Database is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Database failed to become ready within 60 seconds"
        exit 1
    fi
    
    # Run database setup script
    log_info "Running database setup..."
    python3 "$PROJECT_ROOT/scripts/setup_production_db.py"
    
    log_success "Database setup completed"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    cd "$PROJECT_ROOT"
    
    # Create necessary directories
    mkdir -p logs data/processed results/models
    
    # Deploy based on environment
    if [ "$ENVIRONMENT" = "production" ]; then
        # Production deployment with full stack
        log_info "Starting production deployment..."
        $DOCKER_COMPOSE_CMD --profile production up -d
    else
        # Development/staging deployment
        log_info "Starting development deployment..."
        $DOCKER_COMPOSE_CMD up -d api postgres redis
    fi
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check health endpoints
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        show_logs
        exit 1
    fi
    
    log_success "Application deployed successfully"
}

# Show service logs
show_logs() {
    log_info "Showing service logs..."
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE_CMD logs --tail=50
}

# Show service status
show_status() {
    log_info "Service Status:"
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE_CMD ps
    
    echo
    log_info "Health Checks:"
    
    # API health
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "✅ API is healthy"
    else
        log_error "❌ API is not healthy"
    fi
    
    # Database health
    if $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U ${POSTGRES_USER:-student_user} &> /dev/null; then
        log_success "✅ Database is healthy"
    else
        log_error "❌ Database is not healthy"
    fi
    
    # Redis health
    if $DOCKER_COMPOSE_CMD exec -T redis redis-cli ping &> /dev/null; then
        log_success "✅ Redis is healthy"
    else
        log_error "❌ Redis is not healthy"
    fi
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE_CMD down
    log_success "Services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting services..."
    stop_services
    deploy_application
}

# Cleanup old containers and images
cleanup() {
    log_info "Cleaning up old containers and images..."
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful in production)
    if [ "$ENVIRONMENT" != "production" ]; then
        docker volume prune -f
    fi
    
    log_success "Cleanup completed"
}

# Backup database
backup_database() {
    log_info "Creating database backup..."
    
    cd "$PROJECT_ROOT"
    
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/student_success_db_${ENVIRONMENT}_${TIMESTAMP}.sql"
    
    $DOCKER_COMPOSE_CMD exec -T postgres pg_dump -U ${POSTGRES_USER:-student_user} ${POSTGRES_DB:-student_success_db} > "$BACKUP_FILE"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    
    log_success "Database backup created: ${BACKUP_FILE}.gz"
}

# Run tests
run_tests() {
    log_info "Running integration tests..."
    
    cd "$PROJECT_ROOT"
    
    # Ensure test environment is running
    $DOCKER_COMPOSE_CMD up -d api postgres
    
    # Wait for services
    sleep 20
    
    # Run tests
    python3 -m pytest tests/integration/ -v
    
    if [ $? -eq 0 ]; then
        log_success "All tests passed"
    else
        log_error "Some tests failed"
        exit 1
    fi
}

# Main deployment function
main_deploy() {
    log_info "🚀 Starting deployment for environment: $ENVIRONMENT"
    echo "=================================================="
    
    check_prerequisites
    load_environment
    build_images
    setup_database
    deploy_application
    show_status
    
    echo "=================================================="
    log_success "🎉 Deployment completed successfully!"
    
    echo
    log_info "📋 Next Steps:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/health"
    echo "  • Metrics: http://localhost:8001/metrics (if enabled)"
    echo "  • Logs: docker-compose logs -f api"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "  • Grafana Dashboard: http://localhost:3000 (admin/admin)"
        echo "  • Prometheus: http://localhost:9090"
    fi
}

# Command routing
case "$COMMAND" in
    "deploy")
        main_deploy
        ;;
    "build")
        check_prerequisites
        load_environment
        build_images
        ;;
    "start")
        check_prerequisites
        load_environment
        deploy_application
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        check_prerequisites
        load_environment
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "test")
        check_prerequisites
        load_environment
        run_tests
        ;;
    "backup")
        check_prerequisites
        load_environment
        backup_database
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 [environment] [command]"
        echo ""
        echo "Environments:"
        echo "  development  - Local development (default)"
        echo "  staging      - Staging environment"
        echo "  production   - Production environment"
        echo ""
        echo "Commands:"
        echo "  deploy       - Full deployment (build + start + setup)"
        echo "  build        - Build Docker images only"
        echo "  start        - Start services"
        echo "  stop         - Stop services"
        echo "  restart      - Restart services"
        echo "  status       - Show service status"
        echo "  logs         - Show service logs"
        echo "  test         - Run integration tests"
        echo "  backup       - Create database backup"
        echo "  cleanup      - Remove old containers and images"
        echo ""
        echo "Examples:"
        echo "  $0 development deploy"
        echo "  $0 production start"
        echo "  $0 staging backup"
        exit 1
        ;;
esac