
import os
import uuid
import zipfile

from pathlib import Path

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.core.config import (
    UPLOAD_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS,
)

from app.core.database import get_db

from app.models.app_model import App
from app.models.user_model import User

from app.schemas.app_schema import (
    AppUploadResponse,
    AppDetailsResponse,
)

from app.api.auth import get_current_user

from app.services.aab_converter import (
    convert_aab_to_apk,
    ConversionError,
)


router = APIRouter(
    prefix="/apps",
    tags=["Apps"],
)


# =========================================================
# SECURITY LIMITS
# =========================================================

MAX_UPLOAD_BYTES = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)

UPLOAD_CHUNK_SIZE = (
    1024 * 1024
)

MAX_APP_NAME_LENGTH = 100

MAX_PACKAGE_NAME_LENGTH = 255

MAX_VERSION_LENGTH = 50

MAX_DESCRIPTION_LENGTH = 5000

MAX_CATEGORY_LENGTH = 50

MAX_CHANGELOG_LENGTH = 10000


# =========================================================
# ZIP SECURITY
# =========================================================

MAX_ZIP_ENTRIES = 10000

MAX_ZIP_UNCOMPRESSED_BYTES = (
    1024 * 1024 * 1024
)


# =========================================================
# ICON SECURITY
# =========================================================

MAX_ICON_SIZE_MB = 5

MAX_ICON_BYTES = (
    MAX_ICON_SIZE_MB * 1024 * 1024
)

ICON_UPLOAD_CHUNK_SIZE = (
    256 * 1024
)

ICON_UPLOAD_DIR_NAME = "icons"


ALLOWED_ICON_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".svg",
}


# =========================================================
# PATH SECURITY
# =========================================================

def get_upload_root() -> Path:

    root = Path(
        UPLOAD_DIR
    ).resolve()

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return root


def get_icon_root() -> Path:

    root = (
        get_upload_root()
        / ICON_UPLOAD_DIR_NAME
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return root.resolve()


def ensure_safe_storage_path(
    file_path: str | Path,
) -> Path:

    root = get_upload_root()

    candidate = Path(
        file_path
    ).resolve()

    try:

        candidate.relative_to(
            root
        )

    except ValueError:

        raise HTTPException(
            status_code=500,
            detail=(
                "Stored app file ka path invalid hai"
            ),
        )

    return candidate


def ensure_safe_icon_path(
    file_path: str | Path,
) -> Path:

    root = get_icon_root()

    candidate = Path(
        file_path
    ).resolve()

    try:

        candidate.relative_to(
            root
        )

    except ValueError:

        raise HTTPException(
            status_code=500,
            detail=(
                "Stored icon path invalid hai"
            ),
        )

    return candidate


# =========================================================
# SAFE FILE DELETE
# =========================================================

def safe_remove(
    file_path: str | Path | None,
) -> None:

    if not file_path:
        return

    try:

        path = ensure_safe_storage_path(
            file_path
        )

    except HTTPException:

        return

    try:

        if (
            path.exists()
            and path.is_file()
        ):

            path.unlink()

    except OSError:

        pass


def safe_remove_icon(
    file_path: str | Path | None,
) -> None:

    if not file_path:
        return

    try:

        path = ensure_safe_icon_path(
            file_path
        )

    except HTTPException:

        return

    try:

        if (
            path.exists()
            and path.is_file()
        ):

            path.unlink()

    except OSError:

        pass


# =========================================================
# FILE VALIDATION
# =========================================================

def validate_archive(
    file_path: str | Path,
    extension: str,
) -> None:

    path = ensure_safe_storage_path(
        file_path
    )

    if (
        not path.exists()
        or not path.is_file()
    ):

        raise ValueError(
            "Uploaded package file nahi mili"
        )

    try:

        with zipfile.ZipFile(
            path,
            "r",
        ) as archive:

            if archive.testzip() is not None:

                raise ValueError(
                    "Package archive corrupted hai"
                )

            infos = archive.infolist()

            if not infos:

                raise ValueError(
                    "Package archive empty hai"
                )

            if (
                len(infos)
                > MAX_ZIP_ENTRIES
            ):

                raise ValueError(
                    "Package me bahut zyada archive entries hain"
                )

            total_uncompressed = 0

            for info in infos:

                if info.file_size < 0:

                    raise ValueError(
                        "Invalid archive entry size"
                    )

                total_uncompressed += (
                    info.file_size
                )

                if (
                    total_uncompressed
                    > MAX_ZIP_UNCOMPRESSED_BYTES
                ):

                    raise ValueError(
                        "Package ka uncompressed size allowed limit se zyada hai"
                    )

            names = {
                info.filename
                for info in infos
            }

            # -------------------------------------------------
            # APK
            # -------------------------------------------------

            if extension == ".apk":

                if (
                    "AndroidManifest.xml"
                    not in names
                ):

                    raise ValueError(
                        "APK me AndroidManifest.xml nahi mila"
                    )

            # -------------------------------------------------
            # AAB
            # -------------------------------------------------

            elif extension == ".aab":

                if (
                    "BundleConfig.pb"
                    not in names
                ):

                    raise ValueError(
                        "AAB me BundleConfig.pb nahi mila"
                    )

                if (
                    "base/manifest/AndroidManifest.xml"
                    not in names
                ):

                    raise ValueError(
                        "AAB me base module manifest nahi mila"
                    )

            else:

                raise ValueError(
                    "Unsupported package type"
                )

    except zipfile.BadZipFile:

        raise ValueError(
            "File valid Android ZIP package nahi hai"
        )

    except zipfile.LargeZipFile:

        raise ValueError(
            "Package archive bahut large hai"
        )


# =========================================================
# PACKAGE UPLOAD STREAM
# =========================================================

async def save_upload_stream(
    file: UploadFile,
    destination: Path,
) -> int:

    total_bytes = 0

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        destination,
        "wb",
    ) as output:

        while True:

            chunk = await file.read(
                UPLOAD_CHUNK_SIZE
            )

            if not chunk:
                break

            total_bytes += len(
                chunk
            )

            if (
                total_bytes
                > MAX_UPLOAD_BYTES
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"File size "
                        f"{MAX_FILE_SIZE_MB}MB "
                        "se zyada nahi honi chahiye"
                    ),
                )

            output.write(
                chunk
            )

    return total_bytes


