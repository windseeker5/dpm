# Complete Deployment Guide for Minipass

**This guide assumes you know NOTHING about deployment. Follow each step exactly.**

---

## Table of Contents
1. [First-Time Setup (Do Once)](#first-time-setup)
2. [How to Deploy](#how-to-deploy)
3. [How to Update Your App](#how-to-update)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Topics](#advanced-topics)

---

## First-Time Setup (Do Once)

### Step 1: Get a Server

You need a VPS (Virtual Private Server). Good options:
- **DigitalOcean** ($6/month) - easiest for beginners
- **Linode** ($5/month)
- **Vultr** ($6/month)
- **Hetzner** ($4/month)

**What to choose:**
- Operating System: **Ubuntu 22.04 LTS**
- RAM: **At least 2GB** (for multiple customers)
- Storage: **At least 25GB**

After you create it, you'll get:
- An IP address (looks like: `203.0.113.45`)
- A root password (or SSH key)

---

### Step 2: Connect to Your Server

**On Mac/Linux:**
```bash
ssh root@YOUR_SERVER_IP
```
Replace `YOUR_SERVER_IP` with your actual IP (e.g., `203.0.113.45`)

**On Windows:**
- Download and install [PuTTY](https://www.putty.org/)
- Open PuTTY
- Enter your server IP in "Host Name"
- Click "Open"
- Login as `root` with your password

**You're now "inside" your server!** Any commands you type run on the server.

---

### Step 3: Install Docker

Copy and paste these commands one at a time:

```bash
# Update the system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify Docker is installed
docker --version
```

You should see something like: `Docker version 24.0.7, build...`

---

### Step 4: Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify it's installed
docker-compose --version
```

You should see: `Docker Compose version v2.x.x`

---

### Step 5: Install Git

```bash
apt install git -y

# Verify
git --version
```

---

### Step 6: Get Your Code on the Server

**Option A: Using Git (Recommended)**

```bash
# Go to home directory
cd ~

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Go into the app directory
cd YOUR_REPO
```

**Option B: Upload Files Manually**

On your local computer (NOT on the server):
```bash
# Zip your app folder
cd /home/kdresdell/Documents/DEV/minipass_env
tar -czf app.tar.gz app/

# Upload to server (replace YOUR_SERVER_IP)
scp app.tar.gz root@YOUR_SERVER_IP:~/

# Then on the server, unzip it:
cd ~
tar -xzf app.tar.gz
cd app/
```

---

### Step 7: Copy Your .env File to the Server

**IMPORTANT:** Your `.env` file contains your API keys and should NEVER be in git!

On your **local computer**, run:
```bash
# Copy .env to the server
scp /home/kdresdell/Documents/DEV/minipass_env/app/.env root@YOUR_SERVER_IP:~/app/.env
```

**Verify it worked** (on the server):
```bash
cd ~/app
ls -la .env
```

You should see: `-rw-r--r-- 1 root root 1234 Nov 2 12:34 .env`

---

### Step 8: First Deployment

```bash
# Make sure you're in the app directory
cd ~/app

# Make the deploy script executable (first time only)
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

The script will:
1. Check if `.env` exists
2. Check if Docker is installed
3. Build your Docker image
4. Start your container
5. Show you the status

**If everything worked**, you'll see:
```
✓ Deployment Complete!
```

---

### Step 9: Test It Works

Open your web browser and go to:
```
http://YOUR_SERVER_IP:8889
```

You should see your Minipass login page!

---

## How to Deploy

After the first-time setup, deploying is super easy.

### SSH into Your Server
```bash
ssh root@YOUR_SERVER_IP
cd ~/app
```

### Pull Latest Code
```bash
git pull
```

### Deploy
```bash
./deploy.sh
```

That's it! The script does everything for you.

---

## How to Update Your App

### Scenario 1: You Changed Code

1. **On your local computer:** Commit and push to git
   ```bash
   git add .
   git commit -m "Your changes"
   git push
   ```

2. **On your server:**
   ```bash
   cd ~/app
   git pull
   ./deploy.sh
   ```

### Scenario 2: You Changed .env (Added New API Keys)

1. **On your local computer:** Copy the new .env
   ```bash
   scp .env root@YOUR_SERVER_IP:~/app/.env
   ```

2. **On your server:** Restart the container
   ```bash
   cd ~/app
   docker-compose restart
   ```

### Scenario 3: You Just Want to Restart

```bash
cd ~/app
docker-compose restart
```

---

## Troubleshooting

### "I can't access my app at http://MY_IP:8889"

**Check 1: Is the container running?**
```bash
docker-compose ps
```

You should see:
```
NAME                  STATUS
minipass-customer-1   Up 2 minutes (healthy)
```

If it says "Exited" or "Unhealthy", check the logs:
```bash
docker-compose logs minipass-app
```

**Check 2: Is the port open on your firewall?**
```bash
# On Ubuntu with UFW
sudo ufw allow 8889
```

**Check 3: Can you access it from the server itself?**
```bash
curl http://localhost:8889
```

If this works but you can't access from your computer, it's a firewall issue.

---

### "Error: .env file not found"

You forgot to copy your `.env` file!

**On your local computer:**
```bash
scp /home/kdresdell/Documents/DEV/minipass_env/app/.env root@YOUR_SERVER_IP:~/app/.env
```

**Verify it's there:**
```bash
ssh root@YOUR_SERVER_IP
cd ~/app
cat .env
```

You should see your API keys.

---

### "Port 8889 is already in use"

Someone is already using that port. Two options:

**Option 1: Stop the old container**
```bash
docker-compose down
./deploy.sh
```

**Option 2: Use a different port**

Edit `docker-compose.yml`:
```yaml
ports:
  - "8890:8889"  # Changed from 8889 to 8890
```

Then:
```bash
./deploy.sh
```

Access your app at `http://YOUR_SERVER_IP:8890`

---

### "Permission denied" when running deploy.sh

Make it executable:
```bash
chmod +x deploy.sh
```

---

### "git pull says there are conflicts"

You edited files on the server (not recommended). Two options:

**Option 1: Reset to git version (LOSES SERVER CHANGES)**
```bash
git reset --hard
git pull
```

**Option 2: Save your changes first**
```bash
git stash
git pull
git stash pop
```

---

### "Container keeps restarting"

Check the logs to see what's wrong:
```bash
docker-compose logs -f minipass-app
```

Common issues:
- Missing .env file
- Wrong API keys in .env
- Port already in use
- Not enough memory

---

### "How do I see what's happening inside the container?"

**View logs in real-time:**
```bash
docker-compose logs -f minipass-app
```

**Enter the container (like SSH into it):**
```bash
docker exec -it minipass-customer-1 bash
```

Now you're "inside" the container. Type `exit` to leave.

---

### "I broke everything! How do I start over?"

```bash
# Stop and remove everything
docker-compose down

# Remove all Docker images (clean slate)
docker system prune -a

# Deploy again
./deploy.sh
```

---

## Advanced Topics

### Running Multiple Customers

Each customer gets their own container with their own database.

**Edit `docker-compose.yml`** and add:
```yaml
  minipass-customer-2:
    build:
      context: .
      dockerfile: dockerfile
    container_name: minipass-customer-2
    env_file:
      - .env.customer2
    ports:
      - "8890:8889"
    volumes:
      - ./instance-customer2:/app/instance
      - ./static/uploads-customer2:/app/static/uploads
      - ./static/backups-customer2:/app/static/backups
    restart: unless-stopped
```

**Create separate .env files:**
```bash
cp .env .env.customer2
# Edit .env.customer2 if they need different API keys
```

**Start both customers:**
```bash
docker-compose up -d
```

Customer 1: `http://YOUR_IP:8889`
Customer 2: `http://YOUR_IP:8890`

---

### Using a Domain Name Instead of IP

**Step 1: Point your domain to your server**

In your domain registrar (Namecheap, GoDaddy, etc.):
- Add an **A record**
- Name: `@` (for main domain) or `app` (for app.yourdomain.com)
- Value: Your server IP
- TTL: 300

**Step 2: Install Nginx (reverse proxy)**
```bash
apt install nginx -y
```

**Step 3: Create Nginx config**
```bash
nano /etc/nginx/sites-available/minipass
```

Paste this:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 4: Enable it**
```bash
ln -s /etc/nginx/sites-available/minipass /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

Now you can access your app at `http://yourdomain.com`

**Step 5: Add HTTPS (free SSL certificate)**
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

Now you can access at `https://yourdomain.com` (secure!)

---

### Monitoring Your App

**Check disk space:**
```bash
df -h
```

**Check memory usage:**
```bash
free -m
```

**Check Docker container stats:**
```bash
docker stats
```

**Check if your app is responding:**
```bash
curl -I http://localhost:8889
```

Should return: `HTTP/1.1 200 OK`

---

### Backing Up Your Data

Your important data is in:
- `instance/minipass.db` - Database
- `static/uploads/` - User uploads
- `.env` - Your API keys

**Backup script:**
```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

cd ~/app
tar -czf $BACKUP_DIR/minipass_backup_$DATE.tar.gz \
    instance/minipass.db \
    static/uploads/ \
    .env

echo "Backup created: $BACKUP_DIR/minipass_backup_$DATE.tar.gz"
```

Save as `backup.sh`, make executable, and run daily with cron.

---

### Setting Up Automated Backups

```bash
# Edit crontab
crontab -e

# Add this line (runs backup every day at 2 AM)
0 2 * * * /root/app/backup.sh
```

---

## Quick Reference

### Common Commands

```bash
# Deploy/Update
cd ~/app && git pull && ./deploy.sh

# View logs
docker-compose logs -f minipass-app

# Restart
docker-compose restart

# Stop
docker-compose down

# Start
docker-compose up -d

# Check status
docker-compose ps

# View all containers
docker ps -a

# Clean up old images/containers
docker system prune -a
```

---

## Getting Help

**Check logs first:**
```bash
docker-compose logs -f minipass-app
```

**Common log messages and what they mean:**
- `Address already in use` → Port 8889 is taken, change port or stop other container
- `No such file or directory: .env` → Copy your .env file to the server
- `Connection refused` → App isn't running, check `docker-compose ps`
- `Out of memory` → Your server needs more RAM

---

## Security Best Practices

1. **Never commit .env to git** ✓ Already in .gitignore
2. **Use strong passwords** for your server
3. **Enable firewall:**
   ```bash
   ufw allow ssh
   ufw allow 8889
   ufw enable
   ```
4. **Keep system updated:**
   ```bash
   apt update && apt upgrade -y
   ```
5. **Change default SSH port** (optional but recommended)
6. **Disable root login** after creating a regular user

---

## Summary

**First time setup:**
1. Get a VPS with Ubuntu
2. SSH into it
3. Install Docker and Docker Compose
4. Clone your code
5. Copy your .env file
6. Run `./deploy.sh`

**Regular updates:**
1. SSH into server
2. `cd ~/app`
3. `git pull`
4. `./deploy.sh`

**That's it!** You now know how to deploy Minipass like a pro. 🚀
