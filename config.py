import os
import mysql.connector
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

# Railway can provide a MySQL connection URL.
# We check multiple possible Railway variable names.
mysql_url = (
    os.getenv("MYSQL_PRIVATE_URL")
    or os.getenv("MYSQL_URL")
    or os.getenv("DATABASE_URL")
)


if mysql_url:
    # =====================================================
    # RAILWAY MYSQL URL CONNECTION
    # =====================================================

    url = urlparse(mysql_url)

    db_config = {
        "host": url.hostname,
        "port": url.port or 3306,
        "user": unquote(url.username) if url.username else "",
        "password": unquote(url.password) if url.password else "",
        "database": url.path.lstrip("/") if url.path else "",
    }

    print("🚂 Using Railway MySQL connection")
    print(f"📡 MySQL Host: {db_config['host']}")
    print(f"🔌 MySQL Port: {db_config['port']}")
    print(f"🗄️ Database: {db_config['database']}")

else:
    # =====================================================
    # RAILWAY INDIVIDUAL MYSQL VARIABLES
    # =====================================================

    railway_host = os.getenv("MYSQLHOST")
    railway_port = os.getenv("MYSQLPORT")
    railway_user = os.getenv("MYSQLUSER")
    railway_password = os.getenv("MYSQLPASSWORD")
    railway_database = os.getenv("MYSQLDATABASE")

    if railway_host:
        db_config = {
            "host": railway_host,
            "port": int(railway_port or 3306),
            "user": railway_user,
            "password": railway_password,
            "database": railway_database,
        }

        print("🚂 Using Railway MySQL variables")
        print(f"📡 MySQL Host: {db_config['host']}")
        print(f"🔌 MySQL Port: {db_config['port']}")
        print(f"🗄️ Database: {db_config['database']}")

    else:
        # =================================================
        # LOCAL MYSQL
        # =================================================

        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv(
                "DB_NAME",
                "campus_placement_db"
            ),
        }

        print("💻 Using local MySQL")
        print(f"📡 MySQL Host: {db_config['host']}")
        print(f"🔌 MySQL Port: {db_config['port']}")
        print(f"🗄️ Database: {db_config['database']}")


# =========================================================
# CREATE MYSQL CONNECTION
# =========================================================

try:

    db = mysql.connector.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        connection_timeout=10
    )

    cursor = db.cursor(dictionary=True)

    print("✅ MySQL connected successfully!")

except mysql.connector.Error as err:

    print(f"❌ MySQL connection error: {err}")

    db = None
    cursor = None