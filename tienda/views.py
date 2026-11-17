"""Vistas de Nudito (arquitectura MPA: cada vista devuelve una página HTML
completa, salvo marcar_vuelta, que responde JSON a una petición Fetch)."""
import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .carrito import Carrito
from .forms import PerfilForm, RegistroForm, ResenaForm
from .models import (Categoria, CompraPatron, DetallePedido, ImagenCarrusel, Kit, NIVELES,
                     Patron, Pedido, Producto, ProgresoPatron, VarianteProducto, Vuelta)


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
def home(request):
    contexto = {
        'carrusel': ImagenCarrusel.objects.filter(activa=True),
        'categorias': Categoria.objects.filter(tipo='amigurumi'),
        'patrones': Patron.objects.all()[:4],
        'amigurumis': Producto.objects.filter(tipo='amigurumi', disponible=True)[:8],
        'insumos': Producto.objects.filter(tipo='insumo', disponible=True).prefetch_related('variantes')[:3],
    }
    return render(request, 'tienda/home.html', contexto)


# ---------------------------------------------------------------------------
# Patrones
# ---------------------------------------------------------------------------
def catalogo_patrones(request):
    patrones = Patron.objects.select_related('categoria').annotate(promedio=Avg('resenas__calificacion'))

    q = request.GET.get('q', '').strip()
    niveles = request.GET.getlist('nivel')
    categorias = request.GET.getlist('categoria')
    precio = request.GET.get('precio', '')
    orden = request.GET.get('orden', 'recientes')

    if q:                                   # búsqueda por nombre
        patrones = patrones.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
    if niveles:                             # filtro por nivel
        patrones = patrones.filter(nivel__in=niveles)
    if categorias:                          # filtro por tipo de amigurumi
        patrones = patrones.filter(categoria__slug__in=categorias)
    if precio == 'gratis':
        patrones = patrones.filter(es_gratuito=True)
    elif precio == 'pago':
        patrones = patrones.filter(es_gratuito=False)

    if orden == 'valorados':
        patrones = patrones.order_by('-promedio')
    elif orden == 'precio':
        patrones = patrones.order_by('precio')

    contexto = {
        'patrones': patrones,
        'niveles': NIVELES,
        'categorias': Categoria.objects.filter(tipo='amigurumi'),
        'filtro': {'q': q, 'niveles': niveles, 'categorias': categorias, 'precio': precio, 'orden': orden},
    }
    return render(request, 'tienda/catalogo_patrones.html', contexto)


def detalle_patron(request, pk):
    patron = get_object_or_404(Patron, pk=pk)
    acceso = patron.usuario_tiene_acceso(request.user)
    piezas = patron.piezas.prefetch_related('vueltas')
    if acceso:
        vista_previa = None
    else:
        primera = piezas.first()
        vista_previa = {'pieza': primera, 'vueltas': primera.vueltas.all()[:3]} if primera else None

    guardado = request.user.is_authenticated and patron.compras.filter(usuario=request.user).exists()
    pago_pendiente = request.user.is_authenticated and not guardado and DetallePedido.objects.filter(
        pedido__usuario=request.user, pedido__estado='pendiente', patron=patron).exists()
    contexto = {
        'patron': patron,
        'acceso': acceso,
        'guardado': guardado,
        'pago_pendiente': pago_pendiente,
        'piezas': piezas,
        'vista_previa': vista_previa,
        'materiales': patron.materiales.select_related('producto'),
        'kit': getattr(patron, 'kit', None),
        'resenas': patron.resenas.filter(visible=True).select_related('usuario'),
        'puede_resenar': guardado,
        'form_resena': ResenaForm(),
    }
    return render(request, 'tienda/detalle_patron.html', contexto)


@login_required
@require_POST
def adquirir_patron(request, pk):
    """Guarda un patrón gratuito en Mis patrones. Los de pago se compran por el carrito."""
    patron = get_object_or_404(Patron, pk=pk)
    if not patron.es_gratuito:
        return redirect('detalle_patron', pk=pk)
    CompraPatron.objects.get_or_create(usuario=request.user, patron=patron)
    messages.success(request, f'¡"{patron.titulo}" ya está en Mis patrones!')
    return redirect('tejer_patron', pk=pk)


@login_required
def mis_patrones(request):
    compras = request.user.patrones_comprados.select_related('patron')
    lista = []
    for compra in compras:
        progreso = ProgresoPatron.objects.filter(usuario=request.user, patron=compra.patron).first()
        lista.append({'patron': compra.patron, 'porcentaje': progreso.porcentaje() if progreso else 0})
    return render(request, 'tienda/mis_patrones.html', {'lista': lista})


