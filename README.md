# Smart Approval AI

AI-Based Document Analysis, Performance Indicators & Reporting System for UGC & AICTE Reviewers

## Overview

Smart Approval AI is a reviewer-facing AI tool that automatically analyzes institutional documents submitted for UGC/AICTE approvals and produces:

- Performance scores on official KPI metrics
- Document sufficiency percentage
- Risk/compliance flags
- Evidence-backed structured data
- Past-performance trends
- Official downloadable PDF report

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI
- **Database**: MongoDB
- **AI**: OpenAI GPT-5 Nano (GPT-5 Mini fallback)
- **Document Processing**: Unstructured-IO
- **Report Generation**: WeasyPrint (HTML → PDF)

### Frontend (Next.js)
- **Framework**: Next.js 14
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **File Upload**: React Dropzone

## Project Structure

```
.
├── backend/
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── models/           # Data models
│   ├── schemas/          # Pydantic schemas
│   ├── pipelines/        # Processing pipeline
│   ├── ai/               # AI client
│   ├── config/           # Configuration
│   └── utils/            # Utilities
├── frontend/
│   ├── pages/            # Next.js pages
│   ├── components/       # React components
│   ├── services/         # API services
│   └── styles/           # CSS styles
└── docker-compose.yml    # Docker setup
```

## Features

### Core Modules

1. **Dual Reviewer Mode** - UGC / AICTE mode selection
2. **Document Upload** - Drag & drop, multiple formats
3. **Document Preprocessing** - OCR, segmentation via Unstructured-IO
4. **AI Classification** - Document type detection
5. **AI Extraction** - Structured data extraction
6. **Document Quality** - Duplicate, outdated, quality checks
7. **Sufficiency Scoring** - Document completeness calculation
8. **KPI Scoring** - Mode-specific performance indicators
9. **Trend Analysis** - Historical performance tracking
10. **Compliance Engine** - Rule-based compliance checks
11. **Evidence System** - Source tracking for all extractions
12. **PDF Report Generation** - Official government-style reports
13. **Chatbot Assistant** - GPT-powered reviewer assistant

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (or use Docker)
- OpenAI API key

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd sih-2
```

2. **Backend Setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**

```bash
cd frontend
npm install
```

4. **Environment Configuration**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
- Set `MONGODB_URL`
- Set `OPENAI_API_KEY`
- Configure other settings as needed

5. **Start MongoDB**

```bash
# Using Docker
docker run -d -p 27017:27017 mongo:7.0

# Or use local MongoDB installation
```

6. **Run Backend**

```bash
cd backend
uvicorn main:app --reload
```

7. **Run Frontend**

```bash
cd frontend
npm run dev
```

### Docker Setup

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Usage

1. **Select Mode**: Choose UGC or AICTE reviewer mode
2. **Upload Documents**: Drag & drop institutional documents
3. **Start Processing**: Begin AI analysis pipeline
4. **View Dashboard**: See KPIs, sufficiency, compliance flags
5. **Download Report**: Generate and download PDF report
6. **Chat Assistant**: Ask questions about the analysis

## API Endpoints

### Batches
- `POST /api/batches/` - Create batch
- `GET /api/batches/` - List batches
- `GET /api/batches/{batch_id}` - Get batch
- `DELETE /api/batches/{batch_id}` - Delete batch

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/batch/{batch_id}` - List documents
- `GET /api/documents/{document_id}` - Get document
- `DELETE /api/documents/{document_id}` - Delete document

### Processing
- `POST /api/processing/start` - Start processing
- `GET /api/processing/status/{batch_id}` - Get status

### Dashboard
- `GET /api/dashboard/{batch_id}` - Get dashboard data

### Reports
- `POST /api/reports/generate` - Generate report
- `GET /api/reports/download/{batch_id}` - Download report

### Chatbot
- `POST /api/chatbot/chat` - Chat with assistant

### Search
- `GET /api/search/{batch_id}` - Search batch

### Audit
- `POST /api/audit/` - Create audit log
- `GET /api/audit/batch/{batch_id}` - Get audit logs

## KPI Formulas

### UGC Mode
- **Research Index**: Based on publications and citations
- **Governance Score**: Committee count and compliance
- **Student Outcome Index**: Placement and graduation rates

### AICTE Mode
- **FSR Score**: Faculty-Student Ratio
- **Infrastructure Score**: Built-up area, labs, classrooms
- **Placement Index**: Placement rate and average salary
- **Lab Compliance Index**: Lab count and equipment

## Sufficiency Formula

```
base_pct = (P/R) * 100
penalty = D*2 + O*4 + L*5 + I*7
penalty = min(penalty, 50)
sufficiency = max(0, base_pct - penalty)
```

Where:
- P = Present documents
- R = Required documents
- D = Duplicate count
- O = Outdated count
- L = Low quality count
- I = Invalid count

## Development

### Backend Development

```bash
cd backend
# Install dev dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
# Install dependencies
npm install

# Run dev server
npm run dev
```

## Testing

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

## Deployment

### Production Considerations

1. Set up proper MongoDB replica set
2. Configure environment variables securely
3. Use production-grade OpenAI API keys
4. Set up proper file storage (S3, etc.)
5. Configure CORS properly
6. Set up monitoring and logging
7. Use reverse proxy (Nginx)
8. Enable HTTPS

## License

[Your License Here]

## Support

For issues and questions, please contact [Your Contact Info]

