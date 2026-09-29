
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.user_model import User

from app.models.developer_model import (
    DeveloperProfile,
    DeveloperVerification,
)

from app.models.app_model import App

from app.schemas.developer_schema import (
    DeveloperApplicationCreate,
    DeveloperApplicationOut,
    DeveloperDashboardOut,
    DeveloperProfileOut,
    DeveloperVerificationOut,
    DeveloperPendingOut,
    DeveloperRejectRequest,
)

from app.api.auth import get_current_user


router = APIRouter(
    prefix="/developers",
    tags=["Developers"],
)


# =========================================================
# COMMON ADMIN SECURITY
# =========================================================

def require_admin(
    current_user: User,
) -> User:

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sirf admin is action ko perform kar sakta hai",
        )

    return current_user


# =========================================================
# DEVELOPER STATE HELPERS
# =========================================================

def is_payment_paid(
    user: User,
) -> bool:
    """
    Developer registration payment successfully paid hai
    ya nahi.

    IMPORTANT:
    Payment state aur verification state alag rakhi jaati hai.
    """

    return (
        user.payment_status or ""
    ).strip().lower() == "paid"


def update_developer_activation_state(
    user: User,
    verification_status: str | None,
    now: datetime | None = None,
) -> None:
    """
    Developer activation ka single source of truth.

    Active developer tabhi hoga jab:

        payment_status == paid
        AND
        verification_status == approved
    """

    normalized_verification = (
        verification_status or ""
    ).strip().lower()

    payment_paid = is_payment_paid(user)

    if normalized_verification == "approved" and payment_paid:

        user.is_developer = True
        user.developer_active = True
        user.developer_plan = "verified"

        if user.activated_at is None:
            if now is None:
                now = datetime.now(timezone.utc)

            user.activated_at = (
                now.replace(tzinfo=None)
            )

        return

    # -----------------------------------------------------
    # Not fully activated
    # -----------------------------------------------------

    user.developer_active = False

    user.activated_at = None

    # Verification approved but payment pending:
    # user is verified, but developer account is not active.
    if normalized_verification == "approved":

        user.is_developer = True
        user.developer_plan = "verified"

        return

    # Verification pending/rejected
    user.is_developer = False
    user.developer_plan = "free"


# =========================================================
# DEVELOPER PROFILE UPDATE SCHEMA
# =========================================================

class DeveloperProfileUpdate(BaseModel):

    full_name: str | None = Field(
        default=None,
        max_length=150,
    )

    developer_type: str = Field(
        default="individual",
        max_length=30,
    )

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    address: str | None = Field(
        default=None,
        max_length=2000,
    )

    company_name: str | None = Field(
        default=None,
        max_length=150,
    )

    bio: str | None = Field(
        default=None,
        max_length=5000,
    )

    website: str | None = Field(
        default=None,
        max_length=500,
    )

    github: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator(
        "full_name",
        "country",
        "phone",
        "address",
        "company_name",
        "bio",
        "website",
        "github",
    )
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value or None

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


# =========================================================
# DEVELOPER ACCOUNT RESPONSE
# =========================================================

def serialize_developer_account(
    user: User,
) -> dict:

    return {
        "id": user.id,
        "email": user.email,

        "is_developer": user.is_developer,
        "is_admin": user.is_admin,

        "developer_active": user.developer_active,
        "developer_plan": user.developer_plan,
        "payment_status": user.payment_status,

        "activated_at": (
            user.activated_at.isoformat()
            if user.activated_at
            else None
        ),

        "full_name": user.full_name,
        "developer_type": user.developer_type,
        "country": user.country,
        "phone": user.phone,
        "address": user.address,
        "company_name": user.company_name,
        "bio": user.bio,
        "website": user.website,
        "github": user.github,
    }


# =========================================================
# DEVELOPER APPLICATION
# =========================================================

