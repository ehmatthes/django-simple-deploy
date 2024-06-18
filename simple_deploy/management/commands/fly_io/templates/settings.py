{{current_settings}}

# Fly.io settings.
import os

if os.environ.get("ON_FLYIO_SETUP") or os.environ.get("ON_FLYIO"):
    # Static file configuration needs to take effect during the build process,
    #   and when deployed.
    # from https://whitenoise.evans.io/en/stable/#quickstart-for-django-apps
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATIC_URL = "/static/"
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
    i = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(i + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

if os.environ.get("ON_FLYIO"):
    # These settings need to be in place during deployment, but not during
    #   the setup process.
    # The `dj_database_url.parse()` call causes the build to fail; other settings
    #   here may not.
    import dj_database_url

    # Use secret, if set, to update DEBUG value.
    if os.environ.get("DEBUG") == "FALSE":
        DEBUG = False
    elif os.environ.get("DEBUG") == "TRUE":
        DEBUG = True

    # Set a Fly.io-specific allowed host.
    ALLOWED_HOSTS.append("{{ deployed_project_name }}.fly.dev")

    # Use the Fly.io Postgres database.
    db_url = os.environ.get("DATABASE_URL")
    DATABASES["default"] = dj_database_url.parse(db_url)

    # Prevent CSRF "Origin checking failed" issue.
    CSRF_TRUSTED_ORIGINS = ["https://{{ deployed_project_name }}.fly.dev"]
