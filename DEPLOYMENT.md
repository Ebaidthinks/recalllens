# RecallLens Deployment Guide

Deploy RecallLens to the web with a public URL that you can share.

## Architecture

**Frontend:** Vercel (React/Vite static site)
**Backend:** Render (Docker container with ML models)

**Total Cost:** $0/month (free tiers) or $7/month (recommended for production)

---

## Option 1: Free Deployment (with limitations)

### ⚠️ Free Tier Limitations
- Backend spins down after 15 minutes of inactivity
- First request after idle takes ~30-40 seconds to wake up
- Limited to 750 hours/month compute time
- Good for demos and testing

### Steps

#### **1. Deploy Backend to Render (Free)**

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **Go to [Render.com](https://render.com)**
   - Sign up with GitHub
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `Ebaidthinks/recalllens`

3. **Configure the service:**
   - **Name:** `recalllens-api`
   - **Region:** Oregon (US West)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Plan:** Free

4. **Environment Variables** (Optional):
   - No environment variables needed for basic setup

5. **Create Web Service**
   - Wait 5-10 minutes for initial build
   - You'll get a URL like: `https://recalllens-api.onrender.com`

6. **Test the backend:**
   ```bash
   curl https://recalllens-api.onrender.com/health
   ```

#### **2. Deploy Frontend to Vercel (Free)**

1. **Create production environment file:**
   ```bash
   cd frontend
   cp .env.example .env.production
   ```

2. **Edit `.env.production`:**
   ```
   VITE_API_URL=https://recalllens-api.onrender.com
   ```
   (Replace with your actual Render URL from step 1)

3. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

4. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

   Follow prompts:
   - Link to existing project? **N**
   - Project name? **recalllens** (or choose your own)
   - Directory? **./** (press Enter)
   - Build command? **npm run build**
   - Output directory? **dist**
   - Deploy? **Y**

5. **Set production environment variable:**
   ```bash
   vercel env add VITE_API_URL production
   ```
   Enter your Render URL: `https://recalllens-api.onrender.com`

6. **Deploy to production:**
   ```bash
   vercel --prod
   ```

7. **You'll get a URL like:** `https://recalllens.vercel.app`

---

## Option 2: Production Deployment ($7/month)

For reliable performance without cold starts:

### Backend: Render Starter Plan

1. Follow same steps as Option 1, but choose **"Starter"** plan ($7/month)
2. Benefits:
   - No cold starts
   - Always running
   - Better performance
   - 512MB RAM (vs 512MB Free)

### Frontend: Vercel (Still Free!)

Same as Option 1 - Vercel is free for personal projects.

**Total Cost:** $7/month for reliable backend + $0 for frontend

---

## Alternative: All-in-One Deploy Button

### Quick Deploy to Render

Click this button to deploy both services automatically:

1. Fork the repo to your GitHub account
2. Click the "Deploy to Render" button in README
3. Render will create both services and connect them

**Note:** You'll still need to deploy frontend separately to Vercel.

---

## Configuration

### Environment Variables

#### Frontend (.env.production)
```bash
VITE_API_URL=https://your-backend-url.onrender.com
```

#### Backend (Optional)
- `PORT=8000` (auto-set by Render)
- No other env vars needed for basic operation

---

## Post-Deployment

### 1. Test the Full Stack

```bash
# Test backend health
curl https://recalllens-api.onrender.com/health

# Test Dubai presets endpoint
curl https://recalllens-api.onrender.com/dubai-presets

# Test frontend
open https://recalllens.vercel.app
```

### 2. Upload a Test Image

- Go to your Vercel URL
- Upload a billboard image
- Configure parameters
- Click "Analyze Billboard"
- Download the PDF report

### 3. Share Your URL

Your live RecallLens app is now at:
```
https://recalllens.vercel.app
```

Share it with clients, colleagues, or on social media!

---

## Troubleshooting

### Backend Issues

**Problem:** "Service Unavailable"
**Solution:** Backend is cold starting (free tier). Wait 30 seconds and retry.

**Problem:** Build fails with "Out of memory"
**Solution:** Upgrade to Starter plan ($7/month) for more RAM.

**Problem:** `/health` returns unhealthy
**Solution:** Check Render logs for missing dependencies.

### Frontend Issues

**Problem:** "Network Error" when analyzing
**Solution:** Check that `VITE_API_URL` is set correctly in Vercel dashboard.

**Problem:** CORS errors
**Solution:** Backend already has CORS enabled for all origins. If issues persist, check Render logs.

**Problem:** Images not loading
**Solution:** Check that backend `/files/` route is accessible.

---

## Custom Domain (Optional)

### Add Custom Domain to Vercel

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain (e.g., `recalllens.yourdomain.com`)
3. Follow DNS configuration instructions
4. SSL certificate auto-provisioned

### Add Custom Domain to Render

1. Go to Render Dashboard → Your Service → Settings
2. Add custom domain under "Custom Domains"
3. Update your DNS records
4. Update frontend `.env.production` with new backend URL

---

## Monitoring

### Render Dashboard
- View logs: `https://dashboard.render.com`
- Check uptime and requests
- Monitor cold starts (free tier)

### Vercel Dashboard
- View analytics: `https://vercel.com/dashboard`
- Monitor page views
- Check build logs

---

## Upgrading

### To Scale Up

1. **Backend:** Upgrade Render plan for:
   - No cold starts: Starter ($7/month)
   - More power: Standard ($25/month)
   - High traffic: Pro ($85/month)

2. **Frontend:** Vercel free tier supports:
   - 100GB bandwidth/month
   - Unlimited requests
   - Upgrade to Pro ($20/month) for:
     - Custom domains
     - Analytics
     - Team collaboration

---

## Maintenance

### Update Deployment

**Backend:**
```bash
git push origin main
```
Render auto-deploys on every push to main branch.

**Frontend:**
```bash
cd frontend
vercel --prod
```
Or enable auto-deploy: Connect GitHub repo in Vercel dashboard.

### Rollback

**Render:**
- Go to dashboard → Deployments
- Click "..." → "Redeploy" on previous version

**Vercel:**
- Go to dashboard → Deployments
- Click "..." → "Promote to Production" on previous version

---

## Cost Breakdown

### Free Option (Development/Demo)
- Backend: $0/month (Render Free)
- Frontend: $0/month (Vercel Free)
- **Total: $0/month**
- Limitations: Cold starts, 750hrs/month

### Recommended Production
- Backend: $7/month (Render Starter)
- Frontend: $0/month (Vercel Free)
- **Total: $7/month**
- Benefits: Always-on, no cold starts

### High-Traffic Production
- Backend: $25/month (Render Standard)
- Frontend: $20/month (Vercel Pro)
- **Total: $45/month**
- Benefits: Dedicated resources, analytics, priority support

---

## Security

### Included Protections

- ✅ HTTPS enforced (Render + Vercel)
- ✅ CORS configured
- ✅ Input validation on backend
- ✅ File size limits (8000x8000 max)
- ✅ Request timeouts (60 seconds)

### Recommendations

1. **Add rate limiting** (Render Pro feature)
2. **Add authentication** if needed for production
3. **Monitor usage** to detect abuse
4. **Set up alerts** for errors (both platforms support integrations)

---

## Support

### Need Help?

**Render:**
- Docs: https://render.com/docs
- Community: https://community.render.com

**Vercel:**
- Docs: https://vercel.com/docs
- Support: https://vercel.com/support

**RecallLens:**
- GitHub Issues: https://github.com/Ebaidthinks/recalllens/issues
- Documentation: See project README.md

---

## Summary Checklist

- [ ] Push code to GitHub
- [ ] Deploy backend to Render
- [ ] Get backend URL
- [ ] Set `VITE_API_URL` in frontend
- [ ] Deploy frontend to Vercel
- [ ] Test `/health` endpoint
- [ ] Upload test billboard and analyze
- [ ] Share your public URL!

**Your app is live! 🎉**

Frontend: `https://recalllens.vercel.app`
Backend API: `https://recalllens-api.onrender.com`
