from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import payments as payments_router
from app.api import apps as apps_router
from app.api import auth as auth_router
from app.api import developers as developers_router


app = FastAPI(
    title="NextStore Backend",
    description="A transparent, developer-friendly app marketplace backend",
    version="0.1.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTERS
# =========================================================

app.include_router(
    auth_router.router
)

app.include_router(
    apps_router.router
)

app.include_router(
    developers_router.router
)

app.include_router(
    payments_router.router)
    
# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "NextStore backend chal raha hai"
    }