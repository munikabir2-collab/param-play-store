import os
import subprocess
import tempfile
from pathlib import Path

from app.core.config import (
    BUNDLETOOL_JAR,
    KEYSTORE_PATH,
    KEYSTORE_PASSWORD,
    KEY_ALIAS,
    KEY_PASSWORD,
)

aab = Path(r"app\storage\uploads\diagnostic-test.aab").resolve()
out_dir = Path(r"app\storage\uploads").resolve()
apks = out_dir / "diagnostic-test.apks"

print("AAB:", aab)
print("AAB EXISTS:", aab.exists())
print("BUNDLETOOL:", Path(BUNDLETOOL_JAR).resolve())
print("BUNDLETOOL EXISTS:", Path(BUNDLETOOL_JAR).resolve().exists())
print("KEYSTORE:", Path(KEYSTORE_PATH).resolve())
print("KEYSTORE EXISTS:", Path(KEYSTORE_PATH).resolve().exists())
print("KEY ALIAS:", KEY_ALIAS)
print("KS PASSWORD SET:", bool(KEYSTORE_PASSWORD))
print("KEY PASSWORD SET:", bool(KEY_PASSWORD))

ks_file = None
key_file = None

try:
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(KEYSTORE_PASSWORD)
        ks_file = f.name

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(KEY_PASSWORD)
        key_file = f.name

    cmd = [
        "java",
        "-jar",
        str(Path(BUNDLETOOL_JAR).resolve()),
        "build-apks",
        f"--bundle={aab}",
        f"--output={apks}",
        f"--ks={Path(KEYSTORE_PATH).resolve()}",
        f"--ks-key-alias={KEY_ALIAS}",
        f"--ks-pass=file:{ks_file}",
        f"--key-pass=file:{key_file}",
        "--mode=universal",
    ]

    print("\nRUNNING BUNDLETOOL...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
    )

    print("\nRETURN CODE:", result.returncode)

    print("\n--- STDOUT ---")
    print(result.stdout or "(empty)")

    print("\n--- STDERR ---")
    print(result.stderr or "(empty)")

    print("\nAPKS EXISTS:", apks.exists())

finally:
    for p in (ks_file, key_file):
        if p:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
