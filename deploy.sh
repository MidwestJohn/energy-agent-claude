#!/bin/bash

# Energy Grid Management Agent Deployment Script
# Supports multiple environments and cloud platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="energy-grid-agent"
VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")

# Default values
ENVIRONMENT="development"
PLATFORM="docker"
BUILD_TARGET="production"
SKIP_TESTS=false
FORCE_REBUILD=false

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

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Energy Grid Management Agent

OPTIONS:
    -e, --environment ENV    Deployment environment (development|staging|production)
    -p, --platform PLATFORM  Deployment platform (docker|kubernetes|aws|gcp|azure)
    -t, --target TARGET      Docker build target (production|development)
    -s, --skip-tests         Skip running tests before deployment
    -f, --force              Force rebuild of Docker images
    -h, --help               Show this help message

EXAMPLES:
    $0 -e development -p docker
    $0 -e production -p kubernetes -f
    $0 -e staging -p aws --skip-tests

EOF
}

# Function to validate environment variables
validate_env_vars() {
    print_status "Validating environment variables..."
    
    local required_vars=(
        "CLAUDE_API_KEY"
        "NEO4J_URI"
        "NEO4J_USERNAME"
        "NEO4J_PASSWORD"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        print_error "Please set these variables in your .env file or environment"
        exit 1
    fi
    
    print_success "Environment variables validated"
}

# Function to run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        print_warning "Skipping tests as requested"
        return 0
    fi
    
    print_status "Running tests..."
    
    if ! python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term; then
        print_error "Tests failed. Aborting deployment."
        exit 1
    fi
    
    print_success "Tests passed"
}

