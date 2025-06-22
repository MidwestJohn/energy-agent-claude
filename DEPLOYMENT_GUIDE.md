# Deployment Guide

## Energy Grid Management Agent

This guide covers deployment of the Energy Grid Management Agent across different environments and platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Cloud Platform Deployment](#cloud-platform-deployment)
7. [Monitoring & Observability](#monitoring--observability)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Python**: 3.11 or higher
- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **Memory**: Minimum 4GB RAM, 8GB recommended
- **Storage**: 10GB free space

### Required Accounts & Services

- **Claude AI**: API key from [Anthropic Console](https://console.anthropic.com)
- **Neo4j**: Database instance (AuraDB or self-hosted)
- **Cloud Platform**: AWS, GCP, or Azure account (for cloud deployment)

### Development Tools

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov black flake8 mypy

# Install Docker (if not already installed)
# Follow instructions at https://docs.docker.com/get-docker/
```

## Environment Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Application Settings
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8501

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_OUTPUT=file
LOG_FILE=logs/energy_agent.log

# Neo4j Database
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
NEO4J_MAX_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30

# Claude AI
CLAUDE_API_KEY=sk-ant-api03-your-api-key
CLAUDE_MODEL=claude-3-sonnet-20240229
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7
CLAUDE_RPM=50
CLAUDE_RPD=10000
CLAUDE_TPM=50000

# Security
ENCRYPTION_KEY=your-32-character-encryption-key
HASH_SALT=your-16-character-salt
SESSION_TIMEOUT=3600

# Performance
CACHE_TTL=300
MAX_WORKERS=4
HEALTH_CHECK_INTERVAL=300

# Service Information
SERVICE_NAME=energy-grid-agent
APP_VERSION=1.0.0
```

### 2. Directory Structure

```bash
mkdir -p logs data exports monitoring/grafana monitoring/prometheus nginx/ssl
```

### 3. Permissions

```bash
# Set proper permissions
chmod +x deploy.sh
chmod 600 .env
```

## Local Development

### 1. Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd energy-agent-claude

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# Run the application
streamlit run app_enhanced.py
```

### 2. Development with Docker

```bash
# Build development image
docker build --target development -t energy-grid-agent:dev .

# Run with Docker Compose
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_energy_tools.py -v
```

## Docker Deployment

### 1. Single Container Deployment

```bash
# Build production image
docker build --target production -t energy-grid-agent:latest .

# Run container
docker run -d \
  --name energy-agent \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  energy-grid-agent:latest
```

### 2. Docker Compose Deployment

```bash
# Deploy all services
docker-compose up -d

# View logs
docker-compose logs -f energy-agent

# Scale application
docker-compose up -d --scale energy-agent=3

# Stop services
docker-compose down
```

### 3. Production Docker Compose

```bash
# Deploy with production profile
docker-compose --profile production up -d

# Deploy with monitoring
docker-compose --profile monitoring up -d
```

### 4. Health Checks

```bash
# Check application health
curl http://localhost:8501/_stcore/health

# Check all services
docker-compose ps

# View health check logs
docker-compose logs energy-agent | grep health
```

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install kubectl
# Follow instructions at https://kubernetes.io/docs/tasks/tools/

# Install Helm (optional)
# Follow instructions at https://helm.sh/docs/intro/install/

# Configure kubectl for your cluster
kubectl config use-context your-cluster-context
```

### 2. Basic Deployment

```bash
# Create namespace
kubectl create namespace energy-grid-agent

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n energy-grid-agent
kubectl get services -n energy-grid-agent
```

### 3. Helm Deployment

```bash
# Add Helm repository (if using external charts)
helm repo add bitnami https://charts.bitnami.com/bitnami

# Install with Helm
helm install energy-agent ./helm/energy-agent \
  --namespace energy-grid-agent \
  --create-namespace \
  --values values-production.yaml

# Upgrade deployment
helm upgrade energy-agent ./helm/energy-agent \
  --namespace energy-grid-agent \
  --values values-production.yaml
```

### 4. Scaling

```bash
# Scale horizontally
kubectl scale deployment energy-agent --replicas=3 -n energy-grid-agent

# Enable auto-scaling
kubectl autoscale deployment energy-agent \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n energy-grid-agent
```

## Cloud Platform Deployment

### 1. AWS Deployment

#### ECS Deployment

```bash
# Configure AWS CLI
aws configure

# Create ECR repository
aws ecr create-repository --repository-name energy-grid-agent

# Build and push image
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

docker tag energy-grid-agent:latest \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/energy-grid-agent:latest

docker push \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/energy-grid-agent:latest

# Deploy to ECS
aws ecs create-cluster --cluster-name energy-agent-cluster
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-definition.json
aws ecs create-service --cli-input-json file://aws/ecs-service-definition.json
```

#### EKS Deployment

```bash
# Create EKS cluster
eksctl create cluster \
  --name energy-agent-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4

# Deploy to EKS
kubectl apply -f aws/eks-deployment.yaml
kubectl apply -f aws/eks-service.yaml
kubectl apply -f aws/eks-ingress.yaml
```

### 2. Google Cloud Platform Deployment

#### Cloud Run Deployment

```bash
# Configure gcloud
gcloud config set project your-project-id

# Build and push to Container Registry
docker tag energy-grid-agent:latest \
  gcr.io/$(gcloud config get-value project)/energy-grid-agent:latest

docker push \
  gcr.io/$(gcloud config get-value project)/energy-grid-agent:latest

# Deploy to Cloud Run
gcloud run deploy energy-grid-agent \
  --image gcr.io/$(gcloud config get-value project)/energy-grid-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

#### GKE Deployment

```bash
# Create GKE cluster
gcloud container clusters create energy-agent-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-medium

# Get credentials
gcloud container clusters get-credentials energy-agent-cluster --zone us-central1-a

# Deploy to GKE
kubectl apply -f gcp/gke-deployment.yaml
```

### 3. Azure Deployment

#### Container Instances

```bash
# Login to Azure
az login

# Create resource group
az group create --name energy-agent-rg --location eastus

# Create container registry
az acr create --resource-group energy-agent-rg \
  --name energyagentregistry --sku Basic

# Build and push to ACR
az acr build --registry energyagentregistry \
  --image energy-grid-agent:latest .

# Deploy to Container Instances
az container create \
  --resource-group energy-agent-rg \
  --name energy-agent \
  --image energyagentregistry.azurecr.io/energy-grid-agent:latest \
  --dns-name-label energy-agent \
  --ports 8501 \
  --environment-variables \
    CLAUDE_API_KEY=your-api-key \
    NEO4J_URI=your-neo4j-uri
```

#### AKS Deployment

```bash
# Create AKS cluster
az aks create \
  --resource-group energy-agent-rg \
  --name energy-agent-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group energy-agent-rg --name energy-agent-cluster

# Deploy to AKS
kubectl apply -f azure/aks-deployment.yaml
```

## Monitoring & Observability

### 1. Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'energy-agent'
    static_configs:
      - targets: ['energy-agent:8501']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:7687']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 2. Grafana Dashboards

Create `monitoring/grafana/dashboards/energy-agent.json`:

```json
{
  "dashboard": {
    "title": "Energy Grid Agent Dashboard",
    "panels": [
      {
        "title": "Application Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"energy-agent\"}",
            "legendFormat": "Application Status"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "http_request_duration_seconds{job=\"energy-agent\"}",
            "legendFormat": "Response Time"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting Rules

Create `monitoring/alerting-rules.yml`:

```yaml
groups:
  - name: energy-agent
    rules:
      - alert: ApplicationDown
        expr: up{job="energy-agent"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Energy Grid Agent is down"
          description: "The application has been down for more than 1 minute"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{job="energy-agent"} > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "Response time is above 5 seconds"
```

### 4. Log Aggregation

```bash
# Using ELK Stack
docker-compose -f monitoring/elk-stack.yml up -d

# Using Fluentd
docker-compose -f monitoring/fluentd.yml up -d
```

## Troubleshooting

### 1. Common Issues

#### Application Won't Start

```bash
# Check logs
docker-compose logs energy-agent

# Check environment variables
docker-compose exec energy-agent env | grep -E "(CLAUDE|NEO4J)"

# Check configuration
docker-compose exec energy-agent python -c "from config import config; print(config.database.URI)"
```

#### Database Connection Issues

```bash
# Test Neo4j connection
docker-compose exec energy-agent python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('neo4j://neo4j:7687', auth=('neo4j', 'password'))
with driver.session() as session:
    result = session.run('RETURN 1')
    print('Connection successful')
driver.close()
"
```

#### API Rate Limiting

```bash
# Check rate limit status
curl http://localhost:8501/api/rate-limit-status

# View rate limit logs
docker-compose logs energy-agent | grep "rate limit"
```

### 2. Performance Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats energy-agent

# Analyze memory usage
docker-compose exec energy-agent python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

#### Slow Database Queries

```bash
# Enable query logging
docker-compose exec neo4j cypher-shell -u neo4j -p password \
  "CALL dbms.setConfigValue('dbms.logs.query.enabled', 'true')"

# View slow queries
docker-compose logs neo4j | grep "slow query"
```

### 3. Security Issues

#### API Key Exposure

```bash
# Check for exposed secrets
grep -r "sk-ant-api03" . --exclude-dir=node_modules --exclude-dir=.git

# Rotate API keys
# 1. Generate new API key in Anthropic console
# 2. Update environment variables
# 3. Restart application
```

#### Unauthorized Access

```bash
# Check access logs
docker-compose logs nginx | grep "401\|403"

# Review firewall rules
iptables -L -n | grep 8501
```

### 4. Recovery Procedures

#### Application Recovery

```bash
# Restart application
docker-compose restart energy-agent

# Rollback to previous version
docker-compose down
docker tag energy-grid-agent:previous energy-grid-agent:latest
docker-compose up -d
```

#### Database Recovery

```bash
# Restore from backup
docker-compose exec neo4j neo4j-admin restore --from=/backups/latest --database=neo4j

# Reset database
docker-compose exec neo4j cypher-shell -u neo4j -p password \
  "MATCH (n) DETACH DELETE n"
```

## Maintenance

### 1. Regular Maintenance Tasks

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f

# Rotate logs
docker-compose exec energy-agent logrotate /etc/logrotate.conf
```

### 2. Backup Procedures

```bash
# Backup Neo4j database
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/$(date +%Y%m%d_%H%M%S).dump

# Backup application data
tar -czf backups/app_data_$(date +%Y%m%d_%H%M%S).tar.gz data/

# Backup configuration
cp .env backups/env_$(date +%Y%m%d_%H%M%S).backup
```

### 3. Monitoring Maintenance

```bash
# Check monitoring stack health
docker-compose -f monitoring/prometheus.yml ps

# Update Grafana dashboards
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/energy-agent.json

# Clean up old metrics
docker-compose exec prometheus promtool tsdb clean --retention.time=30d /prometheus
```

## Support

For additional support:

1. **Documentation**: Check the README.md file
2. **Issues**: Create an issue in the project repository
3. **Logs**: Review application logs for error details
4. **Community**: Join the project's community channels

## Version History

- **v1.0.0**: Initial production release
- **v1.1.0**: Added monitoring and observability
- **v1.2.0**: Enhanced security features
- **v1.3.0**: Cloud platform deployment support 