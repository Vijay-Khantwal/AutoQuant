from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-secret-key-change-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "channels",
    # Local apps
    "apps.signals",
    "apps.research",
    "apps.execution",
    "apps.portfolio",
    "apps.model_mgmt",
    "apps.ws",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ASGI app (Channels)
ASGI_APPLICATION = "config.asgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# â”€â”€â”€ CORS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CORS_ALLOW_ALL_ORIGINS = True  # Dev only â€“ tighten for production

# â”€â”€â”€ DRF â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# â”€â”€â”€ CHANNELS (WebSocket) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://127.0.0.1:6379")],
        },
    },
}

# â”€â”€â”€ CELERY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CELERY_BROKER_URL = config("REDIS_URL", default="redis://127.0.0.1:6379")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://127.0.0.1:6379")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'monitor-portfolio-every-1-min': {
        'task': 'apps.portfolio.tasks.monitor_positions_task',
        'schedule': crontab(minute='*/1', hour='9-15', day_of_week='mon-fri'),
    },
    'autonomous-daily-pipeline-at-310pm': {
        'task': 'apps.execution.tasks.autonomous_daily_pipeline_task',
        'schedule': crontab(minute='10', hour='15', day_of_week='mon-fri'),
    },
}
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_TASK_TRACK_STARTED = True

CELERY_TASK_ROUTES = {
    "apps.execution.tasks.autonomous_daily_pipeline_task": {"queue": "heavy_tasks"},
    "apps.model_mgmt.tasks.retrain_model_task": {"queue": "heavy_tasks"},
    "apps.research.tasks.run_research_task": {"queue": "heavy_tasks"},
    "apps.research.tasks.rerun_single_stock_task": {"queue": "heavy_tasks"},
    "apps.signals.tasks.run_prediction_task": {"queue": "heavy_tasks"},
    "apps.portfolio.tasks.monitor_positions_task": {"queue": "fast_tasks"},
    "apps.execution.tasks.run_execution_task": {"queue": "fast_tasks"},
}
# â”€â”€â”€ PROJECT-SPECIFIC PATHS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Root of the original scripts (one level up from backend/)
TRADING_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"

# â”€â”€â”€ EXTERNAL API KEYS (read from .env in project root) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import sys
from pathlib import Path as _P

# Allow .env at project root to be loaded by decouple automatically
# (decouple searches upward from CWD, but we set it explicitly too)
_env_path = _P(__file__).resolve().parent.parent.parent / ".env"

TAVILY_API_KEY    = config("TAVILY_API_KEY",    default="")
NVIDIA_API_KEY    = config("NVIDIA_API_KEY",    default="")
NIM_BASE_URL      = config("NIM_BASE_URL",      default="https://integrate.api.nvidia.com/v1")
NVIDIA_FAST_MODEL = config("WORKER_MODEL",      default="stepfun-ai/step-3.7-flash")
NVIDIA_REASONING_MODEL = config("AUDITOR_MODEL", default="nvidia/nemotron-3-super-120b-a12b")
DHAN_CLIENT_ID    = config("DHAN_CLIENT_ID",    default="")
DHAN_ACCESS_TOKEN = config("DHAN_ACCESS_TOKEN", default="")
DHAN_ENV          = config("DHAN_ENV", default="sandbox")  # "live" or "sandbox"
DHAN_BASE_URL     = "https://api.dhan.co/v2" if DHAN_ENV == "live" else "https://sandbox.dhan.co/v2"

# â”€â”€â”€ TRADING PARAMETERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PAPER_TRADE_MODE = config("PAPER_TRADE_MODE", default=True, cast=bool)
HOLD_PERIOD  = 15      # trading days (~3 calendar weeks)
TP_TARGET    = 0.03    # +3 % take-profit
SL_STOP      = -0.02   # -2 % stop-loss
CAPITAL_PER_TRADE_INR = 5_000   # â‚¹5k per position â€” paper trading phase
TOP_N_CANDIDATES = 10            # 3 focused picks per research cycle

