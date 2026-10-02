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

from fastapi.responses import (
    FileResponse,
    StreamingResponse,
)

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

from app.services import b2_storage


router = APIRouter(
    prefix="/apps",
    tags=["Apps"],
)

# =========================================================
# TEMPORARY B2 DATABASE MIGRATION
# =========================================================

@router.post(
    "/admin/migrate-b2-paths",
)
def migrate_b2_paths(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -----------------------------------------------------
    # Developer authentication
    # -----------------------------------------------------
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Login required hai",
        )

    if not current_user.is_developer:
        raise HTTPException(
            status_code=403,
            detail="Developer account required hai",
        )

    if not current_user.developer_active:
        raise HTTPException(
            status_code=403,
            detail="Developer account active nahi hai",
        )

    # -----------------------------------------------------
    # ONLY these exact app IDs are migrated.
    # No other app record is touched.
    # -----------------------------------------------------
    migrations = {
        3: "apps/1/381af67b-75c4-4304-8a1c-714342b8a351.apk",
        4: "apps/1/e42841f3-345a-48ec-8f69-102b89674f62.apk",
        5: "apps/1/867f25430dde449d9f4bc87470c599da.apk",
    }

    results = []

    try:
        for app_id, new_b2_path in migrations.items():
            app = (
                db.query(App)
                .filter(App.id == app_id)
                .first()
            )

            if app is None:
                results.append(
                    {
                        "id": app_id,
                        "status": "not_found",
                    }
                )
                continue

            old_path = (
                str(app.file_path).strip()
                if app.file_path
                else ""
            )

            # Already migrated: do nothing.
            if old_path == new_b2_path:
                results.append(
                    {
                        "id": app_id,
                        "app_name": app.app_name,
                        "old_path": old_path,
                        "new_path": new_b2_path,
                        "status": "already_migrated",
                    }
                )
                continue

            app.file_path = new_b2_path

            results.append(
                {
                    "id": app_id,
                    "app_name": app.app_name,
                    "old_path": old_path,
                    "new_path": new_b2_path,
                    "status": "updated",
                }
            )

        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "B2 database migration failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        )

    return {
        "message": "B2 file paths database mein migrate ho gaye",
        "migrated_by_user_id": current_user.id,
        "results": results,
    }
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
# B2 STORAGE HELPERS
# =========================================================

def is_b2_object(
    value: str | None,
) -> bool:

    if not value:
        return False

    value = str(
        value
    ).strip()

    return (
        value.startswith("apps/")
        or value.startswith("icons/")
    )


def get_b2_app_key(
    developer_id: int,
) -> str:

    return (
        f"apps/{developer_id}/"
        f"{uuid.uuid4().hex}.apk"
    )


def get_b2_icon_key(
    developer_id: int,
    extension: str,
) -> str:

    return (
        f"icons/{developer_id}/"
        f"{uuid.uuid4().hex}{extension}"
    )


def get_storage_name(
    storage_path: str | None,
) -> str | None:

    if not storage_path:
        return None

    return os.path.basename(
        str(storage_path)
    )


# =========================================================
# DELETE STORED APP FILE
# =========================================================
#
# Returns:
#   True  = deleted successfully / already absent
#   False = deletion failed or invalid path
#
# Supports:
#   1. Backblaze B2 object
#   2. Legacy local storage file
#
# =========================================================