# =========================================================
# ICON UPLOAD STREAM
# =========================================================

async def save_icon_stream(
    file: UploadFile,
    destination: Path,
) -> int:

    total_bytes = 0

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        destination,
        "wb",
    ) as output:

        while True:

            chunk = await file.read(
                ICON_UPLOAD_CHUNK_SIZE
            )

            if not chunk:
                break

            total_bytes += len(
                chunk
            )

            if (
                total_bytes
                > MAX_ICON_BYTES
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Icon size "
                        f"{MAX_ICON_SIZE_MB}MB "
                        "se zyada nahi ho sakta"
                    ),
                )

            output.write(
                chunk
            )

    return total_bytes


# =========================================================
# INPUT CLEANING
# =========================================================

def clean_app_name(
    value: str,
) -> str:

    value = value.strip()

    if not value:

        raise HTTPException(
            status_code=400,
            detail="App name required hai",
        )

    if (
        len(value)
        > MAX_APP_NAME_LENGTH
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"App name maximum "
                f"{MAX_APP_NAME_LENGTH} characters ka ho sakta hai"
            ),
        )

    return value


def clean_package_name(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    if (
        len(value)
        > MAX_PACKAGE_NAME_LENGTH
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Package name maximum "
                f"{MAX_PACKAGE_NAME_LENGTH} characters ka ho sakta hai"
            ),
        )

    parts = value.split(".")

    if (
        len(parts) < 2
        or any(
            not part
            or not part[0].isalpha()
            or any(
                not (
                    char.isalnum()
                    or char == "_"
                )
                for char in part
            )
            for part in parts
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Valid Android package name dein, "
                "jaise com.example.myapp"
            ),
        )

    return value


def clean_version(
    value: str,
) -> str:

    value = value.strip()

    if not value:

        raise HTTPException(
            status_code=400,
            detail="Version required hai",
        )

    if (
        len(value)
        > MAX_VERSION_LENGTH
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Version maximum "
                f"{MAX_VERSION_LENGTH} characters ka ho sakta hai"
            ),
        )

    return value


def clean_description(
    value: str | None,
) -> str:

    if value is None:
        return ""

    value = value.strip()

    if (
        len(value)
        > MAX_DESCRIPTION_LENGTH
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Description maximum "
                f"{MAX_DESCRIPTION_LENGTH} characters ka ho sakta hai"
            ),
        )

    return value


