{{current_settings}}

# Platform.sh settings.
import os

if os.environ.get("PLATFORM_APPLICATION_NAME"):
    # Import some Platform.sh settings from the environment.
    from platformshconfig import Config

    config = Config()

    ALLOWED_HOSTS.append("*")
    DEBUG = False

    STATIC_URL = "/static/"

    if config.appDir:
        STATIC_ROOT = os.path.join(config.appDir, "static")
    if config.projectEntropy:
        SECRET_KEY = config.projectEntropy

    if not config.in_build():
        db_settings = config.credentials("database")
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_settings["path"],
                "USER": db_settings["username"],
                "PASSWORD": db_settings["password"],
                "HOST": db_settings["host"],
                "PORT": db_settings["port"],
            },
            "sqlite": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
            },
        }
