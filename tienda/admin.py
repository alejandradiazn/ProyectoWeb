from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Categoria, CompraPatron, DetallePedido, ImagenCarrusel, Kit,
                     MaterialPatron, Patron, Pedido, Pieza, Producto, ProgresoPatron,
                     Resena, Usuario, VarianteProducto, Vuelta)

admin.site.site_header = 'Nudito – Panel de administración'
admin.site.site_title = 'Nudito'


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'rol', 'nivel']
    list_filter = ['rol', 'nivel']
    fieldsets = UserAdmin.fieldsets + (
        ('Datos de Nudito', {'fields': ('telefono', 'direccion', 'nivel', 'rol')}),
    )


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo']
    prepopulated_fields = {'slug': ('nombre',)}


class VarianteInline(admin.TabularInline):
    model = VarianteProducto
    extra = 1


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'categoria', 'precio', 'stock', 'disponible']
    list_filter = ['tipo', 'categoria', 'disponible']
    search_fields = ['nombre']
    list_editable = ['stock', 'disponible']
    inlines = [VarianteInline]


class PiezaInline(admin.TabularInline):
    model = Pieza
    extra = 1
    show_change_link = True


class MaterialInline(admin.TabularInline):
    model = MaterialPatron
    extra = 1


@admin.register(Patron)
class PatronAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'nivel', 'categoria', 'es_gratuito', 'precio']
    list_filter = ['nivel', 'categoria', 'es_gratuito']
    search_fields = ['titulo']
    inlines = [PiezaInline, MaterialInline]


class VueltaInline(admin.TabularInline):
    model = Vuelta
    extra = 3


@admin.register(Pieza)
class PiezaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'patron', 'cantidad', 'orden']
    list_filter = ['patron']
    inlines = [VueltaInline]


@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'patron', 'precio']


class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ['variante', 'kit', 'patron', 'cantidad', 'subtotal']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha', 'estado', 'total']
    list_filter = ['estado']
    list_editable = ['estado']
    inlines = [DetalleInline]


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'producto', 'patron', 'calificacion', 'visible', 'fecha']
    list_filter = ['visible', 'calificacion']
    list_editable = ['visible']


@admin.register(ImagenCarrusel)
class ImagenCarruselAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'orden', 'activa']
    list_editable = ['orden', 'activa']


admin.site.register(CompraPatron)
admin.site.register(ProgresoPatron)
