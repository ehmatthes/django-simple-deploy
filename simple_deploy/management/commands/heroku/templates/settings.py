{{current_settings}}

# Heroku settings.
import os

if "ON_HEROKU" in os.environ:
    import dj_database_url

    DEBUG = os.getenv("DEBUG") == "TRUE"
    SECRET_KEY = os.getenv("SECRET_KEY")

    ALLOWED_HOSTS.append("*")

    DATABASES = {"default": dj_database_url.config(default="postgres://localhost")}

    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATIC_URL = "/static/"
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

    i = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(i + 1, "whitenoise.middleware.WhiteNoiseMiddleware")
