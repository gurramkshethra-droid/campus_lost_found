import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_this_secret')

    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB')

    # ✅ Decide database safely
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    elif MYSQL_USER and MYSQL_DB:
        try:
            user = quote_plus(MYSQL_USER)
            password = quote_plus(MYSQL_PASSWORD or "")

            SQLALCHEMY_DATABASE_URI = (
                f"mysql+pymysql://{user}:{password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
            )

            print("✅ Using MySQL Database")

        except Exception as e:
            print("⚠️ MySQL failed, switching to SQLite:", e)
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "campus_lost_found.db")

    else:
        print("✅ Using SQLite Database")
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "campus_lost_found.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    REMEMBER_COOKIE_DURATION = timedelta(days=7)