@router.post(
    "/apply",
    response_model=DeveloperApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def apply_as_developer(
    data: DeveloperApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    # -----------------------------------------------------
    # Already active developer
    # -----------------------------------------------------

    if (
        current_user.is_developer
        and current_user.developer_active
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already active developer hai",
        )

    # -----------------------------------------------------
    # Existing application check
    # -----------------------------------------------------

    existing = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == current_user.id
        )
        .first()
    )

    if existing is not None:

        verification = (
            db.query(DeveloperVerification)
            .filter(
                DeveloperVerification.developer_id
                == existing.id
            )
            .first()
        )

        if verification is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Verification record missing hai",
            )

        # -------------------------------------------------
        # Re-application after rejection
        # -------------------------------------------------

        if verification.status == "rejected":

            try:

                existing.full_name = data.full_name
                existing.developer_type = data.developer_type
                existing.country = data.country
                existing.phone = data.phone
                existing.address = data.address

                verification.status = "pending"
                verification.verification_method = None
                verification.verification_reference = None
                verification.rejection_reason = None
                verification.submitted_at = datetime.now(
                    timezone.utc
                )
                verification.verified_at = None
                verification.reviewed_by = None

                current_user.full_name = data.full_name
                current_user.developer_type = data.developer_type
                current_user.country = data.country
                current_user.phone = data.phone
                current_user.address = data.address

                current_user.is_developer = False
                current_user.developer_active = False
                current_user.developer_plan = "free"

                # IMPORTANT:
                # Existing paid payment ko erase nahi karna.
                # Agar payment paid hai to paid hi rahega.
                if not is_payment_paid(current_user):
                    current_user.payment_status = "unpaid"

                current_user.activated_at = None

                db.commit()

                db.refresh(existing)
                db.refresh(verification)

            except Exception:

                db.rollback()

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Rejected developer application "
                        "dobara submit nahi ho payi"
                    ),
                )

            return DeveloperApplicationOut(
                profile=DeveloperProfileOut.model_validate(
                    existing
                ),
                verification=DeveloperVerificationOut.model_validate(
                    verification
                ),
            )

        # -------------------------------------------------
        # Existing pending/approved application
        # -------------------------------------------------

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Developer application already exist karti hai. "
                "Existing application ka status check karein."
            ),
        )

    # -----------------------------------------------------
    # New developer application
    # -----------------------------------------------------

    profile = DeveloperProfile(
        user_id=current_user.id,
        full_name=data.full_name,
        developer_type=data.developer_type,
        country=data.country,
        phone=data.phone,
        address=data.address,
    )

    db.add(profile)

    try:

        db.flush()

        # -------------------------------------------------
        # Sync basic profile information
        # -------------------------------------------------

        current_user.full_name = data.full_name
        current_user.developer_type = data.developer_type
        current_user.country = data.country
        current_user.phone = data.phone
        current_user.address = data.address

        # -------------------------------------------------
        # Application is not active yet
        # -------------------------------------------------

        current_user.is_developer = False
        current_user.developer_active = False
        current_user.developer_plan = "free"

        # -------------------------------------------------
        # Payment has not been completed yet
        # -------------------------------------------------

        current_user.payment_status = "unpaid"

        current_user.activated_at = None

        # -------------------------------------------------
        # Verification record
        # -------------------------------------------------

        verification = DeveloperVerification(
            developer_id=profile.id,
            status="pending",
            verification_method=None,
            verification_reference=None,
            rejection_reason=None,
            reviewed_by=None,
        )

        db.add(verification)

        db.commit()

        db.refresh(profile)
        db.refresh(verification)

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Developer application "
                "already exist karti hai"
            ),
        )

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Developer application save "
                "nahi ho payi"
            ),
        )

    return DeveloperApplicationOut(
        profile=DeveloperProfileOut.model_validate(
            profile
        ),
        verification=DeveloperVerificationOut.model_validate(
            verification
        ),
    )


# =========================================================
# CURRENT USER'S DEVELOPER APPLICATION
# =========================================================

