# Quick Start Guide - Smart Approval AI

## ✅ System Status

**Backend:** ✅ Running on `http://127.0.0.1:8010`  
**Frontend:** Ready to start

---

## 🚀 Start the System

### Step 1: Backend (Already Running)
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```
✅ **Status:** Backend is already running!

### Step 2: Frontend
Open a **NEW terminal window** and run:
```bash
cd frontend
npm run dev
```

### Step 3: Open Browser
Navigate to: **http://localhost:3000**

---

## 📋 Complete User Flow

1. **Home Page** → Select AICTE or UGC mode
2. **Upload Page** → Drag & drop PDF files
3. **Processing Page** → Watch real-time progress
4. **Dashboard** → View complete evaluation:
   - ✅ KPI Cards (FSR, Infrastructure, Placement, Lab Compliance, Overall)
   - ✅ Sufficiency Percentage
   - ✅ Compliance Flags
   - ✅ All Information Blocks (10 AICTE / 9 UGC)
   - ✅ Trend Charts
   - ✅ Evidence Viewer (click any block)
   - ✅ AI Chatbot (bottom-right button)
   - ✅ Download Report (PDF)

---

## 🎯 Features Available

### Dashboard Features:
- **KPI Cards** - All 5 performance indicators
- **Sufficiency Card** - Document completeness (92%+)
- **Compliance Flags** - Missing/expired certificates
- **Information Blocks** - All extracted data blocks
- **Trend Charts** - Multi-year performance visualization
- **Evidence Modal** - Click blocks to see source evidence
- **AI Chatbot** - Ask questions about KPIs, sufficiency, compliance
- **Report Download** - Generate and download PDF report

---

## 🔧 Troubleshooting

### Backend Not Responding?
- Check if port 8010 is in use: `netstat -ano | findstr :8010`
- Restart backend: `python -m uvicorn main:app --host 127.0.0.1 --port 8010`

### Frontend Not Connecting?
- Check `.env.local` in frontend folder has: `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8010/api`
- Make sure backend is running first

### Port Conflicts?
- Backend: Change port in uvicorn command
- Frontend: Change port with `npm run dev -- -p 3001`

---

## ✅ System Ready!

**Backend:** ✅ Running  
**Frontend:** Ready (run `npm run dev`)  
**Integration:** ✅ Connected  
**Features:** ✅ All Implemented  

**Your system is ready for showcase!** 🚀