def clean_category(
    value: str | None,
) -> str:

    if value is None:
        return "Other"

    value = value.strip()

    if not value:
        return "Other"

    if (
        len(value)
        > MAX_CATEGORY_LENGTH
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Category maximum "
                f"{MAX_CATEGORY_LENGTH} characters ka ho sakta hai"
            ),
        )

    return value


def clean_changelog(
    value: str | None,
) -> str:

    if value is None:
        return ""

    value = value.strip()

    if (
        len(value)
        > MAX_CHANGELOG_LENGTH
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Changelog maximum "
                f"{MAX_CHANGELOG_LENGTH} characters ka ho sakta hai"
            ),
        )

    return value


# =========================================================
# PACKAGE EXTENSION
# =========================================================

def get_extension(
    filename: str | None,
) -> str:

    if not filename:

        raise HTTPException(
            status_code=400,
            detail="File required hai",
        )

    filename = os.path.basename(
        filename
    )

    ext = os.path.splitext(
        filename
    )[1].lower()

    if (
        ext
        not in ALLOWED_EXTENSIONS
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Sirf .apk ya .aab files allowed hain"
            ),
        )

    return ext


# =========================================================
# ICON EXTENSION
# =========================================================

def get_icon_extension(
    filename: str | None,
) -> str:

    if not filename:

        raise HTTPException(
            status_code=400,
            detail="Icon file required hai",
        )

    filename = os.path.basename(
        filename
    )

    ext = os.path.splitext(
        filename
    )[1].lower()

    if (
        ext
        not in ALLOWED_ICON_EXTENSIONS
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Icon ke liye sirf "
                ".png, .jpg, .jpeg, .webp ya .svg "
                "files allowed hain"
            ),
        )

    return ext


# =========================================================
# ICON URL
# =========================================================

def get_icon_url(
    app_id: int,
    icon_path: str | None,
) -> str | None:

    if not icon_path:
        return None

    return f"/apps/{app_id}/icon"


# =========================================================
# OWNER CHECK
# =========================================================

def get_app_for_owner(
    app_id: int,
    current_user: User,
    db: Session,
) -> App:

    app = (
        db.query(App)
        .filter(
            App.id == app_id
        )
        .first()
    )

    if app is None:

        raise HTTPException(
            status_code=404,
            detail="App nahi mila",
        )

    if (
        app.developer_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Aap sirf apne uploaded app ko "
                "manage kar sakte hain."
            ),
        )

    return app


# =========================================================
# UPLOAD APK / AAB + ICON
# =========================================================

