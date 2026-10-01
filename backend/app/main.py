
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine

# =======================================================
# DATABASE MODELS
# =======================================================

from app.models.user_model import User
from app.models.app_model import App
from app.models.developer_model import (
    DeveloperProfile,
    DeveloperVerification,
)
from app.models.payment_model import Payment

# =======================================================
# CREATE MISSING DATABASE TABLES
# =======================================================

Base.metadata.create_all(bind=engine)

# =======================================================
# API ROUTERS
# =======================================================

from app.api import payments as payments_router
from app.api import apps as apps_router
from app.api import auth as auth_router
from app.api import developers as developers_router

# =======================================================
# FASTAPI APP
# =======================================================

app = FastAPI(
    title="PARAM Play Store Backend",
    description="A transparent, developer-friendly app marketplace backend",
    version="0.1.0",
)

# =======================================================
# CORS
# =======================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================================================
# API ROUTES
# =======================================================

app.include_router(auth_router.router)
app.include_router(apps_router.router)
app.include_router(developers_router.router)
app.include_router(payments_router.router)

# =======================================================
# ROOT
# =======================================================

@app.get("/")
def root():
    return {
        "message": "PARAM PLAY STORE backend chal raha hai"
    }

