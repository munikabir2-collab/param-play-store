
import os

from dotenv import load_dotenv


# ---------------------------------------------------------
# Load .env file
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Upload configuration
# ---------------------------------------------------------

UPLOAD_DIR = os.getenv(
    "UPLOAD_DIR",
    "app/storage/uploads",
)

MAX_FILE_SIZE_MB = 200

ALLOWED_EXTENSIONS = {
    ".apk",
    ".aab",
}


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:123456@localhost:5433/nextstore",
)


# ---------------------------------------------------------
# JWT / Authentication
# ---------------------------------------------------------

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key",
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


# ---------------------------------------------------------
# Razorpay Payment Gateway
# ---------------------------------------------------------

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID",
    "",
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET",
    "",
)

RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET",
    "",
)


# ---------------------------------------------------------
# AAB / bundletool configuration
# ---------------------------------------------------------

BUNDLETOOL_JAR = os.getenv(
    "BUNDLETOOL_JAR",
    "tools/bundletool.jar",
)

KEYSTORE_PATH = os.getenv(
    "KEYSTORE_PATH",
    "tools/nextstore-upload.jks",
)

KEYSTORE_PASSWORD = os.getenv(
    "KEYSTORE_PASSWORD",
    "",
)

KEY_ALIAS = os.getenv(
    "KEY_ALIAS",
    "nextstore",
)

KEY_PASSWORD = os.getenv(
    "KEY_PASSWORD",
    "",
)


# ---------------------------------------------------------
# Create required directories
# ---------------------------------------------------------

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True,
)
