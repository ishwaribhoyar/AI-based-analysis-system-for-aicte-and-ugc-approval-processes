# Smart Approval AI - Frontend

AI-Based Document Analysis, Performance Indicators & Reporting System for UGC & AICTE Reviewers

## Features

- ✅ Mode Selection (AICTE / UGC)
- ✅ Multi-PDF Upload with Drag & Drop
- ✅ Real-time Processing Status
- ✅ Complete Dashboard with:
  - KPI Cards (FSR, Infrastructure, Placement, Lab Compliance, Overall Score)
  - Document Sufficiency Percentage
  - Compliance Flags
  - Information Blocks (10 AICTE / 9 UGC)
  - Trend Charts
  - Evidence Viewer
  - AI Chatbot Assistant
- ✅ PDF Report Download

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts (for trend visualization)
- React Hot Toast (notifications)
- Lucide React (icons)
- Axios (API client)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set API base URL (create `.env.local`):
```
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8010/api
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Pages

- `/` - Mode selection (AICTE / UGC)
- `/upload` - PDF upload page
- `/processing` - Real-time processing status
- `/dashboard` - Complete evaluation dashboard

## Backend Connection

The frontend connects to the FastAPI backend running on port 8010 by default.

All API endpoints are defined in `lib/api.ts`:
- Batch management
- Document upload
- Processing status
- Dashboard data
- Chatbot
- Report generation

## Build for Production

```bash
npm run build
npm start
```
