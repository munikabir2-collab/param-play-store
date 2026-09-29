
import os
import subprocess
import uuid
import zipfile
from pathlib import Path

from app.core.config import (
    BUNDLETOOL_JAR,
    KEYSTORE_PATH,
    KEYSTORE_PASSWORD,
    KEY_ALIAS,
    KEY_PASSWORD,
    UPLOAD_DIR,
)


class ConversionError(Exception):
    """AAB ko installable APK me convert karne me error."""


# =========================================================
# SECURITY LIMITS
# =========================================================

CONVERSION_TIMEOUT_SECONDS = 120

MAX_APKS_ENTRIES = 10000
MAX_GENERATED_APK_SIZE = 200 * 1024 * 1024


# =========================================================
# PATH SECURITY
# =========================================================

def get_upload_root() -> Path:

    return Path(
        UPLOAD_DIR
    ).resolve()


def ensure_upload_path(
    file_path: str | Path,
) -> Path:

    root = get_upload_root()

    candidate = Path(
        file_path
    ).resolve()

    try:

        candidate.relative_to(root)

    except ValueError:

        raise ConversionError(
            "Generated file path invalid hai."
        )

    return candidate


def safe_remove(
    file_path: str | Path | None,
) -> None:

    if not file_path:
        return

    try:

        path = ensure_upload_path(
            file_path
        )

    except ConversionError:
        return

    try:

        if path.exists() and path.is_file():
            path.unlink()

    except OSError:
        pass


# =========================================================
# AAB -> APK
# =========================================================

def convert_aab_to_apk(
    aab_path: str,
) -> str:
    """
    bundletool ke through AAB ko universal installable APK
    me convert karta hai.

    Returns:
        Generated APK ka path.

    Raises:
        ConversionError:
            Agar conversion fail ho.
    """

    upload_root = get_upload_root()

    upload_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        safe_aab_path = ensure_upload_path(
            aab_path
        )

    except ConversionError:

        raise

    if not safe_aab_path.exists():

        raise ConversionError(
            "AAB input file nahi mili."
        )

    if not safe_aab_path.is_file():

        raise ConversionError(
            "AAB input path valid file nahi hai."
        )

    bundletool_path = Path(
        BUNDLETOOL_JAR
    ).resolve()

    keystore_path = Path(
        KEYSTORE_PATH
    ).resolve()

    if not bundletool_path.exists():

        raise ConversionError(
            "Bundletool configured nahi hai."
        )

    if not bundletool_path.is_file():

        raise ConversionError(
            "Bundletool file invalid hai."
        )

    if not keystore_path.exists():

        raise ConversionError(
            "Signing configuration available nahi hai."
        )

    if not keystore_path.is_file():

        raise ConversionError(
            "Signing configuration invalid hai."
        )

    if not KEYSTORE_PASSWORD:

        raise ConversionError(
            "Signing password configured nahi hai."
        )

    if not KEY_PASSWORD:

        raise ConversionError(
            "Signing key password configured nahi hai."
        )

    apks_path = (
        upload_root
        / f"{uuid.uuid4().hex}.apks"
    )

    apk_path = (
        upload_root
        / f"{uuid.uuid4().hex}.apk"
    )

    # -----------------------------------------------------
    # bundletool command
    # -----------------------------------------------------

    cmd = [
        "java",
        "-jar",
        str(bundletool_path),
        "build-apks",
        f"--bundle={safe_aab_path}",
        f"--output={apks_path}",
        "--mode=universal",
        f"--ks={keystore_path}",
        f"--ks-pass=pass:{KEYSTORE_PASSWORD}",
        f"--ks-key-alias={KEY_ALIAS}",
        f"--key-pass=pass:{KEY_PASSWORD}",
        "--overwrite",
    ]

    try:

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT_SECONDS,
            check=False,
        )

    except FileNotFoundError:

        safe_remove(
            apks_path
        )

        safe_remove(
            apk_path
        )

        raise ConversionError(
            "Java runtime available nahi hai."
        )

    except subprocess.TimeoutExpired:

        safe_remove(
            apks_path
        )

        safe_remove(
            apk_path
        )

        raise ConversionError(
            "AAB conversion timeout ho gaya."
        )

    except OSError:

        safe_remove(
            apks_path
        )

        safe_remove(
            apk_path
        )

        raise ConversionError(
            "AAB conversion process start nahi ho saka."
        )

    if result.returncode != 0:

        safe_remove(
            apks_path
        )

        safe_remove(
            apk_path
        )

        # IMPORTANT:
        # result.stderr/stdout intentionally client
        # ko expose nahi kiya ja raha.
        raise ConversionError(
            "bundletool conversion fail ho gaya."
        )

    if not apks_path.exists():

        raise ConversionError(
            "bundletool output generate nahi hua."
        )

    # -----------------------------------------------------
    # Validate .apks archive
    # -----------------------------------------------------

    try:

        with zipfile.ZipFile(
            apks_path,
            "r",
        ) as archive:

            if archive.testzip() is not None:

                raise ConversionError(
                    "bundletool output corrupted hai."
                )

            infos = archive.infolist()

            if not infos:

                raise ConversionError(
                    "bundletool output empty hai."
                )

            if len(infos) > MAX_APKS_ENTRIES:

                raise ConversionError(
                    "bundletool output invalid hai."
                )

            names = {
                info.filename
                for info in infos
            }

            if "universal.apk" not in names:

                raise ConversionError(
                    "Universal APK output nahi mila."
                )

            universal_info = None

            for info in infos:

                if info.filename == "universal.apk":

                    universal_info = info
                    break

            if universal_info is None:

                raise ConversionError(
                    "Universal APK metadata missing hai."
                )

            if (
                universal_info.file_size
                <= 0
            ):

                raise ConversionError(
                    "Generated universal APK empty hai."
                )

            if (
                universal_info.file_size
                > MAX_GENERATED_APK_SIZE
            ):

                raise ConversionError(
                    "Generated APK allowed size se bada hai."
                )

            # -------------------------------------------------
            # Extract universal.apk manually in chunks.
            # extractall() intentionally use nahi kiya.
            # -------------------------------------------------

            with archive.open(
                universal_info,
                "r",
            ) as source:

                with open(
                    apk_path,
                    "wb",
                ) as destination:

                    total_written = 0

                    while True:

                        chunk = source.read(
                            1024 * 1024
                        )

                        if not chunk:
                            break

                        total_written += len(
                            chunk
                        )

                        if (
                            total_written
                            > MAX_GENERATED_APK_SIZE
                        ):

                            raise ConversionError(
                                "Generated APK allowed size se bada hai."
                            )

                        destination.write(
                            chunk
                        )

    except zipfile.BadZipFile:

        raise ConversionError(
            "bundletool output valid archive nahi hai."
        )

    finally:

        safe_remove(
            apks_path
        )

    if not apk_path.exists():

        raise ConversionError(
            "Universal APK generate nahi hua."
        )

    if not apk_path.is_file():

        safe_remove(
            apk_path
        )

        raise ConversionError(
            "Generated APK invalid hai."
        )

    if apk_path.stat().st_size <= 0:

        safe_remove(
            apk_path
        )

        raise ConversionError(
            "Generated APK empty hai."
        )

    try:

        return str(
            ensure_upload_path(
                apk_path
            )
        )

    except ConversionError:

        safe_remove(
            apk_path
        )

        raise

