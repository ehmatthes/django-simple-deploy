{{ current_settings }}


# platform.sh settings
from platformshconfig import Config
import os

# Import some Platform.sh settings from the environment.
config = Config()
if config.is_valid_platform():

    ALLOWED_HOSTS.append('*')

    STATIC_URL = '/static/'

    if config.appDir:
        STATIC_ROOT = os.path.join(config.appDir, 'static')
    if config.projectEntropy:
        SECRET_KEY = config.projectEntropy

    if not config.in_build():
        db_settings = config.credentials('database')
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_settings['path'],
                'USER': db_settings['username'],
                'PASSWORD': db_settings['password'],
                'HOST': db_settings['host'],
                'PORT': db_settings['port'],
            },
            'sqlite': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }