# Version Validation Guide

## Quick Usage

### 1. Local Testing
Test the health check endpoint locally:
```bash
curl http://localhost:5000/health
```

### 2. Before Deployment
Check your current version:
```bash
git rev-parse HEAD | cut -c1-8
```

### 3. Deploy to VPS
Push to GitHub and run deployment script:
```bash
git push origin v1
# Then on VPS:
./deploy-vps.sh
```

### 4. Verify Deployment
The script will automatically:
- ✅ Check if expected version matches deployed version
- ⚠️ Alert you if versions don't match (cache issue detected)
- 🔄 Automatically rollback if version mismatch occurs

## Manual Verification

### Check deployed version on VPS:
```bash
curl http://YOUR_VPS_IP:5000/health
```

### Example healthy response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-03T15:30:00.000Z",
  "version": "a1b2c3d4",
  "git_commit": "a1b2c3d4",
  "database": "connected"
}
```

## Troubleshooting

**Version Mismatch Detected:**
- The deployment script will automatically rollback
- This indicates Docker cache served old code
- The enhanced cleaning in the script should prevent this

**Health Check Failed:**
- Check container logs: `docker-compose logs web`
- Verify Flask app started correctly
- Check database connection

**Database Error:**
- Status will be "unhealthy" with 503 response
- Check database file exists: `/root/minipass_env/instance/minipass.db`

## Benefits

✅ **Cache Detection**: Immediately know if Docker serves old code  
✅ **Automatic Rollback**: Failed deployments rollback automatically  
✅ **Database Validation**: Confirms database connectivity  
✅ **Version Tracking**: Always know exactly what version is running