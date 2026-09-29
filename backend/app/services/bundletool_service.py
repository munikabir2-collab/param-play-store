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
    """Jab bundletool .aab ko installable .apk me convert nahi kar paata."""


def convert_aab_to_apk(aab_path: str) -> str:
    """
    Google ke bundletool CLI se ek .aab file ko sabhi devices par chalne wala
    signed 'universal' .apk me convert karta hai.

    Returns: generated .apk ka file path (UPLOAD_DIR ke andar).
    Raises: ConversionError agar setup missing ho ya conversion fail ho.
    """
    if not os.path.exists(BUNDLETOOL_JAR):
        raise ConversionError(
            f"bundletool.jar nahi mila: '{BUNDLETOOL_JAR}'. "
            "Download karo: https://github.com/google/bundletool/releases "
            "aur .env me BUNDLETOOL_JAR path set karo."
        )
    if not os.path.exists(KEYSTORE_PATH):
        raise ConversionError(
            f"Signing keystore nahi mila: '{KEYSTORE_PATH}'. Pehle keytool se ek "
            "keystore banao (README dekho) aur .env me KEYSTORE_PATH set karo."
        )

    apks_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.apks")

    cmd = [
        "java", "-jar", BUNDLETOOL_JAR,
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise ConversionError(
            "Java nahi mila. Server par JRE/JDK install karo (bundletool Java pe chalta hai)."
        )
    except subprocess.TimeoutExpired:
        raise ConversionError("bundletool 120 second me complete nahi hua (timeout).")

    if result.returncode != 0:
        raise ConversionError(f"bundletool fail ho gaya: {result.stderr.strip()}")

    if not os.path.exists(apks_path):
        raise ConversionError("bundletool chala lekin output file nahi mili.")

    # .apks asal me ek zip file hai — usme se universal.apk nikalo
    apk_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.apk")
    try:
        with zipfile.ZipFile(apks_path, "r") as z:
            with z.open("universal.apk") as src, open(apk_path, "wb") as dst:
                dst.write(src.read())
    finally:
        if os.path.exists(apks_path):
            os.remove(apks_path)  # intermediate .apks file ab nahi chahiye

    return apk_path
