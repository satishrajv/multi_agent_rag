# Jenkins Local Setup Guide

## Quick Start (5 Minutes)

### Step 1: Start Jenkins

```bash
# Navigate to jenkins folder
cd jenkins

# Run setup script (Windows)
setup-jenkins-local.bat

# OR manually with docker-compose
docker-compose up -d
```

### Step 2: Get Initial Password

```bash
# The setup script shows this automatically, or run:
docker exec jenkins_local cat /var/jenkins_home/secrets/initialAdminPassword
```

### Step 3: Access Jenkins

1. Open browser: **http://localhost:8080**
2. Paste the initial admin password
3. Click **Continue**

### Step 4: Install Plugins

1. Select **"Install suggested plugins"**
2. Wait for installation to complete (2-3 minutes)

### Step 5: Create Admin User

Fill in the form:
- Username: `admin` (or your choice)
- Password: `admin123` (or your choice)
- Full name: Your name
- Email: Your email

Click **Save and Continue** → **Save and Finish** → **Start using Jenkins**

---

## Configure Jenkins for Your Pipeline

### Install Required Plugins

Go to **Manage Jenkins → Plugins → Available plugins**

Search and install:
- [x] **Pipeline**
- [x] **Git plugin**
- [x] **Docker Pipeline**
- [x] **Credentials Binding**
- [x] **GitHub Integration**

Click **Install without restart** or **Download now and install after restart**

### Add Credentials

Go to **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

#### 1. Docker Hub Credentials

- **Kind**: Username with password
- **Scope**: Global
- **Username**: Your Docker Hub username
- **Password**: Your Docker Hub password/token
- **ID**: `docker-hub-credentials`
- **Description**: Docker Hub Login
- Click **Create**

#### 2. OpenAI API Key

- **Kind**: Secret text
- **Scope**: Global
- **Secret**: Your OpenAI API key (sk-proj-...)
- **ID**: `openai-api-key`
- **Description**: OpenAI API Key
- Click **Create**

#### 3. Weaviate Credentials

- **Kind**: Secret text
- **Scope**: Global
- **Secret**: Paste this JSON (update with your values):
  ```json
  {
    "url": "your-weaviate-cluster-url",
    "api_key": "your-weaviate-api-key",
    "collection": "Playbooks"
  }
  ```
- **ID**: `weaviate-credentials`
- **Description**: Weaviate Cloud Credentials
- Click **Create**

#### 4. PostgreSQL Password

- **Kind**: Secret text
- **Scope**: Global
- **Secret**: `ragpassword123` (or your choice)
- **ID**: `postgres-password`
- **Description**: PostgreSQL Password
- Click **Create**

### Install Docker in Jenkins Container

Jenkins needs Docker CLI to run your pipeline:

```bash
# Enter Jenkins container
docker exec -it jenkins_local bash

# Install Docker CLI
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce-cli

# Install Python and tools
apt-get install -y python3 python3-pip python3-venv

# Install jq (for JSON parsing)
apt-get install -y jq

# Verify installations
docker --version
python3 --version
jq --version

# Exit container
exit
```

---

## Create Your First Pipeline Job

### Step 1: New Item

1. Click **New Item** (top left)
2. Enter name: `multi-agent-rag-pipeline`
3. Select **Pipeline**
4. Click **OK**

### Step 2: Configure Pipeline

#### General Tab
- [x] Check **GitHub project**
- Project url: `https://github.com/satishrajv/multi_agent_rag/`

#### Build Triggers Tab
- [x] Check **Poll SCM** (for local testing)
- Schedule: `H/5 * * * *` (checks every 5 minutes)

**Note**: For production with GitHub webhooks, use "GitHub hook trigger for GITScm polling"

#### Pipeline Tab
- **Definition**: Pipeline script from SCM
- **SCM**: Git
- **Repository URL**: `https://github.com/satishrajv/multi_agent_rag.git`
- **Credentials**: - none - (public repo)
- **Branch Specifier**: `*/master`
- **Script Path**: `Jenkinsfile`

### Step 3: Save and Build

