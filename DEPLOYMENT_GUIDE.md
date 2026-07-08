# Smart Finance Analyzer - Production Deployment Guide

## ✅ Pre-Deployment Security Check - PASSED

- ✅ No .env files with real keys tracked
- ✅ No .db SQLite database files tracked
- ✅ No __pycache__ folders tracked
- ✅ No node_modules tracked
- ✅ Frontend build successful (4.9 MB bundle)

---

## 🔧 STEP 1 — Backend Push to Hugging Face Spaces

### Prerequisites
1. Create HF Space manually at: https://huggingface.co/new-space
   - Space name: `smart-finance-backend`
   - Username: `Ujju33`
   - SDK: Docker
   - Hardware: CPU basic (free tier)

### Push Backend to HF Space

```bash
cd backend
git push hf-space master:main --force
```

**Credentials when prompted:**
- Username: `Ujju33`
- Password: `<your HF write token>`

### Expected URL
- Backend API: `https://ujju33-smart-finance-backend.hf.space`
- API Docs: `https://ujju33-smart-finance-backend.hf.space/docs`

### Required HF Space Secrets

Go to Space Settings → Variables and Secrets:

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `GROQ_API_KEY` | Your Groq API key | LLM calls for parsing, categorization, insights, chat |

**Get Groq API Key**: https://console.groq.com/keys (free, no credit card)

---

## 🌐 STEP 2 — Frontend Deploy to Vercel

### 1. Go to Vercel
Visit: https://vercel.com/new

### 2. Import Repository
- Click "Import Git Repository"
- Select: `ujju1124/smart-finance-analyzer`
- Click "Import"

### 3. Configure Project Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` ⚠️ **CLICK EDIT** |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

### 4. Add Environment Variable

Click "Environment Variables" → Add:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://ujju33-smart-finance-backend.hf.space` |

Leave "All" selected for environments.

### 5. Deploy
- Click "Deploy"
- Wait 2-3 minutes for build to complete

### Expected URLs
- Main: `https://smart-finance-analyzer-[random].vercel.app`
- Or custom: `https://smart-finance-analyzer.vercel.app`

---

## 📋 Deployment Verification Checklist

### Backend (HF Spaces)
- [ ] Space build succeeded
- [ ] `GROQ_API_KEY` secret added
- [ ] API docs accessible at `/docs`
- [ ] Health check: `GET /api/sample` returns success

### Frontend (Vercel)
- [ ] Build succeeded with no errors
- [ ] `VITE_API_URL` environment variable set
- [ ] Site loads without errors
- [ ] Demo mode works (instant load)
- [ ] Upload mode connects to backend

### Integration Test
1. Open frontend URL
2. Click "Try Demo" → should show charts instantly
3. Click "Upload PDF" → upload test PDF
4. Verify charts update
5. Test chat interface

---

## 🔍 Files Committed to Each Repo

### Main GitHub Repo (`ujju1124/smart-finance-analyzer`)
- ✅ Frontend source code
- ✅ Backend Dockerfile and README
- ✅ Root README.md
- ✅ .env.example files (no secrets)
- ❌ .env files (gitignored)
- ❌ .db files (gitignored)
- ❌ __pycache__ (gitignored)

### HF Space Backend Repo
- ✅ Backend Python code
- ✅ Dockerfile with poppler-utils
- ✅ requirements.txt
- ✅ README.md with HF frontmatter
- ✅ Data files (merchant patterns, sample transactions)
- ❌ Test files (removed)
- ❌ Utility scripts (removed)
- ❌ __pycache__ (gitignored)
- ❌ .db files (gitignored)

---

## 🚀 Tech Stack Summary

### Backend
- **Platform**: Hugging Face Spaces (Docker)
- **Framework**: FastAPI + Uvicorn
- **Port**: 7860 (HF Spaces standard)
- **Dependencies**: pandas, pdfplumber, chromadb, groq, poppler-utils

### Frontend
- **Platform**: Vercel
- **Framework**: React + Vite
- **Build Output**: dist/
- **Bundle Size**: ~4.9 MB (includes Plotly.js)
- **Environment**: Production mode uses HF Spaces backend

