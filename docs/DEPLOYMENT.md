# MedScribe Deployment Guide

## Single-Command Docker Deployment

```bash
# 1. Configure environment
cp .env.example .env

# 2. Build and start services
docker-compose up --build -d

# 3. Seed demo data
python data/seed.py
```

## Service Access Points
- **API Backend**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **Streamlit Dashboard**: `http://localhost:8501`
