
from datetime import datetime
from app.schemas.app_schema import AppDetailsResponse
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class DeveloperApplicationCreate(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    developer_type: str = Field(
        default="individual",
        max_length=30,
    )

    country: str = Field(
        min_length=2,
        max_length=100,
    )

    phone: str = Field(
        min_length=7,
        max_length=30,
    )

    address: str = Field(
        min_length=5,
        max_length=500,
    )

    @field_validator(
        "full_name",
        "country",
        "phone",
        "address",
    )
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Field empty nahi ho sakta"
            )

        return value

    @field_validator("developer_type")
    @classmethod
    def validate_developer_type(
        cls,
        value: str,
    ) -> str:

        value = value.strip().lower()

        allowed = {
            "individual",
            "organization",
        }

        if value not in allowed:
            raise ValueError(
                "developer_type individual ya organization hona chahiye"
            )

        return value


class DeveloperProfileOut(BaseModel):

    id: int
    user_id: int
    full_name: str
    developer_type: str
    country: str
    phone: str
    address: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class DeveloperVerificationOut(BaseModel):

    id: int
    developer_id: int
    status: str
    verification_method: str | None = None
    submitted_at: datetime | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None

    class Config:
        from_attributes = True


class DeveloperApplicationOut(BaseModel):

    profile: DeveloperProfileOut
    verification: DeveloperVerificationOut


class DeveloperPendingOut(BaseModel):

    profile: DeveloperProfileOut
    verification: DeveloperVerificationOut


class DeveloperRejectRequest(BaseModel):

    rejection_reason: str = Field(
        min_length=5,
        max_length=500,
    )

    @field_validator("rejection_reason")
    @classmethod
    def clean_rejection_reason(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Rejection reason required hai"
            )

        return value



class DeveloperDashboardOut(BaseModel):

    profile: DeveloperProfileOut | None = None
    verification: DeveloperVerificationOut | None = None

    is_developer: bool
    developer_active: bool
    developer_plan: str
    payment_status: str
    activated_at: datetime | None = None

    total_apps: int
    apps: list[AppDetailsResponse]



