# GovProject Risk Analytics

Predicts cost overruns and time overruns in government infrastructure projects using machine learning.

## Architecture

| Component | Technology | Port |
|---|---|---|
| Frontend | React 18, Vite, Tailwind CSS | 5173 |
| Backend | Java 21, Spring Boot 3.4, MongoDB | 8080 |
| Model Service | Python 3.12, FastAPI, XGBoost | 8000 |
| Database | MongoDB 7 | 27017 |

## Quick Start (Windows PowerShell)

### Prerequisites
- Java 21+ (`java -version`)
- Node.js 20+ (`node --version`)
- Python 3.12+ (`python --version`)
- MongoDB running on localhost:27017
- Maven (`mvn --version`)

### 1. Start MongoDB
```powershell
# Using Docker:
docker run -d -p 27017:27017 --name govproject-mongo mongo:7

# Or install MongoDB locally
```

### 2. Start Model Service
```powershell
cd model
python -m pip install -r requirements.txt -r api_requirements.txt
python api.py
# Runs on http://localhost:8000
```

### 3. Start Backend
```powershell
cd backend
mvn spring-boot:run
# Runs on http://localhost:8080
# Auto-creates admin user (admin/admin123)
```

### 4. Start Frontend
```powershell
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### 5. Login
Open http://localhost:5173 and login with:
- Username: `admin`
- Password: `admin123`

## Docker Compose

```powershell
docker-compose up --build
# Frontend: http://localhost:5173
# Backend: http://localhost:8080
# Model: http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/auth/login | No | Officer login |
| GET | /api/auth/me | JWT | Current user |
| POST | /api/projects | JWT | Create project |
| GET | /api/projects | JWT | List projects |
| GET | /api/projects/{id} | JWT | Project details |
| POST | /api/predictions | JWT | New prediction |
| GET | /api/predictions | JWT | List predictions |
| GET | /api/predictions/{id} | JWT | Prediction details |
| GET | /api/projects/{id}/predictions | JWT | Project predictions |
| GET | /api/dashboard/summary | JWT | Dashboard stats |
| GET | /api/reports/export | JWT | CSV export |
| POST | /api/admin/users | ADMIN | Create officer |
| GET | /api/admin/users | ADMIN | List officers |

## Environment Variables

See `.env.example` for all configuration options.

| Variable | Default | Description |
|---|---|---|
| MONGODB_URI | mongodb://localhost:27017/govproject_risk_analytics | MongoDB connection |
| JWT_SECRET | (dev default) | JWT signing key |
| MODEL_SERVICE_URL | http://localhost:8000 | Python model service |
| ADMIN_USERNAME | admin | Bootstrap admin username |
| ADMIN_PASSWORD | admin123 | Bootstrap admin password |

## Model

The ML model predicts:
- **Cost Overrun** (₹ Crore) — predicted additional cost
- **Time Overrun** (months) — predicted schedule delay

Inputs: Sector, Original Cost, Physical Progress (%), Time Delay (months)

Risk classification: **SAFE** (green) / **MODERATE** (amber) / **RISKY** (red)

See [docs/MODEL_AUDIT.md](docs/MODEL_AUDIT.md) for detailed model documentation.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Model Audit](docs/MODEL_AUDIT.md)

## Troubleshooting

**MongoDB connection refused:** Ensure MongoDB is running on port 27017.

**Model service errors:** Check that the model artifact exists at `model/models/sih_cost_prediction_model.pkl`. Run `python model/src/train_model.py` to retrain if needed.

**Java version:** Requires Java 21+. Check with `java -version`.

**CORS errors:** Ensure `CORS_ORIGINS` includes your frontend URL.
