from .base import *
from config.env import env
DEBUG = True
ENGINE = env.str('ENGINE', default='django.db.backends.postgresql')
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[""])