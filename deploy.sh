#!/bin/bash
# Production Deployment Script for Student Success Prediction System

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Default values
ENVIRONMENT="production"
BUILD_ONLY=false
SKIP_TESTS=false
BACKUP_DB=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --no-backup)
            BACKUP_DB=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (production|development) [default: production]"
            echo "  -b, --build-only        Only build, don't deploy"
            echo "  --skip-tests            Skip running tests before deployment"
            echo "  --no-backup             Skip database backup"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "🚀 Starting deployment for environment: $ENVIRONMENT"

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Docker is installed and running
if ! docker --version &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check if .env file exists
ENV_FILE=".env"
if [[ "$ENVIRONMENT" == "production" ]]; then
    if [[ ! -f "$ENV_FILE" ]]; then
        print_warning "No .env file found. Please copy .env.production to .env and configure it."
        print_status "Example: cp .env.production .env && nano .env"
        exit 1
    fi
    
    # Verify required environment variables
    if ! grep -q "DATABASE_URL=postgresql" "$ENV_FILE"; then
        print_error "DATABASE_URL not properly configured in .env file"
        exit 1
    fi
    
    if grep -q "your-secure-production-api-key-here" "$ENV_FILE"; then
        print_error "Please update the MVP_API_KEY in .env file with a secure key"
        exit 1
    fi
fi

print_success "Prerequisites check passed"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs test_reports backups config
print_success "Directories created"

# Run tests if not skipped
if [[ "$SKIP_TESTS" != true ]]; then
    print_status "Running tests before deployment..."
    
    # Use development compose for testing
    docker compose -f docker-compose.dev.yml --profile testing up test --build --abort-on-container-exit
    
    if [[ $? -ne 0 ]]; then
        print_error "Tests failed. Deployment aborted."
        print_status "Use --skip-tests to bypass testing"
        exit 1
    fi
    
    print_success "All tests passed"
fi

# Database backup for production
if [[ "$ENVIRONMENT" == "production" && "$BACKUP_DB" == true ]]; then
    print_status "Creating database backup..."
    
    # Load environment variables
    source .env
    
    if [[ -n "$DATABASE_URL" ]]; then
        BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        # Create backup directory if it doesn't exist
        mkdir -p backups
        
        # Create database backup (this assumes pg_dump is available)
        if command -v pg_dump &> /dev/null; then
            pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null && \
            print_success "Database backup created: $BACKUP_FILE" || \
            print_warning "Database backup failed, but continuing deployment"
        else
            print_warning "pg_dump not available, skipping database backup"
        fi
    fi
fi

# Build and deploy
print_status "Building Docker images..."

if [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="docker-compose.dev.yml"
fi

# Build the application
docker compose -f "$COMPOSE_FILE" build --no-cache

if [[ $? -ne 0 ]]; then
    print_error "Docker build failed"
    exit 1
fi

print_success "Docker images built successfully"

# Exit if build-only mode
if [[ "$BUILD_ONLY" == true ]]; then
    print_success "Build completed successfully (build-only mode)"
    exit 0
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker compose -f "$COMPOSE_FILE" down

# Start the application
print_status "Starting application containers..."
docker compose -f "$COMPOSE_FILE" up -d

# Wait for application to be ready
print_status "Waiting for application to be ready..."
sleep 30

# Health check
print_status "Performing health check..."
MAX_RETRIES=10
RETRY_COUNT=0

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if curl -f -s http://localhost:8001/health > /dev/null; then
        print_success "Application is healthy and ready!"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        print_status "Health check attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying in 10 seconds..."
        sleep 10
    fi
done

if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
    print_error "Application failed to start properly"
    print_status "Check logs with: docker compose -f $COMPOSE_FILE logs"
    exit 1
fi

# Show deployment summary
print_success "🎉 Deployment completed successfully!"
echo ""
print_status "Application Information:"
echo "  Environment: $ENVIRONMENT"
echo "  URL: http://localhost:8001"
echo "  Health: http://localhost:8001/health"
echo "  API Docs: http://localhost:8001/docs"
echo ""
print_status "Useful Commands:"
echo "  View logs: docker compose -f $COMPOSE_FILE logs -f"
echo "  Stop app: docker compose -f $COMPOSE_FILE down"
echo "  Restart: docker compose -f $COMPOSE_FILE restart"
echo "  Shell: docker compose -f $COMPOSE_FILE exec app bash"
echo ""

if [[ "$ENVIRONMENT" == "production" ]]; then
    print_status "Production Notes:"
    echo "  - Monitor logs regularly"
    echo "  - Set up automated backups"
    echo "  - Configure domain and SSL certificates"
    echo "  - Review security settings"
fi

print_success "Deployment completed! 🚀"