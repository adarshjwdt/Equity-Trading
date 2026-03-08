import os
import dj_database_url
from urllib.parse import quote
from pathlib import Path

# 1. Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Security Settings
SECRET_KEY = 'django-insecure-your-custom-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = ['*']

# 3. Application Definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Your Portfolio App
    'services',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 4. Routing and WSGI
ROOT_URLCONF = 'TradeGrid.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'TradeGrid.wsgi.application'

# 5. Database Configuration (Supabase Transaction Pooler)
# ---------------------------------------------------------
# We use the Pooler (Port 6543) to bypass IPv6 DNS issues on local machines.
# 5. Database Configuration (Fixed for Psycopg2 Compatibility)
# ---------------------------------------------------------
DB_USER = "postgres.jcysytnfrhokyypqhgbh"
DB_PASS = "jgsuper%^430"
DB_HOST = "aws-1-ap-southeast-1.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"

# Encode password to handle special characters
encoded_pass = quote(DB_PASS)

# REMOVED "?pgbouncer=true" to fix the "invalid dsn" error.
# We keep "sslmode=require" as Supabase requires encrypted connections.
SUPABASE_URL = f"postgresql://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

DATABASES = {
    'default': dj_database_url.config(
        default=SUPABASE_URL,
        conn_max_age=0,  # Mandatory for transaction poolers to prevent stale connections
    )
}

# This is the "manual" way to handle PgBouncer/Supavisor logic in Django:
DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
# ---------------------------------------------------------

# 6. Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

# 7. Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# 8. Static Files Configuration
# ---------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Create the directory if it doesn't exist to prevent the "Directory does not exist" warning
STATIC_DIR = os.path.join(BASE_DIR, 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

STATICFILES_DIRS = [STATIC_DIR]
# ---------------------------------------------------------

# 9. Custom App Paths
GSPREAD_JSON = os.path.join(BASE_DIR, 'credentials', 'service_account.json')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'