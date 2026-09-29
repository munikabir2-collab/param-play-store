
from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


# =========================================================
# USER SIGNUP
# =========================================================

class UserCreate(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    is_developer: bool = False


# =========================================================
# USER LOGIN
# =========================================================

class UserLogin(BaseModel):

    email: EmailStr

    password: str


# =========================================================
# USER OUTPUT
# =========================================================

class UserOut(BaseModel):

    id: int

    email: EmailStr

    # -----------------------------------------------------
    # ACCOUNT
    # -----------------------------------------------------

    is_developer: bool

    is_admin: bool = False

    # -----------------------------------------------------
    # DEVELOPER PLAN
    # -----------------------------------------------------

    developer_active: bool

    developer_plan: str

    payment_status: str

    activated_at: datetime | None = None

    # -----------------------------------------------------
    # DEVELOPER PROFILE
    # -----------------------------------------------------

    full_name: str | None = None

    developer_type: str = "individual"

    country: str | None = None

    phone: str | None = None

    address: str | None = None

    company_name: str | None = None

    bio: str | None = None

    website: str | None = None

    github: str | None = None

    # -----------------------------------------------------
    # PYDANTIC / SQLALCHEMY
    # -----------------------------------------------------

    class Config:
        from_attributes = True


# =========================================================
# LOGIN TOKEN
# =========================================================

class Token(BaseModel):

    access_token: str

    token_type: str = "bearer"

