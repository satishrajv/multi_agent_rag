# Jenkins Quick Start - Choose Your Path

## 🏠 Path 1: Local Jenkins (Start Here)

### ⚡ Quick Setup (5 minutes)

```bash
# 1. Navigate to jenkins folder
cd jenkins

# 2. Run setup script
setup-jenkins-local.bat

# 3. Copy the password shown
# 4. Open http://localhost:8080
# 5. Paste password and follow wizard
```

**Full Guide**: [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)

---

## ☁️ Path 2: AWS EC2 Jenkins (Production)

### 📋 Prerequisites
- AWS Account
- Credit card for billing (~$15-30/month)
- Completed local testing

### 🚀 Quick Steps

1. **Launch EC2 Instance** (10 min)
   - Instance type: t3.medium
   - OS: Ubuntu 22.04
   - Security: Allow ports 22, 8080, 8501

2. **Install Software** (10 min)
   ```bash
   # SSH into instance
   ssh -i jenkins-key.pem ubuntu@YOUR_PUBLIC_IP

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Clone and start
   git clone https://github.com/satishrajv/multi_agent_rag.git
   cd multi_agent_rag/jenkins
   docker-compose up -d
   ```

3. **Access Jenkins**
   - URL: http://YOUR_PUBLIC_IP:8080
   - Configure as before

**Full Guide**: [AWS_EC2_SETUP_GUIDE.md](AWS_EC2_SETUP_GUIDE.md)

---

## 📊 Comparison

| Feature | Local | AWS EC2 |
|---------|-------|---------|
| **Cost** | Free | ~$20/month |
| **Setup Time** | 5 min | 30 min |
| **Availability** | When PC is on | 24/7 |
| **GitHub Webhooks** | No | Yes |
| **Best For** | Learning, Testing | Production |

---

## 🎯 Recommended Path

1. **Week 1**: Use **Local Jenkins**
   - Learn Jenkins basics
   - Test pipeline locally
   - Experiment freely

2. **Week 2+**: Move to **AWS EC2**
   - Deploy production setup
   - Enable GitHub webhooks
   - Team collaboration

---

## 🆘 Need Help?

- **Local Setup**: See [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)
- **AWS Setup**: See [AWS_EC2_SETUP_GUIDE.md](AWS_EC2_SETUP_GUIDE.md)
- **CI/CD Pipeline**: See [../CI_CD_GUIDE.md](../CI_CD_GUIDE.md)
- **Issues**: Check troubleshooting sections in guides

---

## 📞 Quick Commands

### Local Jenkins
```bash
# Start
cd jenkins && setup-jenkins-local.bat

# Stop
docker-compose down

# Logs
docker logs -f jenkins_local

# Password
docker exec jenkins_local cat /var/jenkins_home/secrets/initialAdminPassword
```

### AWS Jenkins
```bash
# SSH connect
ssh -i jenkins-key.pem ubuntu@YOUR_PUBLIC_IP

# Start/Stop
docker-compose up -d
docker-compose down

# Logs
docker logs -f jenkins_local
```

---

**Start Local Now!** Run `jenkins\setup-jenkins-local.bat` and open http://localhost:8080
