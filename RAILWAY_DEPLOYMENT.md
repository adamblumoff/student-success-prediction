# Railway Deployment Guide

## Prerequisites
- Railway account (free at https://railway.app)
- Railway CLI installed and authenticated
- This codebase ready for deployment

## Quick Deployment Steps

### 1. Create Railway Account & Authenticate
```bash
# Visit https://railway.app and create account
# Go to Account Settings → Tokens → Create token

# Set your token (replace with your actual token)
export RAILWAY_TOKEN=replace-with-your-actual-token

# Or authenticate interactively (if possible)
railway login
```

### 2. Deploy Your Application
```bash
# In your project directory
cd /home/adamblumoff/student-success-prediction

# Initialize and deploy
railway init
railway up
```

### 3. Configure Environment Variables
Set these in Railway's dashboard (railway.app → your project → Variables):

**Required Variables:**
```
MVP_API_KEY=replace-with-secure-32-char-api-key
ENVIRONMENT=production
DEVELOPMENT_MODE=false
SQL_DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
```

**Optional GPT Integration:**
```
OPENAI_API_KEY=replace-with-openai-api-key
GPT_MODEL=gpt-4o-mini
GPT_TIMEOUT=30
GPT_CACHE_ENABLED=true
```

### 4. Database Setup (Choose One)

**Option A: Railway PostgreSQL (Recommended)**
1. In Railway dashboard: Add Service → Database → PostgreSQL
2. Railway auto-generates `DATABASE_URL` environment variable
3. No additional configuration needed

**Option B: External PostgreSQL (Neon.tech)**
1. Create database at https://neon.tech
2. Copy connection string
3. Set in Railway: `DATABASE_URL=postgresql://user:pass@host/db`

### 5. Access Your Application
```bash
# Get your app URL
railway open

# Or check deployment status
railway status
```

## Deployment Files Created

- `railway.json` - Railway configuration
- `Procfile` - Process definition  
- `.railwayignore` - Files to exclude from deployment
- `.env.railway` - Environment template
- This deployment guide

## Application Structure for Railway

Your app is configured to:
- ✅ Start with `python3 run_mvp.py`
- ✅ Auto-detect PORT from Railway
- ✅ Load ML models from `results/models/`
- ✅ Serve web interface at root URL
- ✅ Provide API at `/api/` endpoints
- ✅ Handle file uploads up to 10MB
- ✅ Support both SQLite fallback and PostgreSQL

## Troubleshooting

### Build Issues
```bash
# Check build logs
railway logs

# Redeploy if needed
railway up --detach
```

### Environment Issues
- Verify all required environment variables are set
- Check that `MVP_API_KEY` is at least 32 characters
- Ensure `DEVELOPMENT_MODE=false` in production

### Database Issues
- Railway PostgreSQL: Connection string is auto-generated
- External DB: Verify connection string format
- Check database is accessible from Railway's network

### Application Issues
```bash
# View real-time logs
railway logs --tail

# Check service status
railway status
```

## URLs After Deployment
- **Web Interface**: https://your-app.railway.app
- **API Documentation**: https://your-app.railway.app/docs  
- **Health Check**: https://your-app.railway.app/health

## Cost Estimation
- **Hobby Plan**: $0-5/month (500 hours free)
- **Pro Plan**: $20/month (unlimited hours)
- PostgreSQL: Free tier available with Railway

## Next Steps After Deployment
1. Test file upload with sample CSV
2. Verify ML predictions work
3. Test GPT insights (if enabled)
4. Set up custom domain (optional)
5. Monitor application logs
6. Configure alerts for errors

## Support
- Railway Docs: https://docs.railway.com
- Railway Discord: https://discord.gg/railway
- Application logs via `railway logs`