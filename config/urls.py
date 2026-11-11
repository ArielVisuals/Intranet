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

urlpatterns = [
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