@login_required
def tejer_patron(request, pk):
    patron = get_object_or_404(Patron, pk=pk)
    if not patron.compras.filter(usuario=request.user).exists():
        messages.info(request, 'Primero agrega este patrón a Mis patrones.')
        return redirect('detalle_patron', pk=pk)

    progreso, _ = ProgresoPatron.objects.get_or_create(usuario=request.user, patron=patron)
    hechas = set(progreso.vueltas_completadas.values_list('id', flat=True))

    piezas = []
    for pieza in patron.piezas.prefetch_related('vueltas'):
        vueltas = list(pieza.vueltas.all())
        listas = sum(1 for v in vueltas if v.id in hechas)
        piezas.append({'pieza': pieza, 'vueltas': vueltas, 'hechas': listas,
                       'total': len(vueltas), 'completa': vueltas and listas == len(vueltas)})

    # Pieza que se muestra: la elegida o la primera sin terminar
    pieza_id = request.GET.get('pieza')
    actual = next((p for p in piezas if str(p['pieza'].id) == pieza_id), None)
    if actual is None:
        actual = next((p for p in piezas if not p['completa']), piezas[0] if piezas else None)
    siguiente = None
    if actual:
        siguiente = next((v for v in actual['vueltas'] if v.id not in hechas), None)

    contexto = {
        'patron': patron, 'piezas': piezas, 'actual': actual, 'hechas': hechas,
        'siguiente': siguiente, 'porcentaje': progreso.porcentaje(),
        'total_hechas': len(hechas), 'total_vueltas': patron.total_vueltas(),
    }
    return render(request, 'tienda/tejer_patron.html', contexto)


@login_required
@require_POST
def marcar_vuelta(request, pk):
    """Recibe una petición Fetch y guarda el progreso sin recargar la página."""
    vuelta = get_object_or_404(Vuelta, pk=pk)
    patron = vuelta.pieza.patron
    if not patron.compras.filter(usuario=request.user).exists():
        return JsonResponse({'error': 'Sin acceso al patrón'}, status=403)

    progreso, _ = ProgresoPatron.objects.get_or_create(usuario=request.user, patron=patron)
    datos = json.loads(request.body or '{}')
    if datos.get('completada', True):
        progreso.vueltas_completadas.add(vuelta)
    else:
        progreso.vueltas_completadas.remove(vuelta)
    progreso.save()  # actualiza la fecha del último avance

    hechas_pieza = progreso.vueltas_completadas.filter(pieza=vuelta.pieza).count()
    return JsonResponse({
        'porcentaje': progreso.porcentaje(),
        'total_hechas': progreso.vueltas_completadas.count(),
        'hechas_pieza': hechas_pieza,
        'total_pieza': vuelta.pieza.vueltas.count(),
    })


# ---------------------------------------------------------------------------
# Productos (amigurumis e insumos)
# ---------------------------------------------------------------------------
def productos(request, tipo):
    lista = Producto.objects.filter(tipo=tipo, disponible=True).select_related('categoria')
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '')
    if q:
        lista = lista.filter(nombre__icontains=q)
    if categoria:
        lista = lista.filter(categoria__slug=categoria)
    contexto = {
        'productos': lista,
        'tipo': tipo,
        'titulo': 'Amigurumis' if tipo == 'amigurumi' else 'Insumos',
        'categorias': Categoria.objects.filter(tipo=tipo),
        'filtro': {'q': q, 'categoria': categoria},
    }
    return render(request, 'tienda/productos.html', contexto)


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    variantes = list(producto.variantes.all())
    variantes_json = [
        {'id': v.id, 'tamano': v.tamano, 'tamano_txt': v.get_tamano_display(), 'color': v.color,
         'hex': v.color_hex, 'precio': v.precio, 'foto': v.foto.url if v.foto else ''}
        for v in variantes
    ]
    compro = request.user.is_authenticated and DetallePedido.objects.filter(
        pedido__usuario=request.user, variante__producto=producto).exists()
    contexto = {
        'producto': producto,
        'variantes': variantes,
        'variantes_json': variantes_json,
        'tamanos': list(dict.fromkeys((v.tamano, v.get_tamano_display()) for v in variantes)),
        'colores': list(dict.fromkeys((v.color, v.color_hex) for v in variantes)),
        'resenas': producto.resenas.filter(visible=True).select_related('usuario'),
        'puede_resenar': compro,
        'form_resena': ResenaForm(),
    }
    return render(request, 'tienda/detalle_producto.html', contexto)