@router.get(
    "/me",
    response_model=DeveloperApplicationOut,
)
def get_my_developer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == current_user.id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer application nahi mili",
        )

    verification = (
        db.query(DeveloperVerification)
        .filter(
            DeveloperVerification.developer_id
            == profile.id
        )
        .first()
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification record missing hai",
        )

    return DeveloperApplicationOut(
        profile=DeveloperProfileOut.model_validate(
            profile
        ),
        verification=DeveloperVerificationOut.model_validate(
            verification
        ),
    )


# =========================================================
# CURRENT USER ACCOUNT + DASHBOARD PROFILE
# =========================================================

@router.get(
    "/me/account",
)
def get_my_developer_account(
    current_user: User = Depends(get_current_user),
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    return serialize_developer_account(
        current_user
    )


# =========================================================
# UPDATE CURRENT USER ACCOUNT PROFILE
# =========================================================

@router.put(
    "/me/account",
)
def update_my_developer_account(
    data: DeveloperProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    # -----------------------------------------------------
    # Update users table
    # -----------------------------------------------------

    if data.full_name is not None:
        current_user.full_name = data.full_name

    current_user.developer_type = data.developer_type

    if data.country is not None:
        current_user.country = data.country

    if data.phone is not None:
        current_user.phone = data.phone

    if data.address is not None:
        current_user.address = data.address

    if data.company_name is not None:
        current_user.company_name = data.company_name

    if data.bio is not None:
        current_user.bio = data.bio

    if data.website is not None:
        current_user.website = data.website

    if data.github is not None:
        current_user.github = data.github

    # -----------------------------------------------------
    # Keep developer application synchronized
    # -----------------------------------------------------

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == current_user.id
        )
        .first()
    )

    if profile is not None:

        if data.full_name is not None:
            profile.full_name = data.full_name

        profile.developer_type = data.developer_type

        if data.country is not None:
            profile.country = data.country

        if data.phone is not None:
            profile.phone = data.phone

        if data.address is not None:
            profile.address = data.address

    try:

        db.commit()

        db.refresh(current_user)

        if profile is not None:
            db.refresh(profile)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Developer profile save nahi ho paya",
        )

    return serialize_developer_account(
        current_user
    )


# =========================================================
# CURRENT USER VERIFICATION STATUS
# =========================================================

@router.get(
    "/verification-status",
    response_model=DeveloperVerificationOut,
)
def verification_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == current_user.id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer application nahi mili",
        )

    verification = (
        db.query(DeveloperVerification)
        .filter(
            DeveloperVerification.developer_id
            == profile.id
        )
        .first()
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification record nahi mila",
        )

    return verification


# =========================================================
# ADMIN ENDPOINTS
# =========================================================

# ---------------------------------------------------------
# Admin: pending developer applications
# ---------------------------------------------------------

@router.get(
    "/admin/pending",
    response_model=list[DeveloperPendingOut],
)
def get_pending_developers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    require_admin(current_user)

    rows = (
        db.query(
            DeveloperProfile,
            DeveloperVerification,
        )
        .join(
            DeveloperVerification,
            DeveloperVerification.developer_id
            == DeveloperProfile.id,
        )
        .filter(
            DeveloperVerification.status == "pending"
        )
        .order_by(
            DeveloperVerification.submitted_at.asc()
        )
        .all()
    )

    return [
        DeveloperPendingOut(
            profile=DeveloperProfileOut.model_validate(
                profile
            ),
            verification=DeveloperVerificationOut.model_validate(
                verification
            ),
        )
        for profile, verification in rows
    ]


# ---------------------------------------------------------
# Admin: approve developer
# ---------------------------------------------------------

