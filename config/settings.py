"""
Configuración global del proyecto Portal Universidad.

En Django, settings.py es el equivalente a un archivo de configuración de
entorno en Node.js (como .env + config.js juntos). Aquí Django lee todas las
opciones que definen cómo funciona el proyecto.

Usamos python-dotenv para leer variables del archivo .env, así nunca
exponemos secretos en el código fuente (igual que process.env en Node.js).
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env al entorno del proceso.
# Debe llamarse antes de leer cualquier os.environ.
load_dotenv()

# BASE_DIR apunta a la raíz del proyecto (donde está manage.py).
# Path(__file__) es la ruta de este archivo (settings.py).
# .resolve().parent.parent sube dos niveles hasta la raíz.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SEGURIDAD
# =============================================================================

# La SECRET_KEY firma cookies, tokens CSRF y sesiones.
# NUNCA debe estar en el código fuente — siempre en la variable de entorno.
SECRET_KEY = os.environ.get("SECRET_KEY")

# DEBUG=True muestra errores detallados en pantalla. SIEMPRE False en producción.
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Lista de dominios que pueden servir esta app.
# En desarrollo (DEBUG=True) permitimos localhost, 127.0.0.1 y testserver.
ALLOWED_HOSTS_ENV = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(",") if h.strip()]
if DEBUG and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(["localhost", "127.0.0.1", "testserver"])


# =============================================================================
# APLICACIONES INSTALADAS
# =============================================================================
# Equivale a registrar módulos. Django necesita saber qué apps existen para
# incluirlas en las migraciones, URLs y el panel de administración.

INSTALLED_APPS = [
    # Apps de Django (el núcleo del framework)
    "django.contrib.admin",        # Panel de administración automático
    "django.contrib.auth",         # Sistema de autenticación (usuarios, contraseñas, grupos)
    "django.contrib.contenttypes", # Permite relaciones genéricas entre modelos
    "django.contrib.sessions",     # Manejo de sesiones de usuario
    "django.contrib.messages",     # Sistema de mensajes flash (éxito, error, etc.)
    "django.contrib.staticfiles",  # Sirve archivos CSS/JS/imágenes

    # Apps de terceros
    "whitenoise",  # Sirve archivos estáticos en producción sin Nginx

    # Nuestras apps (en la carpeta apps/)
    "apps.cuentas",      # Autenticación, perfiles y áreas
    "apps.solicitudes",  # Flujo de solicitudes (permisos, vacaciones, soporte)
    "apps.documentos",   # Gestión de documentos corporativos
    "apps.portal",       # Dashboard, avisos y directorio
]


# =============================================================================
# MIDDLEWARE
# =============================================================================
# El middleware son capas que procesan cada request/response ANTES y DESPUÉS
# de que llegue a una vista. Es como los "interceptors" de Axios en React.

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise debe ir justo después de SecurityMiddleware para servir estáticos
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # CsrfViewMiddleware agrega protección CSRF automáticamente en todos los formularios.
    # Es el equivalente a incluir un token anti-CSRF en cada <form>.
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =============================================================================
# URLS
# =============================================================================

# Punto de entrada principal de las rutas. Es como el App.jsx con React Router.
ROOT_URLCONF = "config.urls"


# =============================================================================
# PLANTILLAS (TEMPLATES)
# =============================================================================
# Django usa su propio motor de plantillas HTML. Es similar a JSX pero se
# procesa en el servidor y el usuario solo recibe HTML estático.

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Busca plantillas en la carpeta "templates/" de la raíz del proyecto
        "DIRS": [BASE_DIR / "templates"],
        # También busca plantillas dentro de cada app (en subcarpeta templates/)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                # Permite acceder a request.user en cualquier plantilla
                "django.contrib.auth.context_processors.auth",
                # Permite mostrar mensajes flash (éxito, error) en cualquier plantilla
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# =============================================================================
# BASE DE DATOS
# =============================================================================
# SQLite para desarrollo: archivo local, cero configuración.
# Para producción, cambiar DB_ENGINE en .env a postgresql o mysql.

DB_ENGINE = os.environ.get("DB_ENGINE", "django.db.backends.sqlite3")

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Configuración para PostgreSQL o MySQL en producción.
    # Solo se activa si DB_ENGINE está definido en .env
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", "intranet_db"),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }


# =============================================================================
# VALIDADORES DE CONTRASEÑA
# =============================================================================
# Django valida las contraseñas automáticamente al crear usuarios.

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =============================================================================
# INTERNACIONALIZACIÓN
# =============================================================================

LANGUAGE_CODE = "es-mx"       # Idioma español (México) para fechas, errores, admin
TIME_ZONE = "America/Mexico_City"
USE_I18N = True               # Habilita traducción de textos de Django
USE_TZ = True                 # Almacena fechas en UTC, convierte a zona local al mostrar


# =============================================================================
# ARCHIVOS ESTÁTICOS (CSS, JS, imágenes del proyecto)
# =============================================================================
# "Estáticos" = archivos que no cambian según el usuario (tu CSS, JS, logos).
# Equivale a la carpeta public/ de un proyecto React.

STATIC_URL = "/static/"
# Carpeta donde Django busca archivos estáticos del PROYECTO (no de las apps)
STATICFILES_DIRS = [BASE_DIR / "static"]
# Carpeta donde "collectstatic" junta todos los estáticos para producción
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: comprime y cachea los estáticos en producción
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =============================================================================
# ARCHIVOS DE MEDIOS (subidos por usuarios)
# =============================================================================
# "Media" = archivos que suben los usuarios (documentos, fotos de perfil, etc.)
# Equivale al almacenamiento de archivos en servicios como S3 o Firebase Storage.

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

# Redirige al login cuando se intenta acceder a una página protegida.
# Es el equivalente a un "auth guard" en React Router.
LOGIN_URL = "/cuentas/login/"

# Después de hacer login, redirige al dashboard principal.
LOGIN_REDIRECT_URL = "/portal/dashboard/"

# Después de hacer logout, redirige al login.
LOGOUT_REDIRECT_URL = "/cuentas/login/"


# =============================================================================
# TAMAÑO MÁXIMO DE ARCHIVOS SUBIDOS
# =============================================================================

# Límite de 10 MB para archivos subidos (documentos corporativos).
# Django rechaza automáticamente cualquier archivo más grande.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB en bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024    # 10 MB en bytes


# =============================================================================
# CLAVE PRIMARIA POR DEFECTO
# =============================================================================

# BigAutoField usa enteros de 64 bits para IDs. Es la mejor práctica
# para sistemas que pueden crecer (evita quedarse sin IDs con AutoField de 32 bits).
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Permite tu dominio de Vercel y localhost
ALLOWED_HOSTS = ['.vercel.app', 'localhost', '127.0.0.1']

# Si tu aplicación usa formularios, login o botones que envíen datos (POST):
CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']