{{ current_settings }}


# --- Settings for Fly.io. ---
import os

if os.environ.get("ON_FLYIO"):
    import dj_database_url
    
    # Use secret, if set, to update DEBUG value.
    if os.environ.get("DEBUG") == "FALSE":
        DEBUG = False
    elif os.environ.get("DEBUG") == "TRUE":
        DEBUG = True

    # Set a Fly.io-specific allowed host.
    # ALLOWED_HOSTS.append('{{ deployed_project_name }}.fly.dev')
    # Using '*' while further troubleshooting CSRF issue.
    ALLOWED_HOSTS.append('{{ deployed_project_name }}.fly.dev')

    # Use the Fly.io Postgres database.
    db_url = os.environ.get("DATABASE_URL")
    DATABASES['default'] = dj_database_url.parse(db_url)

    # Prevent CSRF "Origin checking failed" issue.
    CSRF_TRUSTED_ORIGINS = ['https://{{ deployed_project_name }}.fly.dev']
