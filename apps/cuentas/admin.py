"""
Configuración del panel de administración de Django para la app 'cuentas'.

El admin de Django es como un CRUD automático generado a partir de los modelos.
Es una herramienta increíblemente poderosa: sin escribir prácticamente nada,
tienes una interfaz para gestionar todos los datos de la aplicación.

Aquí configuramos:
1. Títulos del panel en español
2. Cómo se muestran Área y PerfilUsuario en el admin
3. PerfilUsuario como "inline" dentro del User admin
   (editar perfil directamente desde la página del usuario)
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from .models import Area, PerfilUsuario


# =============================================================================
# PERSONALIZACIÓN DEL PANEL DE ADMINISTRACIÓN
# =============================================================================

# Estos tres atributos cambian los textos que Django muestra en el admin.
admin.site.site_title = "Portal Universidad · Admin"
admin.site.site_header = "Portal Universidad — Administración"
admin.site.index_title = "Panel de control"


# =============================================================================
# ADMIN DE ÁREA
# =============================================================================

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    """
    @admin.register(Area) es un decorador que registra la clase AreaAdmin
    como el configurador de la vista admin para el modelo Area.
    Equivale a: admin.site.register(Area, AreaAdmin)
    """

    # Columnas que se muestran en la lista de áreas
    list_display = ["nombre", "jefe", "total_empleados", "creado_en"]

    # Campos por los que se puede buscar (barra de búsqueda)
    search_fields = ["nombre", "descripcion", "jefe__first_name", "jefe__last_name"]

    # Filtros en el panel lateral derecho
    list_filter = ["creado_en"]

    # Campos que se pueden editar directamente en la lista (sin abrir el detalle)
    list_editable = []

    # Orden de los campos en el formulario de edición
    fieldsets = [
        (None, {
            "fields": ["nombre", "descripcion", "jefe"],
        }),
    ]

    def total_empleados(self, obj):
        """
        Columna calculada: cuenta los empleados del área.
        'obj' es la instancia del modelo Area que se está mostrando.
        """
        return obj.empleados.count()
    total_empleados.short_description = "Empleados"


# =============================================================================
# PERFIL INLINE EN EL ADMIN DE USUARIO
# =============================================================================

class PerfilUsuarioInline(admin.StackedInline):
    """
    StackedInline muestra el PerfilUsuario directamente dentro del formulario
    del User, como si fuera parte del mismo objeto. Es la UX más limpia para
    la relación OneToOne.

    Alternativa: TabularInline lo muestra en formato de tabla (más compacto
    pero menos legible con muchos campos).
    """

    model = PerfilUsuario
    # can_delete=False porque no queremos que el admin elimine el perfil
    # sin eliminar también el usuario
    can_delete = False
    verbose_name_plural = "Perfil y datos corporativos"
    fieldsets = [
        ("Información corporativa", {
            "fields": ["area", "puesto", "fecha_ingreso", "telefono"],
        }),
    ]


class UserAdmin(DjangoUserAdmin):
    """
    Reemplaza el UserAdmin de Django con nuestra versión que incluye
    el PerfilUsuario como inline.

    Extendemos DjangoUserAdmin para conservar TODA la funcionalidad
    del admin de usuario (formulario de contraseña, permisos, grupos, etc.)
    y solo añadimos nuestro inline.
    """

    inlines = [PerfilUsuarioInline]

    # Columnas adicionales en la lista de usuarios
    list_display = [
        "username", "get_nombre_completo", "email",
        "get_area", "get_rol", "is_active", "date_joined",
    ]
    list_filter = ["is_active", "groups", "perfil__area"]
    search_fields = ["username", "first_name", "last_name", "email"]

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or "—"
    get_nombre_completo.short_description = "Nombre completo"
    get_nombre_completo.admin_order_field = "first_name"

    def get_area(self, obj):
        """Muestra el área del usuario accediendo al perfil relacionado."""
        try:
            return obj.perfil.area or "—"
        except PerfilUsuario.DoesNotExist:
            return "Sin perfil"
    get_area.short_description = "Área"

    def get_rol(self, obj):
        """Muestra los grupos del usuario (sus roles)."""
        grupos = obj.groups.values_list("name", flat=True)
        return ", ".join(grupos) if grupos else "Sin rol"
    get_rol.short_description = "Rol"


# Desregistrar el UserAdmin por defecto y registrar el nuestro.
# Esto es necesario porque Django ya registra User con su propio admin.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