@router.post(
    "/admin/{developer_id}/approve",
    response_model=DeveloperVerificationOut,
)
def approve_developer(
    developer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    admin = require_admin(current_user)

    verification = (
        db.query(DeveloperVerification)
        .filter(
            DeveloperVerification.developer_id
            == developer_id
        )
        .first()
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer verification nahi mili",
        )

    if verification.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Developer verification already "
                f"'{verification.status}' state mein hai"
            ),
        )

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.id == developer_id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer profile nahi mili",
        )

    user = (
        db.query(User)
        .filter(
            User.id == profile.user_id
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer user nahi mila",
        )

    now = datetime.now(timezone.utc)

    try:

        # -------------------------------------------------
        # Verification state
        # -------------------------------------------------

        verification.status = "approved"

        verification.verified_at = now

        verification.reviewed_by = admin.id

        verification.rejection_reason = None

        # -------------------------------------------------
        # IMPORTANT
        #
        # Payment status ko admin approval se change
        # nahi karna hai.
        #
        # paid → paid
        # pending → pending
        # unpaid → unpaid
        # -------------------------------------------------

        update_developer_activation_state(
            user=user,
            verification_status=verification.status,
            now=now,
        )

        db.commit()

        db.refresh(verification)
        db.refresh(user)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Developer approval save nahi ho paya",
        )

    return verification


# ---------------------------------------------------------
# Admin: reject developer
# ---------------------------------------------------------

@router.post(
    "/admin/{developer_id}/reject",
    response_model=DeveloperVerificationOut,
)
def reject_developer(
    developer_id: int,
    data: DeveloperRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    admin = require_admin(current_user)

    verification = (
        db.query(DeveloperVerification)
        .filter(
            DeveloperVerification.developer_id
            == developer_id
        )
        .first()
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer verification nahi mili",
        )

    if verification.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Developer verification already "
                f"'{verification.status}' state mein hai"
            ),
        )

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.id == developer_id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer profile nahi mili",
        )

    user = (
        db.query(User)
        .filter(
            User.id == profile.user_id
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer user nahi mila",
        )

    try:

        # -------------------------------------------------
        # Verification state
        # -------------------------------------------------

        verification.status = "rejected"

        verification.rejection_reason = (
            data.rejection_reason
        )

        verification.reviewed_by = admin.id

        verification.verified_at = None

        # -------------------------------------------------
        # Developer privileges
        # -------------------------------------------------

        user.is_developer = False
        user.developer_active = False
        user.developer_plan = "free"
        user.activated_at = None

        # -------------------------------------------------
        # IMPORTANT:
        #
        # Rejection payment ko cancel nahi karta.
        #
        # Agar payment paid hai:
        #     payment_status = paid
        #
        # Agar payment paid nahi hai:
        #     payment status unchanged rahega.
        # -------------------------------------------------

        db.commit()

        db.refresh(verification)
        db.refresh(user)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Developer rejection save nahi ho paya",
        )

    return verification


# =========================================================
# DEVELOPER DASHBOARD
# =========================================================

@router.get(
    "/dashboard",
    response_model=DeveloperDashboardOut,
)
def developer_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required hai",
        )

    # -----------------------------------------------------
    # Developer profile
    # -----------------------------------------------------

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == current_user.id
        )
        .first()
    )

    # -----------------------------------------------------
    # Verification
    # -----------------------------------------------------

    verification = None

    if profile is not None:

        verification = (
            db.query(DeveloperVerification)
            .filter(
                DeveloperVerification.developer_id
                == profile.id
            )
            .first()
        )

    # -----------------------------------------------------
    # Developer apps
    # -----------------------------------------------------

    app_rows = (
        db.query(App)
        .filter(
            App.developer_id
            == current_user.id
        )
        .order_by(
            App.created_at.desc()
        )
        .all()
    )

    apps = app_rows

    return {
        "profile": profile,
        "verification": verification,

        "is_developer": current_user.is_developer,

        "developer_active": (
            current_user.developer_active
        ),

        "developer_plan": (
            current_user.developer_plan
        ),

        "payment_status": (
            current_user.payment_status
        ),

        "activated_at": (
            current_user.activated_at
        ),

        "total_apps": len(apps),

        "apps": apps,
    }