# ---------------------------------------------------------------------------
# Reseñas (solo de lo adquirido)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def resenar(request, tipo, pk):
    form = ResenaForm(request.POST)
    if tipo == 'patron':
        objeto = get_object_or_404(Patron, pk=pk)
        permitido = objeto.compras.filter(usuario=request.user).exists()
        destino = redirect('detalle_patron', pk=pk)
    else:
        objeto = get_object_or_404(Producto, pk=pk)
        permitido = DetallePedido.objects.filter(pedido__usuario=request.user, variante__producto=objeto).exists()
        destino = redirect('detalle_producto', pk=pk)

    if not permitido:
        messages.error(request, 'Solo puedes reseñar lo que hayas adquirido.')
    elif form.is_valid():
        resena = form.save(commit=False)
        resena.usuario = request.user
        setattr(resena, tipo, objeto)
        resena.save()
        messages.success(request, '¡Gracias por tu reseña!')
    return destino


# ---------------------------------------------------------------------------
# Carrito y pedidos
# ---------------------------------------------------------------------------
def ver_carrito(request):
    carrito = Carrito(request)
    return render(request, 'tienda/carrito.html', {'lineas': carrito.lineas(), 'total': carrito.total()})


@require_POST
def agregar_variante(request):
    variante = get_object_or_404(VarianteProducto, pk=request.POST.get('variante'))
    cantidad = max(1, int(request.POST.get('cantidad', 1)))
    Carrito(request).agregar(f'v-{variante.pk}', cantidad)
    messages.success(request, f'Agregaste {variante} al carrito.')
    return redirect(request.POST.get('siguiente') or 'carrito')


@require_POST
def agregar_kit(request, pk):
    kit = get_object_or_404(Kit, pk=pk)
    Carrito(request).agregar(f'k-{kit.pk}')
    messages.success(request, f'Agregaste el {kit.nombre} al carrito.')
    return redirect('carrito')


@require_POST
def agregar_patron(request, pk):
    patron = get_object_or_404(Patron, pk=pk, es_gratuito=False)
    carrito = Carrito(request)
    if f'p-{patron.pk}' not in carrito.items:      # un patrón se compra una sola vez
        carrito.agregar(f'p-{patron.pk}')
    messages.success(request, f'Agregaste el patrón {patron.titulo} al carrito.')
    return redirect('carrito')


@require_POST
def quitar_del_carrito(request, clave):
    Carrito(request).quitar(clave)
    return redirect('carrito')


@login_required
@require_POST
def confirmar_pedido(request):
    carrito = Carrito(request)
    lineas = carrito.lineas()
    if not lineas:
        return redirect('carrito')

    total = carrito.total()
    pedido = Pedido.objects.create(usuario=request.user, total=total,
                                   direccion_envio=request.user.direccion or 'Sin dirección')
    for linea in lineas:
        DetallePedido.objects.create(
            pedido=pedido,
            variante=linea['objeto'] if linea['tipo'] == 'v' else None,
            kit=linea['objeto'] if linea['tipo'] == 'k' else None,
            patron=linea['objeto'] if linea['tipo'] == 'p' else None,
            cantidad=linea['cantidad'], subtotal=linea['subtotal'])
        if linea['tipo'] == 'v':
            producto = linea['objeto'].producto
            producto.stock = max(0, producto.stock - linea['cantidad'])
            producto.save()
    carrito.vaciar()

    # PUNTO DE INTEGRACIÓN – Pasarela de pagos (fuera del alcance del proyecto).
    # Aquí el usuario sería redirigido a una pasarela externa (PSE, Wompi, Mercado Pago)
    # para pagar el pedido. Se muestra una página que representa ese paso.
    return render(request, 'tienda/pasarela.html', {'pedido': pedido})


@login_required
def mis_pedidos(request):
    pedidos = request.user.pedidos.prefetch_related('detalles__variante__producto', 'detalles__kit')
    return render(request, 'tienda/mis_pedidos.html', {'pedidos': pedidos})


# ---------------------------------------------------------------------------
# Cuenta de usuario
# ---------------------------------------------------------------------------
def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f'¡Bienvenida/o a Nudito, {usuario.first_name}!')
            return redirect('home')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})


@login_required
def perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tus datos se actualizaron.')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'tienda/perfil.html', {'form': form})
