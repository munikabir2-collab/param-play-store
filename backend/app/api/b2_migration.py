from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_model import User
from app.models.app_model import App
from app.api.auth import get_current_user


router = APIRouter(
    prefix="/apps",
    tags=["Admin Migration"],
)


@router.post("/admin/migrate-b2-paths")
def migrate_b2_paths(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Login required hai",
        )

    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Sirf admin is migration ko perform kar sakta hai",
        )

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
                results.append({
                    "id": app_id,
                    "status": "not_found",
                })
                continue

            old_path = (
                str(app.file_path).strip()
                if app.file_path
                else ""
            )

            if old_path == new_b2_path:
                results.append({
                    "id": app_id,
                    "app_name": app.app_name,
                    "old_path": old_path,
                    "new_path": new_b2_path,
                    "status": "already_migrated",
                })
                continue

            app.file_path = new_b2_path

            results.append({
                "id": app_id,
                "app_name": app.app_name,
                "old_path": old_path,
                "new_path": new_b2_path,
                "status": "updated",
            })

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