---

## 📝 Post-Deployment Tasks

### 1. Update Main README
Add deployment links:
```markdown
## Live Demo

- **Frontend**: https://smart-finance-analyzer.vercel.app
- **Backend API**: https://ujju33-smart-finance-backend.hf.space
- **API Docs**: https://ujju33-smart-finance-backend.hf.space/docs
```

### 2. Test Rate Limits
Groq free tier limits:
- llama-3.3-70b: ~1,000 req/day, 100K tokens/day
- llama-3.1-8b: ~14,400 req/day

If you hit limits, users can provide their own API key via the UI.

### 3. Monitor Usage
- HF Spaces: Check build logs and runtime logs
- Vercel: Check deployment logs and analytics
- Groq: Check API usage at https://console.groq.com

---

## 🛠️ Troubleshooting

### Backend Issues

**Problem**: Space shows "Starting" but never reaches "Running"
- Check runtime logs in HF Space → Logs tab
- Common causes:
  - Missing `python-multipart` in requirements.txt (fixed in latest version)
  - Missing GROQ_API_KEY secret in HF Space settings
  - Import errors or module not found
- Solution: Check logs for specific error, add missing dependencies or secrets

**Problem**: Space build fails
- Check Dockerfile syntax
- Verify requirements.txt dependencies
- Check HF Space build logs

**Problem**: API returns 500 errors
- Check GROQ_API_KEY is set in HF Secrets
- Check HF Space runtime logs
- Test locally: `uvicorn main:app --port 7860`

**Problem**: PDF parsing fails
- Verify poppler-utils installed in Dockerfile
- Check PDF is text-based (not scanned image)

### Frontend Issues

**Problem**: Build fails on Vercel
- Check `VITE_API_URL` is set
- Verify root directory is `frontend/`
- Check build logs for errors

**Problem**: API calls fail
- Verify CORS is enabled on backend
- Check `VITE_API_URL` matches HF Space URL
- Open browser DevTools → Network tab

**Problem**: Demo mode fails
- Check `demo_analysis.json` is included in build
- Verify sessionStorage is available
- Check browser console for errors

---

## 📦 Repository Structure

```
smart-finance-analyzer/
├── backend/                 # Backend code (copied to HF Space)
│   ├── Dockerfile          # HF Space Docker config
│   ├── README.md           # HF Space frontmatter
│   ├── .gitignore          # Ignores __pycache__, .db, .env
│   ├── main.py             # FastAPI app
│   ├── requirements.txt
│   ├── routers/
│   ├── services/
│   ├── models/
│   └── data/
│
├── frontend/               # Frontend code (deployed to Vercel)
│   ├── src/
│   ├── public/
│   ├── .env.example        # Example env file
│   ├── .env.production     # Production API URL (gitignored)
│   ├── .env.development    # Dev API URL (gitignored)
│   ├── .gitignore          # Ignores .env files, dist/, node_modules
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore              # Root gitignore
├── README.md               # Project documentation
└── DEPLOYMENT_GUIDE.md     # This file
```

---

## ✅ Final Verification Results

### Security Check
```
Main repo: 0 sensitive files tracked ✓
Backend repo: 0 sensitive files tracked ✓
```

### Build Status
```
Backend Dockerfile: Created ✓
Backend README with HF frontmatter: Created ✓
Frontend build: SUCCESS (4.9 MB) ✓
```

### Git Commits
```
Main repo: Latest commit includes Dockerfile and env configs ✓
Backend repo: 3 commits, cleaned of test files and cache ✓
```

### Environment Variables
```
Frontend: VITE_API_URL configured ✓
Backend: GROQ_API_KEY required (add in HF Secrets) ⚠️
```

---

## 🎉 Deployment Complete!

Both services are ready to deploy:
1. **Backend**: Push to HF Space (command provided above)
2. **Frontend**: Deploy via Vercel UI (instructions above)

After deployment:
- Frontend will be live at Vercel URL
- Backend will be live at HF Spaces URL
- Users can upload PDFs or try instant demo mode
- No credit card required for free tiers (Vercel, HF, Groq)
