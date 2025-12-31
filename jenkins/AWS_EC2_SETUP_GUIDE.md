# AWS EC2 Jenkins Setup Guide

## Overview

This guide helps you migrate your local Jenkins to AWS EC2 for production use.

---

## Part 1: AWS Account Setup

### Prerequisites

1. AWS Account (create at https://aws.amazon.com)
2. Credit card for AWS billing
3. Basic understanding of SSH

### Cost Estimate

| Instance Type | vCPU | RAM | Storage | Monthly Cost |
|--------------|------|-----|---------|--------------|
| t3.small | 2 | 2GB | 20GB | ~$15 |
| t3.medium | 2 | 4GB | 20GB | ~$30 |
| t3.large | 2 | 8GB | 20GB | ~$60 |

**Recommended**: t3.small for testing, t3.medium for production

---

## Part 2: Launch EC2 Instance

### Step 1: Launch Instance

1. Log in to AWS Console: https://console.aws.amazon.com
2. Navigate to **EC2 Dashboard**
3. Click **Launch Instance**

### Step 2: Configure Instance

#### Name and Tags
- **Name**: `jenkins-server`

#### Application and OS Images (Amazon Machine Image)
- **OS**: Ubuntu Server 22.04 LTS
- **Architecture**: 64-bit (x86)

#### Instance Type
- **Type**: `t3.medium` (2 vCPU, 4GB RAM)

#### Key Pair (login)
- Click **Create new key pair**
- **Name**: `jenkins-key`
- **Type**: RSA
- **Format**: `.pem` (for SSH)
- Click **Create key pair**
- **IMPORTANT**: Save `jenkins-key.pem` file securely!

#### Network Settings

Click **Edit** and configure:

**Firewall (Security Groups)**:
- [x] Create security group
- **Name**: `jenkins-security-group`
- **Description**: Security group for Jenkins server

**Inbound Security Group Rules**:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| Custom TCP | TCP | 8080 | Anywhere (0.0.0.0/0) | Jenkins UI |
| Custom TCP | TCP | 8501 | Anywhere (0.0.0.0/0) | Streamlit App |

#### Configure Storage
- **Size**: 30 GB
- **Type**: gp3 (General Purpose SSD)

### Step 3: Launch

1. Review all settings
2. Click **Launch Instance**
3. Wait for instance to be in **Running** state

### Step 4: Get Public IP

1. Go to **EC2 Dashboard → Instances**
2. Select your `jenkins-server` instance
3. Copy the **Public IPv4 address** (e.g., 3.145.123.45)

---

## Part 3: Connect to EC2 Instance

### Windows (using Command Prompt or PowerShell)

```bash
# Navigate to where you saved jenkins-key.pem
cd C:\Users\YourName\Downloads

# Set permissions (if needed)
icacls jenkins-key.pem /inheritance:r
icacls jenkins-key.pem /grant:r "%username%":"(R)"

# Connect via SSH
ssh -i jenkins-key.pem ubuntu@YOUR_PUBLIC_IP
```

### Alternative: Use PuTTY on Windows

1. Download PuTTY: https://www.putty.org/
2. Convert .pem to .ppk using PuTTYgen
3. Use PuTTY to connect with the .ppk file

---

## Part 4: Install Software on EC2

Once connected via SSH, run these commands:

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify
docker --version
```

**IMPORTANT**: Log out and log back in for docker group changes to take effect:
```bash
exit
# SSH back in
ssh -i jenkins-key.pem ubuntu@YOUR_PUBLIC_IP
```

### Install Docker Compose

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
```

### Install Git

```bash
sudo apt install -y git
git --version
```

---

## Part 5: Deploy Jenkins on EC2

### Clone Your Repository

```bash
cd ~
git clone https://github.com/satishrajv/multi_agent_rag.git
cd multi_agent_rag/jenkins
```

### Start Jenkins

```bash
# Start Jenkins with docker-compose
docker-compose up -d

# Check status
docker ps

# View logs
docker logs -f jenkins_local
```

### Get Initial Admin Password

```bash
docker exec jenkins_local cat /var/jenkins_home/secrets/initialAdminPassword
```

**Copy this password!**

### Access Jenkins UI

Open browser: **http://YOUR_PUBLIC_IP:8080**

Example: http://3.145.123.45:8080

---

## Part 6: Configure Jenkins on EC2

### Initial Setup

1. Paste the initial admin password
2. Select **Install suggested plugins**
3. Create admin user
4. Jenkins URL: `http://YOUR_PUBLIC_IP:8080` (or use domain if you have one)

### Install Additional Required Software

```bash
# SSH into Jenkins container
docker exec -it jenkins_local bash

# Install Docker CLI
apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce-cli

# Install Python
apt-get install -y python3 python3-pip python3-venv

# Install other tools
apt-get install -y jq curl

# Verify
docker --version
python3 --version
jq --version

exit
```

### Configure Credentials

Same as local setup (see LOCAL_SETUP_GUIDE.md):
1. Docker Hub credentials
2. OpenAI API key
3. Weaviate credentials
4. PostgreSQL password

### Create Pipeline Job

Same as local setup (see LOCAL_SETUP_GUIDE.md)

---

## Part 7: Set Up GitHub Webhook

### Get Jenkins Webhook URL

Format: `http://YOUR_PUBLIC_IP:8080/github-webhook/`

Example: `http://3.145.123.45:8080/github-webhook/`

### Configure in GitHub

1. Go to https://github.com/satishrajv/multi_agent_rag
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Configure:
   - **Payload URL**: `http://YOUR_PUBLIC_IP:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Which events**: Select "Just the push event"
   - [x] Active
4. Click **Add webhook**

### Test Webhook

1. Make a small change to your repo
2. Push to GitHub
3. Jenkins should automatically trigger a build!

---

## Part 8: Deploy Your Application

### Create Environment File on EC2

```bash
cd ~/multi_agent_rag

# Create .env file with your secrets
nano .env
```

Add your configuration:
```bash
OPENAI_API_KEY=your-actual-openai-key
WEAVIATE_URL=your-weaviate-url
WEAVIATE_API_KEY=your-weaviate-key
WEAVIATE_COLLECTION=Playbooks
POSTGRES_PASSWORD=your-postgres-password
```

Save: Ctrl+X, Y, Enter

### Deploy Application Stack

```bash
# Start PostgreSQL, Redis, and Application
docker-compose -f docker-compose.prod.yml up -d

# Check services
docker ps

# View app logs
docker logs -f multiagent_rag_app
```

### Access Your Application

**Streamlit UI**: http://YOUR_PUBLIC_IP:8501

Example: http://3.145.123.45:8501

---

## Part 9: Domain Setup (Optional)

### Option 1: Use AWS Route 53

1. Register domain or transfer existing domain to Route 53
2. Create hosted zone
3. Add A record pointing to your EC2 public IP

### Option 2: Use Existing Domain

1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Add A record:
   - **Type**: A
   - **Name**: jenkins (or app, or @)
   - **Value**: Your EC2 public IP
   - **TTL**: 3600

Example:
- jenkins.yourdomain.com → Your EC2 IP
- app.yourdomain.com → Your EC2 IP

### Update Jenkins URL

1. Go to Jenkins: **Manage Jenkins → System**
2. **Jenkins URL**: `http://jenkins.yourdomain.com:8080`
3. Save

---

## Part 10: Security Hardening

### Enable HTTPS (Optional but Recommended)

#### Install Nginx as Reverse Proxy

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

#### Configure Nginx for Jenkins

```bash
sudo nano /etc/nginx/sites-available/jenkins
```

Add:
```nginx
server {
    listen 80;
    server_name jenkins.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/jenkins /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Get SSL Certificate

```bash
sudo certbot --nginx -d jenkins.yourdomain.com
```

Now access: **https://jenkins.yourdomain.com**

### Restrict SSH Access

Update security group to allow SSH only from your IP:

1. EC2 Console → Security Groups → jenkins-security-group
2. Edit inbound rules
3. SSH rule: Change source from "Anywhere" to "My IP"

### Enable EC2 Instance Backup

1. EC2 Console → Elastic Block Store → Snapshots
2. Create snapshot schedule
3. Or use AWS Backup service

---

## Part 11: Monitoring & Maintenance

### CloudWatch Monitoring

1. EC2 Console → Select instance
2. **Monitoring** tab
3. Enable detailed monitoring

### Set Up Alarms

1. CloudWatch → Alarms → Create alarm
2. Monitor:
   - CPU utilization
   - Disk usage
   - Network traffic

### Backup Jenkins Configuration

```bash
# Backup Jenkins home
docker exec jenkins_local tar czf /tmp/jenkins_backup.tar.gz /var/jenkins_home

# Copy from container to host
docker cp jenkins_local:/tmp/jenkins_backup.tar.gz ~/jenkins_backup.tar.gz

# Download to local machine (from your PC)
scp -i jenkins-key.pem ubuntu@YOUR_PUBLIC_IP:~/jenkins_backup.tar.gz .
```

### Update Jenkins

```bash
cd ~/multi_agent_rag/jenkins

# Pull latest Jenkins image
docker-compose pull

# Restart with new image
docker-compose up -d
```

---

## Part 12: Cost Optimization

### Use Elastic IP (Optional)

If you stop/start your instance, the public IP changes. Elastic IP prevents this:

1. EC2 Console → Elastic IPs → Allocate Elastic IP
2. Associate with your jenkins-server instance
3. **Cost**: Free while instance is running, $3.60/month if not associated

### Auto Shutdown for Testing

Create cron job to stop instance at night:

```bash
# Edit crontab
crontab -e

# Add line to stop at midnight (optional)
0 0 * * * sudo shutdown -h now
```

### Use Spot Instances (Advanced)

Save up to 70% by using Spot Instances for non-critical workloads.

---

## Migration Checklist

- [ ] Launch EC2 instance
- [ ] Configure security groups
- [ ] Install Docker and Docker Compose
- [ ] Clone repository
- [ ] Start Jenkins container
- [ ] Configure Jenkins (plugins, credentials)
- [ ] Create pipeline job
- [ ] Set up GitHub webhook
- [ ] Deploy application stack
- [ ] Test end-to-end pipeline
- [ ] (Optional) Configure domain
- [ ] (Optional) Enable HTTPS
- [ ] Set up backups
- [ ] Configure monitoring

---

## Comparison: Local vs AWS EC2

| Feature | Local | AWS EC2 |
|---------|-------|---------|
| **Access URL** | localhost:8080 | public-ip:8080 |
| **GitHub Webhooks** | ❌ No | ✅ Yes |
| **Uptime** | When PC is on | 24/7 |
| **Performance** | PC resources | Dedicated |
| **Cost** | Free | $15-30/month |
| **Scalability** | Limited | Easy to scale |
| **Team Access** | No | Yes |

---

## Troubleshooting

### Can't SSH into EC2

**Check**:
1. Security group allows SSH from your IP
2. Instance is running
3. Using correct key pair file
4. Using correct username (`ubuntu`)

### Can't Access Jenkins UI

**Check**:
1. Jenkins container is running: `docker ps`
2. Security group allows port 8080
3. Using public IP, not private IP
4. Jenkins has finished starting: `docker logs jenkins_local`

### Webhook Not Working

**Check**:
1. Webhook URL is correct: `http://YOUR_PUBLIC_IP:8080/github-webhook/`
2. Security group allows port 8080 from anywhere
3. Jenkins has GitHub Integration plugin
4. Pipeline is configured for webhook triggers

---

## Next Steps

1. Test local Jenkins first
2. Launch EC2 when ready for production
3. Migrate credentials and jobs
4. Enable GitHub webhooks
5. Deploy application
6. Monitor and optimize

---

## Support

- AWS Documentation: https://docs.aws.amazon.com/ec2/
- Jenkins Documentation: https://www.jenkins.io/doc/
- Your repository: https://github.com/satishrajv/multi_agent_rag

---

**Ready for Production!** 🚀

Your Jenkins server is now running on AWS EC2 with automatic builds triggered by GitHub pushes.