def delete_stored_file(
    storage_path: str | None,
) -> bool:

    if not storage_path:
        return False

    storage_path = str(
        storage_path
    ).strip()

    if not storage_path:
        return False

    # -----------------------------------------------------
    # B2 OBJECT
    # -----------------------------------------------------

    if is_b2_object(
        storage_path
    ):

        try:

            result = (
                b2_storage.delete_file(
                    storage_path
                )
            )

            # Some storage implementations return None
            # on successful deletion.
            if result is None:
                return True

            return bool(
                result
            )

        except Exception as exc:

            print(
                f"[B2 DELETE ERROR] "
                f"Could not delete object "
                f"{storage_path}: "
                f"{type(exc).__name__}: {exc}"
            )

            return False

    # -----------------------------------------------------
    # LEGACY LOCAL FILE
    # -----------------------------------------------------

    try:

        path = ensure_safe_storage_path(
            storage_path
        )

    except HTTPException as exc:

        print(
            f"[LOCAL DELETE WARNING] "
            f"Invalid stored app path: "
            f"{storage_path} | "
            f"{exc.detail}"
        )

        return False

    # Already absent = cleanup completed.
    if not path.exists():
        return True

    if not path.is_file():

        print(
            f"[LOCAL DELETE WARNING] "
            f"Stored app path is not a file: "
            f"{path}"
        )

        return False

    try:

        path.unlink()

        return not path.exists()

    except OSError as exc:

        print(
            f"[LOCAL DELETE ERROR] "
            f"Could not delete local app file "
            f"{path}: "
            f"{type(exc).__name__}: {exc}"
        )

        return False


# =========================================================
# DELETE STORED ICON
# =========================================================
#
# Returns:
#   True  = deleted successfully / already absent
#   False = deletion failed or invalid path
#
# =========================================================

def delete_stored_icon(
    icon_path: str | None,
) -> bool:

    if not icon_path:
        return False

    icon_path = str(
        icon_path
    ).strip()

    if not icon_path:
        return False

    # -----------------------------------------------------
    # B2 OBJECT
    # -----------------------------------------------------

    if is_b2_object(
        icon_path
    ):

        try:

            result = (
                b2_storage.delete_file(
                    icon_path
                )
            )

            if result is None:
                return True

            return bool(
                result
            )

        except Exception as exc:

            print(
                f"[B2 ICON DELETE ERROR] "
                f"Could not delete icon "
                f"{icon_path}: "
                f"{type(exc).__name__}: {exc}"
            )

            return False

    # -----------------------------------------------------
    # LEGACY LOCAL ICON
    # -----------------------------------------------------

    try:

        path = ensure_safe_icon_path(
            icon_path
        )

    except HTTPException as exc:

        print(
            f"[LOCAL ICON DELETE WARNING] "
            f"Invalid stored icon path: "
            f"{icon_path} | "
            f"{exc.detail}"
        )

        return False

    if not path.exists():
        return True

    if not path.is_file():

        print(
            f"[LOCAL ICON DELETE WARNING] "
            f"Stored icon path is not a file: "
            f"{path}"
        )

        return False

    try:

        path.unlink()

        return not path.exists()

    except OSError as exc:

        print(
            f"[LOCAL ICON DELETE ERROR] "
            f"Could not delete local icon "
            f"{path}: "
            f"{type(exc).__name__}: {exc}"
        )

        return False


# =========================================================
# B2 SAFE CLEANUP
# =========================================================
#
# IMPORTANT:
#
# This helper is ONLY for newly-created B2 objects which have
# NOT yet been committed into the database.
#
# If DB commit has already succeeded, this function MUST NOT
# be called for the current/new object.
#
# =========================================================

def cleanup_new_b2_object(
    storage_path: str | None,
) -> None:

    if not storage_path:
        return

    storage_path = str(
        storage_path
    ).strip()

    if not storage_path:
        return

    if not is_b2_object(
        storage_path
    ):
        return

    try:

        result = (
            b2_storage.delete_file(
                storage_path
            )
        )

        print(
            f"[B2 CLEANUP] "
            f"Deleted temporary object: "
            f"{storage_path} "
            f"result={result}"
        )

    except Exception as exc:

        print(
            f"[B2 CLEANUP WARNING] "
            f"Could not delete temporary object "
            f"{storage_path}: "
            f"{type(exc).__name__}: {exc}"
        )


# =========================================================
# SAFE OLD STORAGE DELETE
# =========================================================
#
# Used AFTER DB commit.
#
# If old object cannot be deleted, the new DB reference remains
# valid. Old object becomes an orphan and can be cleaned later.
#
# =========================================================