@router.post(
    "/upload",
    response_model=AppUploadResponse,
)
async def upload_app(

    app_name: str = Form(...),

    package_name: str | None = Form(None),

    version: str = Form(...),

    file: UploadFile = File(...),

    icon: UploadFile | None = File(None),

    description: str = Form(""),

    category: str = Form("Other"),

    changelog: str = Form(""),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    if current_user is None:

        raise HTTPException(
            status_code=401,
            detail="Login required hai",
        )

    if not current_user.is_developer:

        raise HTTPException(
            status_code=403,
            detail=(
                "Sirf developer account app upload "
                "kar sakta hai"
            ),
        )

    if not current_user.developer_active:

        raise HTTPException(
            status_code=403,
            detail=(
                "Developer account active nahi hai. "
                "App upload karne se pehle developer "
                "account activate karein."
            ),
        )

    app_name = clean_app_name(
        app_name
    )

    package_name = clean_package_name(
        package_name
    )

    version = clean_version(
        version
    )

    description = clean_description(
        description
    )

    category = clean_category(
        category
    )

    changelog = clean_changelog(
        changelog
    )

    ext = get_extension(
        file.filename
    )

    upload_root = get_upload_root()

    upload_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_path = (
        upload_root
        / f"{uuid.uuid4().hex}{ext}"
    )

    final_path = original_path

    icon_file_path = None
    icon_path = None

    if icon is not None:

        icon_ext = get_icon_extension(
            icon.filename
        )

        icon_file_path = (
            get_icon_root()
            / f"{uuid.uuid4().hex}{icon_ext}"
        )

    try:

        uploaded_bytes = (
            await save_upload_stream(
                file,
                original_path,
            )
        )

        if uploaded_bytes <= 0:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file empty hai",
            )

        try:

            validate_archive(
                original_path,
                ext,
            )

        except ValueError as exc:

            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )

        if ext == ".aab":

            try:

                generated_apk = (
                    convert_aab_to_apk(
                        str(original_path)
                    )
                )

            except ConversionError:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "AAB ko installable APK me "
                        "convert nahi kiya ja saka"
                    ),
                )

            final_path = (
                ensure_safe_storage_path(
                    generated_apk
                )
            )

            if (
                final_path.suffix.lower()
                != ".apk"
            ):

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Generated APK path invalid hai"
                    ),
                )

            try:

                validate_archive(
                    final_path,
                    ".apk",
                )

            except ValueError as exc:

                raise HTTPException(
                    status_code=500,
                    detail=str(exc),
                )

            safe_remove(
                original_path
            )

        final_path = (
            ensure_safe_storage_path(
                final_path
            )
        )

        if not final_path.exists():

            raise HTTPException(
                status_code=500,
                detail=(
                    "Final app file generate nahi hui"
                ),
            )

        final_size_bytes = (
            final_path.stat().st_size
        )

        if final_size_bytes <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Final app file empty hai"
                ),
            )

        if (
            final_size_bytes
            > MAX_UPLOAD_BYTES
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Generated APK "
                    f"{MAX_FILE_SIZE_MB}MB limit "
                    "se bada hai"
                ),
            )

        final_size_mb = (
            final_size_bytes
            / (1024 * 1024)
        )

        if icon is not None:

            icon_bytes = (
                await save_icon_stream(
                    icon,
                    icon_file_path,
                )
            )

            if icon_bytes <= 0:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Icon file empty hai"
                    ),
                )

            icon_path = str(
                ensure_safe_icon_path(
                    icon_file_path
                )
            )

        new_app = App(

            developer_id=current_user.id,

            app_name=app_name,

            package_name=package_name,

            version=version,

            file_type=ext,

            file_path=str(
                final_path
            ),

            size_mb=round(
                final_size_mb,
                2,
            ),

            description=description,

            category=category,

            changelog=changelog,

            icon_path=icon_path,

        )

        db.add(
            new_app
        )

        db.commit()

        db.refresh(
            new_app
        )

    except HTTPException:

        db.rollback()

        safe_remove(
            final_path
        )

        if (
            str(original_path)
            != str(final_path)
        ):

            safe_remove(
                original_path
            )

        safe_remove_icon(
            icon_file_path
        )

        raise

    except Exception:

        db.rollback()

        safe_remove(
            final_path
        )

        if (
            str(original_path)
            != str(final_path)
        ):

            safe_remove(
                original_path
            )

        safe_remove_icon(
            icon_file_path
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "App upload process complete nahi ho paya"
            ),
        )

    return AppUploadResponse(

        message=(
            "App upload ho gaya aur database "
            "mein save ho gaya"
        ),

        app_name=new_app.app_name,

        package_name=new_app.package_name,

        version=new_app.version,

        file_type=new_app.file_type,

        size_mb=round(
            new_app.size_mb or 0,
            2,
        ),

        stored_as=os.path.basename(
            new_app.file_path
        ),

        icon_path=new_app.icon_path,

        icon_url=get_icon_url(
            new_app.id,
            new_app.icon_path,
        ),

        changelog=new_app.changelog or "",

        status=new_app.status,

    )


# =========================================================
# LIST ALL PUBLISHED APPS
# =========================================================

@router.get("/")
def list_apps(

    db: Session = Depends(get_db),

):

    apps = (
        db.query(App)
        .filter(
            App.status == "published"
        )
        .order_by(
            App.created_at.desc()
        )
        .all()
    )

    return {

        "apps": [

            {

                "id": app.id,

                "app_name": app.app_name,

                "package_name": (
                    app.package_name
                ),

                "version": app.version,

                "file_type": app.file_type,

                "size_mb": app.size_mb,

                "stored_as": os.path.basename(
                    app.file_path
                ),

                "developer_id": (
                    app.developer_id
                ),

                "description": (
                    app.description or ""
                ),

                "category": (
                    app.category or "Other"
                ),

                "changelog": (
                    app.changelog or ""
                ),

                "icon_path": (
                    app.icon_path
                ),

                "icon_url": get_icon_url(
                    app.id,
                    app.icon_path,
                ),

                "status": (
                    app.status
                ),

                "download_count": (
                    app.download_count or 0
                ),

                "view_count": (
                    app.view_count or 0
                ),

                "rating": (
                    app.rating or 0
                ),

                "review_count": (
                    app.review_count or 0
                ),

                "created_at": (
                    app.created_at
                ),

                "updated_at": (
                    app.updated_at
                ),

            }

            for app in apps

        ]

    }


