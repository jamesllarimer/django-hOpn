from .base import *
from config.env import env
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ENGINE = env.str('ENGINE', default='django.db.backends.postgresql_psycopg2')
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[""])
