{{ current_settings }}


# --- Settings for Fly.io. ---
import os, dj_database_url

if os.environ.get("ON_FLYIO"):
    ALLOWED_HOSTS.append('{{ deployed_project_name }}.fly.dev')

    db_url = os.environ.get("DATABASE_URL")
    DATABASES['default'] = dj_database_url.parse(db_url)