# =========================================================
# MY APPS
# =========================================================

@router.get("/mine")
def list_my_apps(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),

):

    if current_user is None:

        raise HTTPException(
            status_code=401,
            detail="Login required hai",
        )

    apps = (
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

    return {

        "apps": [

            {

                "id": app.id,

                "app_name": app.app_name,

                "package_name": (
                    app.package_name
                ),

                "version": app.version,

                "file_type": app.file_type,

                "size_mb": app.size_mb,

                "stored_as": os.path.basename(
                    app.file_path
                ),

                "developer_id": (
                    app.developer_id
                ),

                "description": (
                    app.description or ""
                ),

                "category": (
                    app.category or "Other"
                ),

                "changelog": (
                    app.changelog or ""
                ),

                "icon_path": (
                    app.icon_path
                ),

                "icon_url": get_icon_url(
                    app.id,
                    app.icon_path,
                ),

                "status": (
                    app.status
                ),

                "download_count": (
                    app.download_count or 0
                ),

                "view_count": (
                    app.view_count or 0
                ),

                "rating": (
                    app.rating or 0
                ),

                "review_count": (
                    app.review_count or 0
                ),

                "created_at": (
                    app.created_at
                ),

                "updated_at": (
                    app.updated_at
                ),

            }

            for app in apps

        ]

    }


# =========================================================
# APP ICON
# =========================================================

@router.get(
    "/{app_id}/icon"
)
def get_app_icon(

    app_id: int,

    db: Session = Depends(get_db),

):

    app = (
        db.query(App)
        .filter(
            App.id == app_id
        )
        .first()
    )

    if app is None:

        raise HTTPException(
            status_code=404,
            detail="App nahi mila",
        )

    if not app.icon_path:

        raise HTTPException(
            status_code=404,
            detail=(
                "App icon available nahi hai"
            ),
        )

    icon_path = (
        ensure_safe_icon_path(
            app.icon_path
        )
    )

    if not icon_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "App icon storage me nahi mila"
            ),
        )

    if not icon_path.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                "App icon valid file nahi hai"
            ),
        )

    media_types = {

        ".png":
            "image/png",

        ".jpg":
            "image/jpeg",

        ".jpeg":
            "image/jpeg",

        ".webp":
            "image/webp",

        ".svg":
            "image/svg+xml",

    }

    media_type = media_types.get(
        icon_path.suffix.lower(),
        "application/octet-stream",
    )

    return FileResponse(
        path=str(
            icon_path
        ),
        media_type=media_type,
    )


# =========================================================
# APP DETAILS
# =========================================================

@router.get(
    "/{app_id}",
    response_model=AppDetailsResponse,
)
def get_app_details(

    app_id: int,

    db: Session = Depends(get_db),

):

    app = (
        db.query(App)
        .filter(
            App.id == app_id
        )
        .first()
    )

    if app is None:

        raise HTTPException(
            status_code=404,
            detail="App nahi mila",
        )

    # -----------------------------------------------------
    # VIEW COUNT
    # -----------------------------------------------------

    app.view_count = (
        (app.view_count or 0)
        + 1
    )

    db.commit()

    db.refresh(
        app
    )

    return AppDetailsResponse(

        id=app.id,

        app_name=app.app_name,

        package_name=(
            app.package_name
        ),

        version=app.version,

        file_type=app.file_type,

        size_mb=app.size_mb,

        stored_as=os.path.basename(
            app.file_path
        ),

        developer_id=(
            app.developer_id
        ),

        description=(
            app.description or ""
        ),

        category=(
            app.category or "Other"
        ),

        icon_path=(
            app.icon_path
        ),

        icon_url=get_icon_url(
            app.id,
            app.icon_path,
        ),

        status=(
            app.status
        ),

        # IMPORTANT:
        # Existing database records may contain NULL.
        # AppDetailsResponse expects a string.
        changelog=(
            app.changelog or ""
        ),

        download_count=(
            app.download_count or 0
        ),

        view_count=(
            app.view_count or 0
        ),

        rating=(
            app.rating or 0
        ),

        review_count=(
            app.review_count or 0
        ),

        created_at=(
            app.created_at
        ),

        updated_at=(
            app.updated_at
        ),

    )


# =========================================================
# UPDATE APP
# =========================================================

@router.put(
    "/{app_id}/update",
    response_model=AppUploadResponse,
)
async def update_app(

    app_id: int,

    version: str = Form(...),

    file: UploadFile = File(...),

    icon: UploadFile | None = File(None),

    description: str | None = Form(None),

    category: str | None = Form(None),

    package_name: str | None = Form(None),

    changelog: str | None = Form(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),

):

    if current_user is None:

        raise HTTPException(
            status_code=401,
            detail="Login required hai",
        )

    if not current_user.is_developer:

        raise HTTPException(
            status_code=403,
            detail=(
                "Developer account required hai"
            ),
        )

    if not current_user.developer_active:

        raise HTTPException(
            status_code=403,
            detail=(
                "Developer account active nahi hai"
            ),
        )

    app = get_app_for_owner(
        app_id,
        current_user,
        db,
    )

    version = clean_version(
        version
    )

    if package_name is not None:

        package_name = clean_package_name(
            package_name
        )

    if description is not None:

        description = (
            clean_description(
                description
            )
        )

    if category is not None:

        category = (
            clean_category(
                category
            )
        )

    if changelog is not None:

        changelog = clean_changelog(
            changelog
        )

    ext = get_extension(
        file.filename
    )

    upload_root = get_upload_root()

    upload_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_path = (
        upload_root
        / f"{uuid.uuid4().hex}{ext}"
    )

    new_final_path = original_path

    old_path = (
        ensure_safe_storage_path(
            app.file_path
        )
    )

    old_icon_path = (
        app.icon_path
    )

    new_icon_file_path = None
    new_icon_path = None

    if icon is not None:

        icon_ext = (
            get_icon_extension(
                icon.filename
            )
        )

        new_icon_file_path = (
            get_icon_root()
            / f"{uuid.uuid4().hex}{icon_ext}"
        )

    try:

        uploaded_bytes = (
            await save_upload_stream(
                file,
                original_path,
            )
        )

        if uploaded_bytes <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file empty hai"
                ),
            )

        try:

            validate_archive(
                original_path,
                ext,
            )

        except ValueError as exc:

            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )

        if ext == ".aab":

            try:

                generated_apk = (
                    convert_aab_to_apk(
                        str(original_path)
                    )
                )

            except ConversionError:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "AAB ko installable APK me "
                        "convert nahi kiya ja saka"
                    ),
                )

            new_final_path = (
                ensure_safe_storage_path(
                    generated_apk
                )
            )

            if (
                new_final_path.suffix.lower()
                != ".apk"
            ):

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Generated APK path invalid hai"
                    ),
                )

            try:

                validate_archive(
                    new_final_path,
                    ".apk",
                )

            except ValueError as exc:

                raise HTTPException(
                    status_code=500,
                    detail=str(exc),
                )

            safe_remove(
                original_path
            )

        new_final_path = (
            ensure_safe_storage_path(
                new_final_path
            )
        )

        if not new_final_path.exists():

            raise HTTPException(
                status_code=500,
                detail=(
                    "Updated app file generate nahi hui"
                ),
            )

        final_size_bytes = (
            new_final_path.stat().st_size
        )

        if final_size_bytes <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Updated app file empty hai"
                ),
            )

        if (
            final_size_bytes
            > MAX_UPLOAD_BYTES
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Generated APK "
                    f"{MAX_FILE_SIZE_MB}MB limit "
                    "se bada hai"
                ),
            )

        final_size_mb = (
            final_size_bytes
            / (1024 * 1024)
        )

        if icon is not None:

            icon_bytes = (
                await save_icon_stream(
                    icon,
                    new_icon_file_path,
                )
            )

            if icon_bytes <= 0:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "New icon file empty hai"
                    ),
                )

            new_icon_path = str(
                ensure_safe_icon_path(
                    new_icon_file_path
                )
            )

        app.version = version

        app.file_type = ext

        app.file_path = str(
            new_final_path
        )

        app.size_mb = round(
            final_size_mb,
            2,
        )

        if package_name is not None:

            app.package_name = (
                package_name
            )

        if description is not None:

            app.description = (
                description
            )

        if category is not None:

            app.category = category

        if changelog is not None:

            app.changelog = (
                changelog
            )

        if new_icon_path is not None:

            app.icon_path = (
                new_icon_path
            )

        db.commit()

        db.refresh(
            app
        )

    except HTTPException:

        db.rollback()

        safe_remove(
            new_final_path
        )

        if (
            str(original_path)
            != str(new_final_path)
        ):

            safe_remove(
                original_path
            )

        safe_remove_icon(
            new_icon_file_path
        )

        raise

    except Exception:

        db.rollback()

        safe_remove(
            new_final_path
        )

        if (
            str(original_path)
            != str(new_final_path)
        ):

            safe_remove(
                original_path
            )

        safe_remove_icon(
            new_icon_file_path
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "App update process complete nahi ho paya"
            ),
        )

    # =====================================================
    # DELETE OLD PACKAGE
    # =====================================================

    if (
        old_path != new_final_path
        and old_path.exists()
        and old_path.is_file()
    ):

        try:

            old_path.unlink()

        except OSError:

            pass

    # =====================================================
    # DELETE OLD ICON
    # =====================================================

    if (
        new_icon_path is not None
        and old_icon_path
        and old_icon_path
        != new_icon_path
    ):

        safe_remove_icon(
            old_icon_path
        )

    return AppUploadResponse(

        message=(
            "App successfully update ho gaya"
        ),

        app_name=app.app_name,

        package_name=(
            app.package_name
        ),

        version=app.version,

        file_type=app.file_type,

        size_mb=round(
            app.size_mb or 0,
            2,
        ),

        stored_as=os.path.basename(
            app.file_path
        ),

        icon_path=app.icon_path,

        icon_url=get_icon_url(
            app.id,
            app.icon_path,
        ),

        changelog=(
            app.changelog or ""
        ),

        status=(
            app.status
        ),

    )


# =========================================================
# DELETE APP
# =========================================================

@router.delete(
    "/{app_id}",
)
def delete_app(

    app_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),

):

    if current_user is None:

        raise HTTPException(
            status_code=401,
            detail="Login required hai",
        )

    if not current_user.is_developer:

        raise HTTPException(
            status_code=403,
            detail=(
                "Developer account required hai"
            ),
        )

    if not current_user.developer_active:

        raise HTTPException(
            status_code=403,
            detail=(
                "Developer account active nahi hai"
            ),
        )

    app = get_app_for_owner(
        app_id,
        current_user,
        db,
    )

    file_path = (
        ensure_safe_storage_path(
            app.file_path
        )
    )

    icon_path = None

    if app.icon_path:

        icon_path = (
            ensure_safe_icon_path(
                app.icon_path
            )
        )

    try:

        db.delete(
            app
        )

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "App database se delete nahi ho paya"
            ),
        )

    file_deleted = False

    if file_path.exists():

        try:

            file_path.unlink()

            file_deleted = True

        except OSError:

            file_deleted = False

    icon_deleted = False

    if icon_path is not None:

        if icon_path.exists():

            try:

                icon_path.unlink()

                icon_deleted = True

            except OSError:

                icon_deleted = False

    return {

        "message": (
            "App successfully delete ho gaya"
        ),

        "app_id": app_id,

        "file_deleted": file_deleted,

        "icon_deleted": icon_deleted,

    }


# =========================================================
# DOWNLOAD APP
# =========================================================

@router.get(
    "/{app_id}/download"
)
def download_app(

    app_id: int,

    db: Session = Depends(get_db),

):

    app = (
        db.query(App)
        .filter(
            App.id == app_id
        )
        .first()
    )

    if app is None:

        raise HTTPException(
            status_code=404,
            detail="App nahi mila",
        )

    if app.status != "published":

        raise HTTPException(
            status_code=404,
            detail=(
                "Ye app marketplace me available nahi hai"
            ),
        )

    file_path = (
        ensure_safe_storage_path(
            app.file_path
        )
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "App file storage me nahi mili"
            ),
        )

    if not file_path.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                "App file storage me valid nahi hai"
            ),
        )

    app.download_count = (
        (app.download_count or 0)
        + 1
    )

    db.commit()

    db.refresh(
        app
    )

    download_name = (
        f"{app.app_name}"
        f"-{app.version}.apk"
    )

    safe_download_name = (
        download_name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )

    return FileResponse(

        path=str(
            file_path
        ),

        media_type=(
            "application/vnd.android.package-archive"
        ),

        filename=safe_download_name,

    )

