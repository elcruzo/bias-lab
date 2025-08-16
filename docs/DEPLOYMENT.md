# 🚀 Deployment Guide

## Quick Deploy Steps

### 1. Backend (Render)
1. Push code to GitHub
2. Connect GitHub repo to Render
3. Select `bias-lab-pipeline` directory as root
4. Add environment variables:
   - `OPENAI_API_KEY=sk-your-key`
   - `NEWSAPI_KEY=your-key`
   - `ENVIRONMENT=production`
5. Deploy!

### 2. Frontend (Vercel)
1. Connect GitHub repo to Vercel  
2. Select `bias-lab-ui` directory as root
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-render-backend-url.onrender.com`
4. Deploy!

## Local Development

### Backend Setup
```bash
cd bias-lab-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your OPENAI_API_KEY and NEWSAPI_KEY

# Run the server
python api/main.py
```

### Frontend Setup
```bash
cd bias-lab-ui
npm install
npm run dev
```

Visit `http://localhost:3000` to see the application.

## Environment Variables

### Backend (.env in bias-lab-pipeline/)
```env
OPENAI_API_KEY=sk-your-openai-key
NEWSAPI_KEY=your-newsapi-key
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development
```

### Frontend (.env.local in bias-lab-ui/)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Deployment

1. **Backend Health Check**:
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```

2. **Frontend Check**: Visit your Vercel URL

3. **Integration Test**: Try searching for articles

## Troubleshooting

### Common Issues

**Backend not starting?**
- Check environment variables are set
- Verify OpenAI API key is valid
- Check Render logs for errors

**Frontend can't connect to backend?**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings in backend
- Ensure backend is deployed and running

**Slow performance?**
- First load might be slow (cold start)
- Subsequent requests should be <500ms
- Check caching is working

---

**Your deployment should be live in ~10 minutes!** 🎉
