import os
import mysql.connector
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Railway MySQL
# ---------------------------------------------------------
# Railway provides MYSQL_PRIVATE_URL when the Flask service
# is connected to the MySQL service.
#
# Example:
# mysql://username:password@host:3306/database
# ---------------------------------------------------------

mysql_url = os.getenv("MYSQL_PRIVATE_URL")

if mysql_url:
    # Railway connection
    url = urlparse(mysql_url)

    db_config = {
        "host": url.hostname,
        "port": url.port or 3306,
        "user": url.username,
        "password": url.password,
        "database": url.path.lstrip("/"),
    }

else:
    # -----------------------------------------------------
    # Local MySQL connection
    # -----------------------------------------------------
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "campus_placement_db"),
    }


# ---------------------------------------------------------
# Create MySQL connection
# ---------------------------------------------------------

try:
    db = mysql.connector.connect(**db_config)

    cursor = db.cursor(dictionary=True)

    print("✅ MySQL connected successfully!")

except mysql.connector.Error as err:
    print(f"❌ MySQL connection error: {err}")

    db = None
    cursor = None