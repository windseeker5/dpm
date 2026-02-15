# Minipass Deployment Documentation Index

**📚 Choose the right guide for your task:**

---

## 🎯 Quick Navigation

### For Regular LHGI Deployments (Most Common)
👉 **[QUICK_DEPLOY_LHGI.md](QUICK_DEPLOY_LHGI.md)** - 5-step cheat sheet (5 minutes)

**When to use:** You have code changes tested locally and ready to deploy to production LHGI container.

---

### For Detailed Deployment Information
👉 **[VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md)** - Complete production deployment guide

**When to use:**
- First time deploying to production
- Need troubleshooting help
- Want to understand the deployment process in depth
- Need rollback procedures

---

### For Brand New VPS Server Setup
👉 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Generic first-time VPS setup

**When to use:**
- Setting up a completely new VPS from scratch
- Creating a new customer container (not LHGI)
- Need help with Docker installation, Nginx, domains, etc.

---

### For API Keys Setup
👉 **[ENV_SETUP.md](ENV_SETUP.md)** - One-time .env configuration

**When to use:**
- First time setting up API keys (Google Maps, Groq, Unsplash)
- Adding a new customer container that needs API keys
- Updating API keys across all containers

**Note:** This is a ONE-TIME setup. Once done, you don't need it again unless adding new containers.

---

## 🔄 Common Workflows

### "I Fixed Bugs and Want to Deploy to LHGI"
1. Read: [QUICK_DEPLOY_LHGI.md](QUICK_DEPLOY_LHGI.md)
2. Follow the 5 steps
3. Done in 5-7 minutes

### "I'm Setting Up a Brand New Customer Container"
1. Read: [DEPLOYMENT.md](DEPLOYMENT.md) - Initial VPS setup
2. Read: [ENV_SETUP.md](ENV_SETUP.md) - Configure API keys
3. Read: [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) - First deployment

### "I Need to Rollback LHGI Deployment"
1. Read: [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md)
2. Go to "Rollback Procedure" section

### "I Need to Update API Keys"
1. Read: [ENV_SETUP.md](ENV_SETUP.md)
2. Go to "Update API Keys Later" section

---

## 📖 Document Purpose Summary

| Document | Purpose | Audience | Frequency |
|----------|---------|----------|-----------|
| **QUICK_DEPLOY_LHGI.md** | 5-step cheat sheet for LHGI updates | Developer | Every deployment |
| **VPS_DEPLOYMENT_GUIDE.md** | Complete production deployment guide | Developer | Reference as needed |
| **DEPLOYMENT.md** | Generic VPS setup from scratch | Beginner | Once per server |
| **ENV_SETUP.md** | API keys configuration | Developer | Once per container |

---

## 🆘 Help

**Can't find what you need?**

- Deployment issues → [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) - "Troubleshooting" section
- Database issues → [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) - "Database Migrations" section
- Container won't start → [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) - "Troubleshooting" section

---

**Last Updated:** November 2, 2025
