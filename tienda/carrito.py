"""Carrito de compras guardado en la sesión del usuario."""
from .models import Kit, Patron, VarianteProducto


class Carrito:
    def __init__(self, request):
        self.session = request.session
        self.items = self.session.setdefault('carrito', {})

    def agregar(self, clave, cantidad=1):
        item = self.items.setdefault(clave, {'cantidad': 0})
        item['cantidad'] += cantidad
        self.guardar()

    def quitar(self, clave):
        self.items.pop(clave, None)
        self.guardar()

    def vaciar(self):
        self.session['carrito'] = {}
        self.items = self.session['carrito']
        self.guardar()

    def guardar(self):
        self.session.modified = True

    def lineas(self):
        """Devuelve cada artículo con su objeto, precio y subtotal."""
        resultado = []
        for clave, datos in list(self.items.items()):
            tipo, pk = clave.split('-')
            if tipo == 'v':
                obj = VarianteProducto.objects.filter(pk=pk).select_related('producto').first()
                nombre = str(obj) if obj else ''
            elif tipo == 'k':
                obj = Kit.objects.filter(pk=pk).first()
                nombre = obj.nombre if obj else ''
            else:
                obj = Patron.objects.filter(pk=pk).first()
                nombre = f'Patrón {obj.titulo}' if obj else ''
            if obj is None:
                self.quitar(clave)
                continue
            resultado.append({
                'clave': clave, 'tipo': tipo, 'objeto': obj, 'nombre': nombre,
                'cantidad': datos['cantidad'], 'precio': obj.precio,
                'subtotal': obj.precio * datos['cantidad'],
            })
        return resultado

    def total(self):
        return sum(linea['subtotal'] for linea in self.lineas())
