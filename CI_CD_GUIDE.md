# CI/CD Pipeline Guide

## Overview

This guide explains the CI/CD pipeline setup for the Multi-Agent RAG system using Jenkins, Docker, and GitHub.

## Table of Contents

1. [Pipeline Architecture](#pipeline-architecture)
2. [Prerequisites](#prerequisites)
3. [Jenkins Setup](#jenkins-setup)
4. [Pipeline Stages](#pipeline-stages)
5. [Deployment](#deployment)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Pipeline Architecture

The CI/CD pipeline automates:

- **Code Quality**: Linting, security scanning
- **Testing**: Unit tests, integration tests, smoke tests
- **Build**: Docker image creation
- **Security**: Container vulnerability scanning
- **Deploy**: Automated deployment to staging
- **Health Checks**: Post-deployment validation

### Pipeline Flow

```
GitHub Push → Jenkins Webhook → Build → Test → Docker Build → Push → Deploy → Verify
```

---

## Prerequisites

### 1. Jenkins Server

Install Jenkins with required plugins:

```bash
# Install Jenkins (Ubuntu/Debian)
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources/list.d/jenkins.list'
sudo apt update
sudo apt install jenkins

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

Access Jenkins at: `http://your-server:8080`

### 2. Required Jenkins Plugins

Install these plugins via Jenkins UI (Manage Jenkins → Plugins):

- **Pipeline** (Multibranch Pipeline)
- **Git Plugin**
- **Docker Pipeline**
- **Credentials Binding**
- **Blue Ocean** (optional, for better UI)
- **JUnit Plugin**
- **HTML Publisher** (for coverage reports)

### 3. Docker on Jenkins Server

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add Jenkins user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### 4. Python on Jenkins Server

```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip
```

---

## Jenkins Setup

### Step 1: Create Jenkins Credentials

Go to **Jenkins → Manage Jenkins → Credentials → Global → Add Credentials**

Create the following credentials:

#### 1. Docker Hub Credentials
- **Kind**: Username with password
- **ID**: `docker-hub-credentials`
- **Username**: Your Docker Hub username
- **Password**: Your Docker Hub password/token

#### 2. OpenAI API Key
- **Kind**: Secret text
- **ID**: `openai-api-key`
- **Secret**: Your OpenAI API key

#### 3. Weaviate Credentials
- **Kind**: Secret text
- **ID**: `weaviate-credentials`
- **Secret**: JSON with Weaviate credentials
```json
{
  "url": "your-weaviate-cluster-url",
  "api_key": "your-weaviate-api-key",
  "collection": "Playbooks"
}
```

#### 4. PostgreSQL Password
- **Kind**: Secret text
- **ID**: `postgres-password`
- **Secret**: Your PostgreSQL password

### Step 2: Create Pipeline Job

1. **New Item** → Enter name: `multi-agent-rag-pipeline`
2. Select **Pipeline** → OK
3. Configure:
   - **General**:
     - Check "GitHub project"
     - Project URL: `https://github.com/satishrajv/multi_agent_rag`

   - **Build Triggers**:
     - Check "GitHub hook trigger for GITScm polling"

   - **Pipeline**:
     - Definition: **Pipeline script from SCM**
     - SCM: **Git**
     - Repository URL: `https://github.com/satishrajv/multi_agent_rag.git`
     - Branch: `*/master`
     - Script Path: `Jenkinsfile`

4. **Save**

### Step 3: Configure GitHub Webhook

1. Go to your GitHub repository: `https://github.com/satishrajv/multi_agent_rag`
2. Navigate to **Settings → Webhooks → Add webhook**
3. Configure:
   - **Payload URL**: `http://your-jenkins-server:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Events**: Select "Just the push event"
   - Check "Active"
4. **Add webhook**

---

## Pipeline Stages

### 1. Checkout
- Clones the repository
- Retrieves commit information

### 2. Environment Setup
- Creates Python virtual environment
- Upgrades pip

### 3. Install Dependencies
- Installs all Python packages from `requirements.txt`

### 4. Code Quality Checks (Parallel)

#### Linting
- **Flake8**: Code style checker
- **Pylint**: Code analysis

#### Security Scan
- **Safety**: Checks dependencies for vulnerabilities
- **Bandit**: Scans code for security issues

### 5. Run Tests
- Executes unit tests with pytest
- Generates coverage reports
- Publishes test results

### 6. Build Docker Image
- Builds Docker image from `Dockerfile`
- Tags with build number and `latest`

### 7. Docker Image Scan
- Uses Trivy to scan for vulnerabilities
- Checks for HIGH and CRITICAL issues

### 8. Integration Tests
- Starts PostgreSQL and Redis
- Tests database connectivity
- Cleans up services

### 9. Push Docker Image (master branch only)
- Authenticates with Docker registry
- Pushes tagged images

### 10. Deploy to Staging (master branch only)
- Deploys using `docker-compose.prod.yml`
- Configures environment variables
- Starts all services

### 11. Smoke Tests (master branch only)
- Verifies application health endpoint
- Checks database connectivity
- Validates Redis connection

---

## Deployment

### Local Docker Deployment

```bash
# Build and run locally
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Production Deployment

1. **Prepare Environment Variables**

Create `.env.prod` file:
```bash
OPENAI_API_KEY=your-openai-api-key
WEAVIATE_URL=your-weaviate-url
WEAVIATE_API_KEY=your-weaviate-api-key
WEAVIATE_COLLECTION=Playbooks
POSTGRES_PASSWORD=secure-password-here
```

2. **Deploy**

```bash
# Load environment variables
export $(cat .env.prod | xargs)

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl http://localhost:8501/_stcore/health
```

3. **Access Application**
- Streamlit UI: `http://your-server:8501`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

## Monitoring

### Jenkins Build Status

Check build status at: `http://your-jenkins-server:8080/job/multi-agent-rag-pipeline/`

### Application Logs

```bash
# View application logs
docker logs -f multiagent_rag_app

# View PostgreSQL logs
docker logs -f multiagent_rag_postgres

# View Redis logs
docker logs -f multiagent_rag_redis
```

### Health Checks

```bash
# Application health
curl http://localhost:8501/_stcore/health

# Database health
docker exec multiagent_rag_postgres pg_isready -U raguser

# Redis health
docker exec multiagent_rag_redis redis-cli ping
```

### Query Analytics

```bash
# View stored queries
python scripts/view_query_chunks.py

# View chunk details
python scripts/view_chunks_clear.py
```

---

## Troubleshooting

### Pipeline Issues

#### Build Fails at Checkout
**Problem**: Cannot connect to GitHub
**Solution**:
```bash
# Verify Git is installed on Jenkins
git --version

# Check Jenkins Git plugin configuration
# Manage Jenkins → Configure System → Git → Git installations
```

#### Build Fails at Docker Push
**Problem**: Authentication failure
**Solution**:
```bash
# Verify Docker Hub credentials in Jenkins
# Manage Jenkins → Credentials → docker-hub-credentials

# Test Docker login manually
docker login -u your-username
```

#### Tests Fail
**Problem**: Missing test dependencies
**Solution**:
```bash
# Add to requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
```

### Deployment Issues

#### Container Won't Start
**Problem**: Port already in use
**Solution**:
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8501

# Stop conflicting service or change port in docker-compose.prod.yml
```

#### Database Connection Error
**Problem**: PostgreSQL not accessible
**Solution**:
```bash
# Check PostgreSQL container
docker ps | grep postgres

# Check PostgreSQL logs
docker logs multiagent_rag_postgres

# Verify credentials
docker exec multiagent_rag_postgres psql -U raguser -d multiagent_rag -c "SELECT 1;"
```

#### Missing Environment Variables
**Problem**: Application can't find API keys
**Solution**:
```bash
# Verify environment variables are set
docker exec multiagent_rag_app env | grep OPENAI_API_KEY

# Restart with environment variables
docker-compose -f docker-compose.prod.yml down
export OPENAI_API_KEY=your-key
docker-compose -f docker-compose.prod.yml up -d
```

### Security Issues

#### Exposed Secrets
**Problem**: API keys in code
**Solution**:
- Never commit `.env` files
- Use Jenkins credentials
- Use `.env.example` for templates
- Verify `.gitignore` includes `.env`

#### Vulnerable Dependencies
**Problem**: Safety or Bandit reports issues
**Solution**:
```bash
# Update vulnerable packages
pip install --upgrade package-name

# Check for updates
pip list --outdated
```

---

## Best Practices

### 1. Environment Management
- Use separate `.env` files for dev/staging/prod
- Never commit secrets to Git
- Rotate API keys regularly

### 2. Docker Images
- Tag images with version numbers
- Use multi-stage builds for smaller images
- Scan images for vulnerabilities

### 3. Testing
- Write unit tests for critical functions
- Add integration tests for API endpoints
- Run tests locally before pushing

### 4. Monitoring
- Set up log aggregation (ELK, Splunk)
- Configure alerts for failures
- Monitor resource usage

### 5. Documentation
- Update README when adding features
- Document environment variables
- Maintain changelog

---

## Additional Resources

### Jenkins Documentation
- [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker Pipeline Plugin](https://plugins.jenkins.io/docker-workflow/)
- [Credentials Plugin](https://plugins.jenkins.io/credentials/)

### Docker Documentation
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Docker Security](https://docs.docker.com/engine/security/)

### Security Tools
- [Trivy Scanner](https://github.com/aquasecurity/trivy)
- [Bandit](https://bandit.readthedocs.io/)
- [Safety](https://pyup.io/safety/)

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/satishrajv/multi_agent_rag/issues
- Review logs: `docker-compose logs -f`
- Check Jenkins console output

---

## Summary

This CI/CD pipeline provides:
- Automated testing and quality checks
- Secure credential management
- Container-based deployment
- Health monitoring
- Production-ready configuration

Next steps:
1. Set up Jenkins server
2. Configure credentials
3. Create pipeline job
4. Set up GitHub webhook
5. Push code to trigger build
