# Telegram Ecomus API

A FastAPI-based REST API for the Telegram Ecomus project.

## Setup Instructions

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - ReDoc documentation

## Project Structure

```
api/
├── main.py              # Main FastAPI application
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## Development

To add new routes, create them in `main.py` or organize them in separate files under a `routers/` directory for larger projects.