def safe_delete_old_storage(
    storage_path: str | None,
    storage_type: str = "file",
) -> bool:

    if not storage_path:
        return False

    try:

        if storage_type == "icon":

            deleted = (
                delete_stored_icon(
                    storage_path
                )
            )

        else:

            deleted = (
                delete_stored_file(
                    storage_path
                )
            )

        if deleted:

            print(
                f"[OLD STORAGE DELETE] "
                f"Deleted old {storage_type}: "
                f"{storage_path}"
            )

        else:

            print(
                f"[OLD STORAGE DELETE WARNING] "
                f"Old {storage_type} was not deleted: "
                f"{storage_path}"
            )

        return deleted

    except Exception as exc:

        print(
            f"[OLD STORAGE DELETE WARNING] "
            f"Could not delete old {storage_type}: "
            f"{storage_path} | "
            f"{type(exc).__name__}: {exc}"
        )

        return False


# =========================================================
# SAFE LOCAL FILE DELETE
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

    # =====================================================
    # AUTHORIZATION
    # =====================================================

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

    # =====================================================
    # INPUT CLEANING
    # =====================================================

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

    # =====================================================
    # LOCAL TEMP PATHS
    # =====================================================

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

    b2_app_key = None

    b2_icon_key = None

    # DB transaction state
    db_committed = False

    # =====================================================
    # ICON TEMP PATH
    # =====================================================

    if icon is not None:

        icon_ext = get_icon_extension(
            icon.filename
        )

        icon_file_path = (
            get_icon_root()
            / f"{uuid.uuid4().hex}{icon_ext}"
        )

    try:

        # =================================================
        # SAVE TEMP PACKAGE LOCALLY
        # =================================================

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

        # =================================================
        # VALIDATE ORIGINAL PACKAGE
        # =================================================

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

        # =================================================
        # AAB -> APK
        # =================================================

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

        # =================================================
        # FINAL LOCAL APK VALIDATION
        # =================================================

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

        # =================================================
        # SAVE TEMP ICON
        # =================================================

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

            ensure_safe_icon_path(
                icon_file_path
            )

        # =================================================
        # GENERATE B2 APK KEY
        # =================================================

        b2_app_key = get_b2_app_key(
            current_user.id
        )

        print(
            f"[B2 UPLOAD] APK key: "
            f"{b2_app_key}"
        )

        # =================================================
        # UPLOAD APK TO B2
        # =================================================

        b2_storage.upload_file(
            final_path,
            b2_app_key,
            "application/vnd.android.package-archive",
        )

        print(
            f"[B2 UPLOAD] APK upload successful: "
            f"{b2_app_key}"
        )

        # =================================================
        # UPLOAD ICON TO B2
        # =================================================

        if icon_file_path is not None:

            icon_ext = (
                icon_file_path
                .suffix
                .lower()
            )

            b2_icon_key = get_b2_icon_key(
                current_user.id,
                icon_ext,
            )

            icon_media_types = {

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

            b2_storage.upload_file(
                icon_file_path,
                b2_icon_key,
                icon_media_types.get(
                    icon_ext,
                    "application/octet-stream",
                ),
            )

            print(
                f"[B2 UPLOAD] Icon upload successful: "
                f"{b2_icon_key}"
            )

        # =================================================
        # CREATE DATABASE OBJECT
        # =================================================

        new_app = App(

            developer_id=current_user.id,

            app_name=app_name,

            package_name=package_name,

            version=version,

            file_type=".apk",

            file_path=b2_app_key,

            size_mb=round(
                final_size_mb,
                2,
            ),

            description=description,

            category=category,

            changelog=changelog,

            icon_path=b2_icon_key,

        )

        db.add(
            new_app
        )

        # =================================================
        # DATABASE COMMIT
        # =================================================

        db.commit()

        # IMPORTANT:
        #
        # From this exact point the B2 objects are referenced
        # by a committed database row.
        #
        # Therefore later errors MUST NOT delete the new
        # B2 objects.
        #
        db_committed = True

        print(
            f"[APP UPLOAD] DB commit successful. "
            f"App ID={new_app.id}"
        )

        # =================================================
        # REFRESH AFTER COMMIT
        # =================================================

        try:

            db.refresh(
                new_app
            )

        except Exception as refresh_error:

            print(
                f"[APP UPLOAD WARNING] "
                f"DB refresh failed after commit: "
                f"{type(refresh_error).__name__}: "
                f"{refresh_error}"
            )

        # =================================================
        # TEMP LOCAL CLEANUP
        # =================================================

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

        # =================================================
        # RESPONSE
        # =================================================

        return AppUploadResponse(

            message=(
                "App upload ho gaya aur Backblaze B2 "
                "storage mein save ho gaya"
            ),

            app_name=new_app.app_name,

            package_name=new_app.package_name,

            version=new_app.version,

            file_type=new_app.file_type,

            size_mb=round(
                new_app.size_mb or 0,
                2,
            ),

            stored_as=get_storage_name(
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

    except HTTPException:

        # =================================================
        # BEFORE DB COMMIT
        # =================================================

        if not db_committed:

            try:

                db.rollback()

            except Exception:

                pass

            # Only NEW/uncommitted B2 objects are deleted.
            cleanup_new_b2_object(
                b2_app_key
            )

            cleanup_new_b2_object(
                b2_icon_key
            )

        # =================================================
        # AFTER DB COMMIT
        # =================================================

        else:

            try:

                db.rollback()

            except Exception:

                pass

            print(
                "[APP UPLOAD WARNING] "
                "DB already committed. "
                "New B2 objects preserved."
            )

        # =================================================
        # LOCAL TEMP CLEANUP
        # =================================================

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

    except Exception as exc:

        print(
            f"[APP UPLOAD ERROR] "
            f"{type(exc).__name__}: {exc}"
        )

        # =================================================
        # BEFORE DB COMMIT
        # =================================================

        if not db_committed:

            try:

                db.rollback()

            except Exception:

                pass

            cleanup_new_b2_object(
                b2_app_key
            )

            cleanup_new_b2_object(
                b2_icon_key
            )

        # =================================================
        # AFTER DB COMMIT
        # =================================================

        else:

            try:

                db.rollback()

            except Exception:

                pass

            print(
                "[APP UPLOAD WARNING] "
                "DB already committed. "
                "New B2 objects intentionally preserved."
            )

        # =================================================
        # LOCAL TEMP CLEANUP
        # =================================================

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

        if db_committed:

            raise HTTPException(
                status_code=500,
                detail=(
                    "App database aur B2 mein save ho gaya hai, "
                    "lekin final response complete nahi ho paya. "
                    "Retry karne se pehle app verify karein."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "App upload process complete nahi ho paya"
            ),
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

                "stored_as": get_storage_name(
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

                "stored_as": get_storage_name(
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

    extension = os.path.splitext(
        str(app.icon_path)
    )[1].lower()

    media_type = media_types.get(
        extension,
        "application/octet-stream",
    )

    # =====================================================
    # B2 ICON
    # =====================================================

    if is_b2_object(
        app.icon_path
    ):

        try:

            response = (
                b2_storage.download_file(
                    str(app.icon_path).strip()
                )
            )

        except Exception as exc:

            print(
                f"[ICON] B2 download failed: "
                f"{type(exc).__name__}: {exc}"
            )

            raise HTTPException(
                status_code=404,
                detail=(
                    "App icon B2 storage me nahi mila"
                ),
            )

        headers = {}

        if response.get(
            "ContentLength"
        ) is not None:

            headers[
                "Content-Length"
            ] = str(
                response[
                    "ContentLength"
                ]
            )

        return StreamingResponse(

            response[
                "Body"
            ].iter_chunks(
                chunk_size=256 * 1024
            ),

            media_type=media_type,

            headers=headers,

        )

    # =====================================================
    # LEGACY LOCAL ICON
    # =====================================================

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

        stored_as=get_storage_name(
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

    # =====================================================
    # AUTHORIZATION
    # =====================================================

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

    # =====================================================
    # FIND APP + OWNER CHECK
    # =====================================================

    app = get_app_for_owner(
        app_id,
        current_user,
        db,
    )

    # =====================================================
    # SAVE OLD STORAGE REFERENCES
    # =====================================================
    #
    # These values MUST remain unchanged until the new DB
    # transaction has successfully committed.
    #
    # =====================================================

    old_storage_path = (
        app.file_path
    )

    old_icon_path = (
        app.icon_path
    )

    # =====================================================
    # CLEAN INPUT
    # =====================================================

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

    # =====================================================
    # LOCAL TEMP PATHS
    # =====================================================

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

    new_icon_file_path = None

    # =====================================================
    # NEW B2 KEYS
    # =====================================================

    b2_app_key = None

    b2_icon_key = None

    # =====================================================
    # DB STATE
    # =====================================================

    db_committed = False

    # =====================================================
    # NEW ICON TEMP PATH
    # =====================================================

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

        # =================================================
        # SAVE NEW PACKAGE LOCALLY
        # =================================================

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

        # =================================================
        # VALIDATE PACKAGE
        # =================================================

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

        # =================================================
        # AAB -> APK
        # =================================================

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

        # =================================================
        # FINAL PACKAGE VALIDATION
        # =================================================

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

        # =================================================
        # SAVE NEW ICON LOCALLY
        # =================================================

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

            ensure_safe_icon_path(
                new_icon_file_path
            )

        # =================================================
        # GENERATE NEW B2 APK KEY
        # =================================================

        b2_app_key = get_b2_app_key(
            current_user.id
        )

        print(
            f"[B2 UPDATE] New APK key: "
            f"{b2_app_key}"
        )

        # =================================================
        # UPLOAD NEW APK TO B2
        # =================================================

        b2_storage.upload_file(
            new_final_path,
            b2_app_key,
            "application/vnd.android.package-archive",
        )

        print(
            f"[B2 UPDATE] New APK upload successful: "
            f"{b2_app_key}"
        )

        # =================================================
        # UPLOAD NEW ICON TO B2
        # =================================================

        if new_icon_file_path is not None:

            icon_ext = (
                new_icon_file_path
                .suffix
                .lower()
            )

            b2_icon_key = get_b2_icon_key(
                current_user.id,
                icon_ext,
            )

            icon_media_types = {

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

            b2_storage.upload_file(
                new_icon_file_path,
                b2_icon_key,
                icon_media_types.get(
                    icon_ext,
                    "application/octet-stream",
                ),
            )

            print(
                f"[B2 UPDATE] New icon upload successful: "
                f"{b2_icon_key}"
            )

        # =================================================
        # UPDATE DATABASE OBJECT
        # =================================================

        app.version = version

        app.file_type = ".apk"

        app.file_path = b2_app_key

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

            app.category = (
                category
            )

        if changelog is not None:

            app.changelog = (
                changelog
            )

        # If no new icon was uploaded,
        # the old icon remains active.
        if b2_icon_key is not None:

            app.icon_path = (
                b2_icon_key
            )

        # =================================================
        # DATABASE COMMIT
        # =================================================

        db.commit()

        # CRITICAL:
        #
        # New B2 object is now referenced by committed DB row.
        #
        db_committed = True

        print(
            f"[APP UPDATE] DB commit successful. "
            f"App ID={app.id}"
        )

        # =================================================
        # REFRESH AFTER COMMIT
        # =================================================

        try:

            db.refresh(
                app
            )

        except Exception as refresh_error:

            print(
                f"[APP UPDATE WARNING] "
                f"DB refresh failed after commit: "
                f"{type(refresh_error).__name__}: "
                f"{refresh_error}"
            )

        # =================================================
        # DELETE OLD PACKAGE
        # =================================================
        #
        # ONLY after the new DB reference has committed.
        #
        # If deletion fails:
        #   - DB remains valid
        #   - new B2 object remains valid
        #   - old object may become orphaned
        #
        # =================================================

        if (
            old_storage_path
            and old_storage_path
            != app.file_path
        ):

            safe_delete_old_storage(
                old_storage_path,
                "package",
            )

        # =================================================
        # DELETE OLD ICON
        # =================================================

        if (
            b2_icon_key is not None
            and old_icon_path
            and old_icon_path
            != app.icon_path
        ):

            safe_delete_old_storage(
                old_icon_path,
                "icon",
            )

        # =================================================
        # TEMP LOCAL CLEANUP
        # =================================================

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

        # =================================================
        # RESPONSE
        # =================================================

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

            stored_as=get_storage_name(
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

    except HTTPException:

        # =================================================
        # BEFORE DB COMMIT
        # =================================================

        if not db_committed:

            try:

                db.rollback()

            except Exception:

                pass

            # ONLY new B2 objects are deleted.
            cleanup_new_b2_object(
                b2_app_key
            )

            cleanup_new_b2_object(
                b2_icon_key
            )

        # =================================================
        # AFTER DB COMMIT
        # =================================================

        else:

            try:

                db.rollback()

            except Exception:

                pass

            print(
                "[B2 UPDATE WARNING] "
                "DB already committed. "
                "New B2 objects preserved."
            )

        # =================================================
        # TEMP LOCAL CLEANUP
        # =================================================

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

    except Exception as exc:

        print(
            f"[APP UPDATE ERROR] "
            f"{type(exc).__name__}: {exc}"
        )

        # =================================================
        # BEFORE DB COMMIT
        # =================================================

        if not db_committed:

            try:

                db.rollback()

            except Exception:

                pass

            cleanup_new_b2_object(
                b2_app_key
            )

            cleanup_new_b2_object(
                b2_icon_key
            )

        # =================================================
        # AFTER DB COMMIT
        # =================================================

        else:

            try:

                db.rollback()

            except Exception:

                pass

            print(
                "[APP UPDATE WARNING] "
                "DB already committed. "
                "New B2 objects intentionally preserved."
            )

        # =================================================
        # TEMP LOCAL CLEANUP
        # =================================================

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

        if db_committed:

            raise HTTPException(
                status_code=500,
                detail=(
                    "App update database aur B2 mein "
                    "successfully commit ho gaya hai, "
                    "lekin final response complete nahi ho paya. "
                    "Retry karne se pehle app verify karein."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "App update process complete nahi ho paya"
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

    # =====================================================
    # AUTHORIZATION
    # =====================================================

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

    stored_file_path = (
        app.file_path
    )

    stored_icon_path = (
        app.icon_path
    )

    # =====================================================
    # DELETE DATABASE ROW
    # =====================================================

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

    # =====================================================
    # DELETE PACKAGE FROM STORAGE
    # =====================================================

    file_deleted = False

    if stored_file_path:

        file_deleted = (
            safe_delete_old_storage(
                stored_file_path,
                "package",
            )
        )

    # =====================================================
    # DELETE ICON FROM STORAGE
    # =====================================================

    icon_deleted = False

    if stored_icon_path:

        icon_deleted = (
            safe_delete_old_storage(
                stored_icon_path,
                "icon",
            )
        )

    # =====================================================
    # RESPONSE
    # =====================================================

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

    # =====================================================
    # FIND APP
    # =====================================================

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

    # =====================================================
    # CHECK PUBLISHED
    # =====================================================

    if app.status != "published":

        raise HTTPException(
            status_code=404,
            detail=(
                "Ye app marketplace me available nahi hai"
            ),
        )

    # =====================================================
    # STORAGE VARIABLES
    # =====================================================

    b2_response = None

    file_path = None

    stored_file_path = (
        str(app.file_path).strip()
        if app.file_path
        else ""
    )

    if not stored_file_path:

        raise HTTPException(
            status_code=404,
            detail=(
                "App file path database me nahi hai"
            ),
        )

    print(
        f"[DOWNLOAD] App ID={app_id}"
    )

    print(
        f"[DOWNLOAD] Stored file path="
        f"{stored_file_path}"
    )

    # =====================================================
    # B2 STORAGE
    # =====================================================

    if is_b2_object(
        stored_file_path
    ):

        print(
            f"[DOWNLOAD] Using B2 storage: "
            f"{stored_file_path}"
        )

        try:

            b2_response = (
                b2_storage.download_file(
                    stored_file_path
                )
            )

        except Exception as exc:

            print(
                f"[DOWNLOAD] B2 download failed: "
                f"{type(exc).__name__}: {exc}"
            )

            raise HTTPException(
                status_code=404,
                detail=(
                    "App file B2 storage me nahi mili"
                ),
            )

    # =====================================================
    # LEGACY LOCAL STORAGE
    # =====================================================

    else:

        print(
            "[DOWNLOAD] Using legacy local storage"
        )

        try:

            file_path = (
                ensure_safe_storage_path(
                    stored_file_path
                )
            )

        except HTTPException:

            print(
                "[DOWNLOAD] Invalid local storage path: "
                f"{stored_file_path}"
            )

            raise

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

        print(
            f"[DOWNLOAD] Local file found: "
            f"{file_path}"
        )

    # =====================================================
    # CAPTURE DOWNLOAD METADATA BEFORE DB COUNTER UPDATE
    # =====================================================
    #
    # This prevents the response metadata from depending on
    # an expired ORM object if download_count commit fails.
    #
    # =====================================================

    app_name = (
        str(app.app_name).strip()
        if app.app_name
        else "app"
    )

    version = (
        str(app.version).strip()
        if app.version
        else "1.0.0"
    )

    download_name = (
        f"{app_name}-{version}.apk"
    )

    # =====================================================
    # WINDOWS / HEADER UNSAFE CHARACTERS
    # =====================================================

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

    print(
        f"[DOWNLOAD] Download filename="
        f"{safe_download_name}"
    )

    # =====================================================
    # INCREMENT DOWNLOAD COUNT
    # =====================================================

    app.download_count = (
        (app.download_count or 0)
        + 1
    )

    try:

        db.commit()

        try:

            db.refresh(
                app
            )

        except Exception as refresh_exc:

            print(
                f"[DOWNLOAD WARNING] "
                f"Could not refresh download counter: "
                f"{type(refresh_exc).__name__}: "
                f"{refresh_exc}"
            )

    except Exception as exc:

        # The file has already been located/opened.
        # Do not break the actual download because a counter
        # update failed.
        print(
            f"[DOWNLOAD WARNING] "
            f"Could not update download_count: "
            f"{type(exc).__name__}: {exc}"
        )

        try:

            db.rollback()

        except Exception:

            pass

    # =====================================================
    # RETURN B2 FILE
    # =====================================================

    if b2_response is not None:

        headers = {

            "Content-Disposition": (
                f'attachment; '
                f'filename="{safe_download_name}"'
            )

        }

        content_length = (
            b2_response.get(
                "ContentLength"
            )
        )

        if content_length is not None:

            headers[
                "Content-Length"
            ] = str(
                content_length
            )

        return StreamingResponse(

            b2_response[
                "Body"
            ].iter_chunks(
                chunk_size=1024 * 1024
            ),

            media_type=(
                "application/vnd.android.package-archive"
            ),

            headers=headers,

        )

    # =====================================================
    # RETURN LOCAL FILE
    # =====================================================

    return FileResponse(

        path=str(
            file_path
        ),

        media_type=(
            "application/vnd.android.package-archive"
        ),

        filename=safe_download_name,

    )