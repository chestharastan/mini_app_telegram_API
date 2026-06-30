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

### 3. Configure Environment

Create a `.env` file:

```bash
BOT_TOKEN=your_telegram_bot_token
FRONTEND_URL=https://your-frontend-url.com
ADMIN_CHAT_ID=your_admin_chat_id
DATABASE_URL=sqlite:///./ecomus.db
```

`DATABASE_URL` is optional. If you do not set it, the API uses `sqlite:///./ecomus.db`.

### 4. Run the Server

```bash
uvicorn index:app --reload
```

The database tables are created automatically on startup, and the initial products/categories are seeded from `app/data/products.py`.

## Create an Order

The frontend sends Telegram-compatible `initData`, the customer phone number,
product IDs, and quantities. Public web checkout may use server-signed web
checkout init data from the Next.js proxy. The backend calculates prices from
the database, saves the order, reduces stock, and sends Telegram/admin messages.
When a Telegram user shares their contact from the Mini App, the webhook stores
that phone number by Telegram user ID so checkout can use it.

```json
{
  "initData": "telegram-web-app-init-data",
  "customerPhone": "+85512345678",
  "items": [
    {
      "product_id": "prod-1",
      "quantity": 1
    }
  ]
}
```

Send it to:

```http
POST /api/orders
```

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
