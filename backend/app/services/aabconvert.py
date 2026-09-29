
import os
import subprocess
import uuid
import zipfile

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


def convert_aab_to_apk(
    aab_path: str,
) -> str:
    """
    bundletool ke through AAB ko universal installable APK me convert karta hai.

    Returns:
        Generated APK ka path.

    Raises:
        ConversionError:
            Agar bundletool, Java, keystore ya conversion me problem aaye.
    """

    if not os.path.exists(aab_path):
        raise ConversionError(
            f"AAB file nahi mili: {aab_path}"
        )

    if not os.path.exists(BUNDLETOOL_JAR):
        raise ConversionError(
            f"bundletool.jar nahi mila: {BUNDLETOOL_JAR}"
        )

    if not os.path.exists(KEYSTORE_PATH):
        raise ConversionError(
            f"Signing keystore nahi mila: {KEYSTORE_PATH}"
        )

    if not KEYSTORE_PASSWORD:
        raise ConversionError(
            "KEYSTORE_PASSWORD configured nahi hai."
        )

    if not KEY_PASSWORD:
        raise ConversionError(
            "KEY_PASSWORD configured nahi hai."
        )

    apks_path = os.path.join(
        UPLOAD_DIR,
        f"{uuid.uuid4()}.apks",
    )

    apk_path = os.path.join(
        UPLOAD_DIR,
        f"{uuid.uuid4()}.apk",
    )

    cmd = [
        "java",
        "-jar",
        BUNDLETOOL_JAR,
        "build-apks",
        f"--bundle={aab_path}",
        f"--output={apks_path}",
        "--mode=universal",
        f"--ks={KEYSTORE_PATH}",
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
            timeout=120,
        )

    except FileNotFoundError:
        raise ConversionError(
            "Java nahi mila. Java/JDK install hona chahiye."
        )

    except subprocess.TimeoutExpired:
        raise ConversionError(
            "bundletool 120 seconds ke andar complete nahi hua."
        )

    if result.returncode != 0:
        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown bundletool error"
        )

        raise ConversionError(
            f"bundletool conversion fail: {error_message}"
        )

    if not os.path.exists(apks_path):
        raise ConversionError(
            "bundletool successful dikha raha hai, "
            "lekin .apks output nahi mila."
        )

    try:
        with zipfile.ZipFile(
            apks_path,
            "r",
        ) as archive:

            if "universal.apk" not in archive.namelist():
                raise ConversionError(
                    "bundletool output me universal.apk nahi mila."
                )

            with archive.open(
                "universal.apk"
            ) as source:

                with open(
                    apk_path,
                    "wb",
                ) as destination:

                    while True:
                        chunk = source.read(
                            1024 * 1024
                        )

                        if not chunk:
                            break

                        destination.write(chunk)

    except zipfile.BadZipFile:
        raise ConversionError(
            "bundletool ne invalid .apks file banayi."
        )

    finally:
        if os.path.exists(apks_path):
            try:
                os.remove(apks_path)
            except OSError:
                pass

    if not os.path.exists(apk_path):
        raise ConversionError(
            "universal APK generate nahi hua."
        )

    return apk_path

