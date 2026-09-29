
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# =========================================================
# UPLOAD RESPONSE
# =========================================================

class AppUploadResponse(BaseModel):

    message: str

    app_name: str

    package_name: str | None = None

    version: str

    file_type: str

    size_mb: float

    stored_as: str

    icon_path: str | None = None

    icon_url: str | None = None

    changelog: str | None = None

    status: str = "published"


# =========================================================
# APP DETAILS
# =========================================================

class AppDetailsResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    app_name: str

    package_name: str | None = None

    version: str

    file_type: str

    size_mb: float | None = None

    stored_as: str

    developer_id: int | None = None

    description: str

    category: str

    icon_path: str | None = None

    icon_url: str | None = None

    status: str = "published"

    changelog: str = ""

    download_count: int = 0

    view_count: int = 0

    rating: float = 0.0

    review_count: int = 0

    created_at: datetime | None = None

    updated_at: datetime | None = None

