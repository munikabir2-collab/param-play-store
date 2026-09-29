# NextStore Backend

Ek transparent, developer-friendly app marketplace backend — FastAPI se bana hua.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env          # phir .env file me apni values daalo

uvicorn app.main:app --reload
```

Swagger docs: `http://127.0.0.1:8000/docs`

## Folder Structure

```
nextstore/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── core/
│   │   ├── config.py        # settings
│   │   └── database.py      # DB session
│   ├── models/               # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── api/                  # route handlers
│   ├── services/              # business logic (empty for now)
│   ├── workers/                # celery background tasks (empty for now)
│   └── storage/uploads/        # uploaded apk/aab files
├── tests/
├── requirements.txt
└── .env.example
```

## Abhi tak bana hua

- [x] Folder structure
- [x] `/auth/signup`
- [x] `/apps/upload` (.apk / .aab)
- [ ] `/auth/login` (JWT)
- [ ] App listing with DB
- [ ] Review system
- [ ] Search
- [ ] Payments
