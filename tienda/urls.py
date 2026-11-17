from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Patrones
    path('patrones/', views.catalogo_patrones, name='catalogo_patrones'),
    path('patrones/<int:pk>/', views.detalle_patron, name='detalle_patron'),
    path('patrones/<int:pk>/adquirir/', views.adquirir_patron, name='adquirir_patron'),
    path('patrones/<int:pk>/tejer/', views.tejer_patron, name='tejer_patron'),
    path('vueltas/<int:pk>/marcar/', views.marcar_vuelta, name='marcar_vuelta'),
    path('mis-patrones/', views.mis_patrones, name='mis_patrones'),

    # Amigurumis e insumos
    path('amigurumis/', views.productos, {'tipo': 'amigurumi'}, name='amigurumis'),
    path('insumos/', views.productos, {'tipo': 'insumo'}, name='insumos'),
    path('productos/<int:pk>/', views.detalle_producto, name='detalle_producto'),

    # Reseñas
    path('resenar/<str:tipo>/<int:pk>/', views.resenar, name='resenar'),

    # Carrito y pedidos
    path('carrito/', views.ver_carrito, name='carrito'),
    path('carrito/agregar/', views.agregar_variante, name='agregar_variante'),
    path('carrito/kit/<int:pk>/', views.agregar_kit, name='agregar_kit'),
    path('carrito/patron/<int:pk>/', views.agregar_patron, name='agregar_patron'),
    path('carrito/quitar/<str:clave>/', views.quitar_del_carrito, name='quitar_del_carrito'),
    path('pedido/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),

    # Cuenta
    path('registro/', views.registro, name='registro'),
    path('ingresar/', auth_views.LoginView.as_view(), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
]