# Function to build Docker image
build_docker_image() {
    print_status "Building Docker image..."
    
    local build_args=""
    if [[ "$FORCE_REBUILD" == "true" ]]; then
        build_args="--no-cache"
    fi
    
    if ! docker build $build_args --target $BUILD_TARGET -t $PROJECT_NAME:$VERSION .; then
        print_error "Docker build failed"
        exit 1
    fi
    
    # Tag as latest
    docker tag $PROJECT_NAME:$VERSION $PROJECT_NAME:latest
    
    print_success "Docker image built successfully"
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Set environment variables for docker-compose
    export BUILD_TARGET=$BUILD_TARGET
    export ENVIRONMENT=$ENVIRONMENT
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env 2>/dev/null || {
            print_error "No .env.example found. Please create a .env file manually."
            exit 1
        }
    fi
    
    # Start services
    if ! docker-compose up -d; then
        print_error "Docker Compose deployment failed"
        exit 1
    fi
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Some services failed to start"
        docker-compose logs
        exit 1
    fi
    
    print_success "Docker Compose deployment completed"
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace $PROJECT_NAME --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    for manifest in k8s/*.yaml; do
        if [[ -f "$manifest" ]]; then
            print_status "Applying $manifest..."
            envsubst < "$manifest" | kubectl apply -f -
        fi
    done
    
    # Wait for deployment to be ready
    print_status "Waiting for deployment to be ready..."
    kubectl rollout status deployment/$PROJECT_NAME -n $PROJECT_NAME --timeout=300s
    
    print_success "Kubernetes deployment completed"
}

# Function to deploy to AWS
deploy_aws() {
    print_status "Deploying to AWS..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Check if ECR repository exists
    local ecr_repo="$PROJECT_NAME"
    if ! aws ecr describe-repositories --repository-names $ecr_repo &> /dev/null; then
        print_status "Creating ECR repository..."
        aws ecr create-repository --repository-name $ecr_repo
    fi
    
    # Get ECR login token
    local ecr_login=$(aws ecr get-login-password --region $(aws configure get region))
    docker login --username AWS --password $ecr_login $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com
    
    # Tag and push image
    local ecr_uri=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com/$ecr_repo
    docker tag $PROJECT_NAME:$VERSION $ecr_uri:$VERSION
    docker push $ecr_uri:$VERSION
    
    # Deploy using ECS or EKS (depending on configuration)
    if [[ -f "aws/ecs-task-definition.json" ]]; then
        deploy_aws_ecs $ecr_uri
    elif [[ -f "aws/eks-deployment.yaml" ]]; then
        deploy_aws_eks $ecr_uri
    else
        print_error "No AWS deployment configuration found"
        exit 1
    fi
    
    print_success "AWS deployment completed"
}

# Function to deploy to Google Cloud Platform
deploy_gcp() {
    print_status "Deploying to Google Cloud Platform..."
    
    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Set project
    local project_id=$(gcloud config get-value project)
    if [[ -z "$project_id" ]]; then
        print_error "No GCP project configured. Run 'gcloud config set project PROJECT_ID'"
        exit 1
    fi
    
    # Build and push to Container Registry
    docker tag $PROJECT_NAME:$VERSION gcr.io/$project_id/$PROJECT_NAME:$VERSION
    docker push gcr.io/$project_id/$PROJECT_NAME:$VERSION
    
    # Deploy to Cloud Run or GKE
    if [[ -f "gcp/cloud-run.yaml" ]]; then
        deploy_gcp_cloud_run $project_id
    elif [[ -f "gcp/gke-deployment.yaml" ]]; then
        deploy_gcp_gke $project_id
    else
        print_error "No GCP deployment configuration found"
        exit 1
    fi
    
    print_success "GCP deployment completed"
}

# Function to deploy to Azure
deploy_azure() {
    print_status "Deploying to Azure..."
    
    # Check if az CLI is available
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Get Azure Container Registry
    local acr_name=$(az acr list --query "[0].name" -o tsv)
    if [[ -z "$acr_name" ]]; then
        print_error "No Azure Container Registry found"
        exit 1
    fi
    
    # Build and push to ACR
    az acr build --registry $acr_name --image $PROJECT_NAME:$VERSION .
    
    # Deploy to AKS or Container Instances
    if [[ -f "azure/aks-deployment.yaml" ]]; then
        deploy_azure_aks $acr_name
    elif [[ -f "azure/aci-deployment.yaml" ]]; then
        deploy_azure_aci $acr_name
    else
        print_error "No Azure deployment configuration found"
        exit 1
    fi
    
    print_success "Azure deployment completed"
}

# Function to perform health checks
perform_health_checks() {
    print_status "Performing health checks..."
    
    local health_url=""
    case $PLATFORM in
        "docker")
            health_url="http://localhost:8501/_stcore/health"
            ;;
        "kubernetes")
            health_url="http://localhost:8080/_stcore/health"
            ;;
        *)
            health_url="http://localhost:8501/_stcore/health"
            ;;
    esac
    
    # Wait for service to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s $health_url > /dev/null; then
            print_success "Health check passed"
            return 0
        fi
        
        print_status "Health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    return 1
}

# Function to show deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo
    echo "Deployment Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Platform: $PLATFORM"
    echo "  Version: $VERSION"
    echo "  Project: $PROJECT_NAME"
    echo
    
    case $PLATFORM in
        "docker")
            echo "Access URLs:"
            echo "  Application: http://localhost:8501"
            echo "  Neo4j Browser: http://localhost:7474"
            echo "  Redis: localhost:6379"
            echo
            echo "To view logs: docker-compose logs -f"
            echo "To stop: docker-compose down"
            ;;
        "kubernetes")
            echo "Access URLs:"
            echo "  Application: http://localhost:8080"
            echo
            echo "To view logs: kubectl logs -f deployment/$PROJECT_NAME -n $PROJECT_NAME"
            echo "To stop: kubectl delete namespace $PROJECT_NAME"
            ;;
        *)
            echo "Check your cloud platform console for access URLs"
            ;;
    esac
}

# Main deployment function
main() {
    print_status "Starting deployment of Energy Grid Management Agent"
    print_status "Environment: $ENVIRONMENT"
    print_status "Platform: $PLATFORM"
    print_status "Version: $VERSION"
    echo
    
    # Validate environment variables
    validate_env_vars
    
    # Run tests
    run_tests
    
    # Build Docker image
    build_docker_image
    
    # Deploy based on platform
    case $PLATFORM in
        "docker")
            deploy_docker_compose
            ;;
        "kubernetes")
            deploy_kubernetes
            ;;
        "aws")
            deploy_aws
            ;;
        "gcp")
            deploy_gcp
            ;;
        "azure")
            deploy_azure
            ;;
        *)
            print_error "Unsupported platform: $PLATFORM"
            exit 1
            ;;
    esac
    
    # Perform health checks
    perform_health_checks
    
    # Show deployment information
    show_deployment_info
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -t|--target)
            BUILD_TARGET="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -f|--force)
            FORCE_REBUILD=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    exit 1
fi

if [[ ! "$PLATFORM" =~ ^(docker|kubernetes|aws|gcp|azure)$ ]]; then
    print_error "Invalid platform: $PLATFORM"
    exit 1
fi

if [[ ! "$BUILD_TARGET" =~ ^(production|development)$ ]]; then
    print_error "Invalid build target: $BUILD_TARGET"
    exit 1
fi

# Run main deployment
main 