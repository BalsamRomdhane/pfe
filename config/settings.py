"""Django settings for the Compliance Platform project.

This file is organized to support both development and production.
Environment variables are used to configure database and secret settings.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "theme",
    "apps.documents",
    "apps.standards",
    "apps.compliance",
    "apps.analytics",
    "apps.agents",
    "apps.rag",
    "apps.graph",
    "apps.orchestration",
    "apps.services",
    "apps.vector_store",
    "apps.ui",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("DJANGO_DB_NAME", "compliance_db"),
        "USER": os.environ.get("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
        "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
    }
}

# Use sqlite fallback in case PostgreSQL is not configured
if os.environ.get("DJANGO_USE_SQLITE", "False").lower() in ("1", "true", "yes"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# Vector database configuration
# Supported: "chromadb", "faiss", "qdrant"
# Default to FAISS for high-performance local vector retrieval.
VECTOR_DB = os.environ.get("VECTOR_DB", "faiss").lower()

# Embedding model configuration
# Use a strong embedding model for more reliable similarity scoring.
COMPLIANCE_EMBEDDING_MODEL = os.environ.get("COMPLIANCE_EMBEDDING_MODEL", "BAAI/bge-m3")

# Reranker model used to rank candidate evidence chunks.
COMPLIANCE_RERANKER_MODEL = os.environ.get(
    "COMPLIANCE_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# LLM model used for final compliance validation and reasoning. Choose a local model if available.
COMPLIANCE_LLM_MODEL = os.environ.get("COMPLIANCE_LLM_MODEL", "gpt2")

# Optional configuration for vector DBs
VECTOR_DB_CONFIG = {
    "chromadb": {
        "persist_directory": os.environ.get("CHROMADB_PERSIST_DIR", str(BASE_DIR / "vector_store")),
    },
    "faiss": {
        "persist_path": os.environ.get("FAISS_PERSIST_PATH", str(BASE_DIR / "vector_store" / "faiss.index")),
        # Embedding dimensionality must match the chosen embedding model.
        # Default set to 768 for BAAI/bge-base-en. Override via FAISS_DIMENSION if needed.
        "dimension": int(os.environ.get("FAISS_DIMENSION", 1024)),
    },
    "qdrant": {
        "url": os.environ.get("QDRANT_URL", "http://localhost:6333"),
        "api_key": os.environ.get("QDRANT_API_KEY", ""),
        "collection": os.environ.get("QDRANT_COLLECTION", "compliance_vectors"),
    },
}

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Ensure the static directory at the project root is served in development
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# REST framework default settings
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
