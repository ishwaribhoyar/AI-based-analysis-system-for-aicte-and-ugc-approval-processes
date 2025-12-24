# Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (running locally or via Docker)
- OpenAI API key

## Quick Setup (5 minutes)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Environment Configuration

Create `.env` file in the root directory:

```env
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB_NAME=smart_approval_ai
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Start MongoDB

```bash
# Option 1: Docker
docker run -d -p 27017:27017 mongo:7.0

# Option 2: Local installation
# Make sure MongoDB is running on port 27017
```

### 5. Run Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend will be available at: http://localhost:8000

### 6. Run Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Using Docker (Alternative)

```bash
# Copy .env.example to .env and fill in values
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## First Use

1. Open http://localhost:3000
2. Select **UGC Reviewer** or **AICTE Reviewer**
3. Upload institutional documents (PDF, DOCX, etc.)
4. Click **Start Processing**
5. Wait for processing to complete
6. View dashboard with KPIs, sufficiency, compliance flags
7. Download PDF report

## API Documentation

Once backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Backend won't start
- Check MongoDB is running
- Verify `.env` file has correct values
- Check Python version: `python --version` (should be 3.11+)

### Frontend won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and `package-lock.json`, then `npm install`

### Processing fails
- Check OpenAI API key is valid
- Verify documents are in supported formats
- Check backend logs for errors

### MongoDB connection error
- Verify MongoDB is running: `mongosh` or check Docker container
- Check `MONGODB_URL` in `.env` file

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check API endpoints in Swagger UI
- Review code structure in `backend/` and `frontend/` directories