1. Click **Save**
2. Click **Build Now**
3. Watch the build progress in **Build History**
4. Click on build number (e.g., #1) → **Console Output** to see logs

---

## Testing the Pipeline Locally

### Modify Jenkinsfile for Local Testing

Since you're running locally, you might want to skip the "Push Docker Image" and "Deploy to Staging" stages initially.

Edit your Jenkinsfile (optional):

```groovy
// Comment out or modify the 'when' condition for local testing
stage('Push Docker Image') {
    when {
        branch 'master'
        // Add this for local testing:
        // expression { return false }  // Disable for local testing
    }
    // ...
}
```

### Run a Test Build

1. Go to your pipeline: http://localhost:8080/job/multi-agent-rag-pipeline/
2. Click **Build Now**
3. Click on the build number in **Build History**
4. Click **Console Output**

Expected stages:
- ✓ Checkout
- ✓ Environment Setup
- ✓ Install Dependencies
- ✓ Code Quality Checks
- ✓ Run Tests
- ✓ Build Docker Image
- ✓ Docker Image Scan
- ✓ Integration Tests

---

## Troubleshooting

### Issue: Docker Socket Permission Denied

**Error**: `permission denied while trying to connect to the Docker daemon socket`

**Solution**:
```bash
# Give Jenkins container access to Docker socket
docker exec -u root jenkins_local chmod 666 /var/run/docker.sock
```

### Issue: Python Not Found

**Error**: `python3: command not found`

**Solution**: Install Python in Jenkins container (see "Install Docker in Jenkins Container" above)

### Issue: Build Stays in Queue

**Problem**: Build doesn't start

**Solution**:
1. Go to **Manage Jenkins → Nodes → Built-In Node**
2. Click **Configure**
3. Set **# of executors** to `2`
4. Click **Save**

### Issue: Can't Access Jenkins UI

**Problem**: http://localhost:8080 doesn't load

**Solution**:
```bash
# Check if Jenkins is running
docker ps | findstr jenkins_local

# Check Jenkins logs
docker logs jenkins_local

# Restart Jenkins
cd jenkins
docker-compose restart
```

### Issue: Credentials Not Working

**Problem**: Pipeline can't access credentials

**Solution**:
1. Verify credentials IDs match exactly:
   - `docker-hub-credentials`
   - `openai-api-key`
   - `weaviate-credentials`
   - `postgres-password`

2. Check credentials scope is **Global**

3. Test credentials in pipeline:
   ```groovy
   stage('Test Credentials') {
       steps {
           withCredentials([string(credentialsId: 'openai-api-key', variable: 'API_KEY')]) {
               sh 'echo "API Key length: ${#API_KEY}"'
           }
       }
   }
   ```

---

## Useful Commands

```bash
# View Jenkins logs
docker logs -f jenkins_local

# Restart Jenkins
docker restart jenkins_local

# Stop Jenkins
cd jenkins
docker-compose down

# Start Jenkins
cd jenkins
docker-compose up -d

# Access Jenkins container shell
docker exec -it jenkins_local bash

# View Jenkins home directory
docker exec jenkins_local ls -la /var/jenkins_home

# Backup Jenkins configuration
docker cp jenkins_local:/var/jenkins_home ./jenkins_backup

# Get admin password again
docker exec jenkins_local cat /var/jenkins_home/secrets/initialAdminPassword
```

---

## Next Steps

Once your local Jenkins is working:

1. **Test Pipeline Stages**: Run builds and verify each stage works
2. **Configure GitHub Webhook**: For automatic builds on push
3. **Optimize Build Time**: Cache dependencies, parallel stages
4. **Move to AWS EC2**: Follow AWS_EC2_SETUP_GUIDE.md (coming next)

---

## Local vs Production Differences

| Feature | Local Jenkins | AWS EC2 Jenkins |
|---------|--------------|-----------------|
| Access | localhost:8080 | public-ip:8080 |
| Uptime | When computer is on | 24/7 |
| Performance | Your PC resources | Dedicated server |
| Webhooks | Manual/polling | GitHub webhooks |
| Cost | Free | ~$15-30/month |
| Setup | 5 minutes | 30 minutes |

---

## Getting Help

- Jenkins not starting? Check: `docker logs jenkins_local`
- Build failing? Check: Console Output in Jenkins UI
- Need to reset? Run: `docker-compose down -v` (deletes all data!)

Your Jenkins is now ready! 🎉

Access it at: **http://localhost:8080**
