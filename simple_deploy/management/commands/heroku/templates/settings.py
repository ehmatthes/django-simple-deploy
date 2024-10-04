{{current_settings}}

# Heroku settings.
import os

if "ON_HEROKU" in os.environ:
    import dj_database_url

    DEBUG = os.getenv("DEBUG") == "TRUE"
    SECRET_KEY = os.getenv("SECRET_KEY")

    ALLOWED_HOSTS.append("*")

    DATABASES = {
        "default": dj_database_url.config(
            env="DATABASE_URL",
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        ),
    }

    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATIC_URL = "/static/"
    try:
        STATICFILES_DIRS.append(os.path.join(BASE_DIR, "static"))
    except NameError:
        STATICFILES_DIRS = [os.path.join(BASE_DIR, "static"),]

    i = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(i + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

    STORAGES = {
        # Enable WhiteNoise's GZip and Brotli compression of static assets:
        # https://whitenoise.readthedocs.io/en/latest/django.html#add-compression-and-caching-support
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    # Don't store the original (un-hashed filename) version of static files, to reduce slug size:
    # https://whitenoise.readthedocs.io/en/latest/django.html#WHITENOISE_KEEP_ONLY_HASHED_FILES
    WHITENOISE_KEEP_ONLY_HASHED_FILES = True
