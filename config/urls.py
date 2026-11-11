"""
URLs principales del proyecto.

Este archivo es el "enrutador raíz" de Django — equivale exactamente a
<BrowserRouter> + <Routes> en React Router. Cada ruta se delega a la app
correspondiente con `include()`, igual que anidar <Route> en React.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Ruta raíz: redirige al login (si no hay sesión) o al dashboard
    path("", lambda request: redirect("portal:dashboard" if request.user.is_authenticated else "cuentas:login")),

    # Panel de administración de Django (accesible en /admin/)
    path("admin/", admin.site.urls),

    # Autenticación: login, logout, cambio de contraseña
    path("cuentas/", include("apps.cuentas.urls")),

    # Módulo de solicitudes (vacaciones, permisos, soporte TI)
    path("solicitudes/", include("apps.solicitudes.urls")),

    # Módulo de documentos corporativos
    path("documentos/", include("apps.documentos.urls")),

    # Dashboard, avisos y directorio
    path("portal/", include("apps.portal.urls")),
]

# En desarrollo, Django sirve los archivos de media (documentos subidos).
# En producción, esto lo hace el servidor web (Nginx, Apache, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
