def carrito(request):
    """Cantidad de artículos del carrito, disponible en todas las plantillas."""
    items = request.session.get('carrito', {})
    return {'cantidad_carrito': sum(item['cantidad'] for item in items.values())}
