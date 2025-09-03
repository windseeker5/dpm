# 🚀 VPS Deployment Guide - Minipass v1

## 🔧 VPS Deployment Steps

### 1. **Connect to VPS**
```bash
ssh -P kdresdell@minipass.me
# or however you usually connect
```

### 2. **Navigate to Project Directory**
```bash
cd minipass_env/app
# (wherever your Docker setup lives)
```


### 3. **Fetch Latest Code**


git fetch origin
git reset --hard origin/v1



### 4. **Stop Running Containers**
```bash
docker-compose down lhgi
```


### 5. **Rebuild Docker Image**
```bash
# Rebuild with no cache to ensure clean build
docker-compose build --no-cache lhgi
```

### 6. **Start Containers**
```bash
docker-compose up -d lhgi
```

### 7. **Verify Deployment**
```bash
# Check container status
docker ps

# Check logs for errors
docker-compose logs -f lhgi
```

### 8. **Test Performance**
```bash
# Quick test from VPS
curl -I https://lhgi.minipass.me

# Check response time
time curl -s https://lhgi.minipass.me > /dev/null
```
