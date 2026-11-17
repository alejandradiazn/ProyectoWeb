"""Carga datos de ejemplo para probar Nudito.

Uso:  python manage.py cargar_datos
Crea categorías, amigurumis, insumos, patrones con sus piezas y vueltas,
kits, imágenes del carrusel y dos usuarios de prueba.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from tienda.models import (Categoria, ImagenCarrusel, Kit, MaterialPatron, Patron, Pieza,
                           Producto, Usuario, VarianteProducto, Vuelta)

IMG = Path(settings.BASE_DIR) / 'static' / 'img'


def imagen(nombre):
    """Abre una imagen de static/img para guardarla en un ImageField."""
    return File(open(IMG / nombre, 'rb'), name=nombre)


def asignar(obj, campo, nombre):
    getattr(obj, campo).save(nombre, imagen(nombre), save=False)


# Vueltas de ejemplo (un patrón básico de amigurumi)
ESFERA = [
    ('6 pb en anillo mágico', 6), ('6 aum', 12), ('(1 pb, 1 aum) x6', 18), ('(2 pb, 1 aum) x6', 24),
    ('(3 pb, 1 aum) x6', 30), ('pb en todos los puntos', 30), ('pb en todos los puntos', 30),
    ('(3 pb, 1 dism) x6', 24), ('(2 pb, 1 dism) x6', 18), ('Rellenar. (1 pb, 1 dism) x6', 12), ('6 dism y cerrar', 6),
]
EXTREMIDAD = [('6 pb en anillo mágico', 6), ('pb en todos los puntos', 6), ('pb en todos los puntos', 6),
              ('pb en todos los puntos', 6), ('Cerrar y dejar hebra para coser', None)]
OREJA = [('4 pb en anillo mágico', 4), ('(1 pb, 1 aum) x2', 6), ('pb en todos los puntos', 6),
         ('Aplanar y cerrar', None)]


class Command(BaseCommand):
    help = 'Carga datos de ejemplo (productos, patrones, carrusel y usuarios).'

    def handle(self, *args, **options):
        if Producto.objects.exists():
            self.stdout.write(self.style.WARNING('Ya hay datos cargados. No se hizo nada.'))
            return

        # ---------- Categorías ----------
        cat = {}
        for slug, nombre, tipo, foto in [
            ('animales', 'Animales', 'amigurumi', 'vaquitas-1.jpg'),
            ('navidad', 'Navidad', 'amigurumi', 'reno-2.jpg'),
            ('kawaii', 'Kawaii', 'amigurumi', 'corazones-1.jpg'),
            ('mini', 'Mini amigurumis', 'amigurumi', 'patitos-rana-2.jpg'),
            ('lanas', 'Lanas', 'insumo', ''),
            ('herramientas', 'Herramientas', 'insumo', ''),
        ]:
            c = Categoria(slug=slug, nombre=nombre, tipo=tipo)
            if foto:
                asignar(c, 'imagen', foto)
            c.save()
            cat[slug] = c

        # ---------- Amigurumis (con tamaños y colores) ----------
        amigurumis = [
            ('Reno navideño', 'navidad', 'reno-2.jpg', 'reno-1.jpg', 42000, [('Café', '#A0662F'), ('Beige', '#D9C2A0')]),
            ('Muñeco de nieve', 'navidad', 'muneco-nieve-1.jpg', 'muneco-nieve-2.jpg', 45000, [('Rojo y verde', '#C0392B')]),
            ('Monito con bolsito', 'animales', 'mono-1.jpg', 'mono-2.jpg', 48000, [('Mostaza', '#B8862B'), ('Café', '#8B5E34')]),
            ('Corazones', 'kawaii', 'corazones-1.jpg', 'corazones-2.jpg', 35000, [('Rojo', '#D62828'), ('Rosado', '#F2A7B5')]),
            ('Conejita con hoodie', 'animales', 'conejita-hoodie-1.jpg', 'conejita-hoodie-2.jpg', 50000, [('Rosado', '#F4B6C2'), ('Celeste', '#BFD9F2')]),
            ('Vaquitas peludas', 'animales', 'vaquitas-1.jpg', 'vaquitas-2.jpg', 46000, [('Negro', '#2B2B2B'), ('Gris', '#A9A9A9')]),
            ('Patitos con gorro de rana', 'mini', 'patitos-rana-1.jpg', 'patitos-rana-2.jpg', 22000, [('Amarillo', '#F6D96B'), ('Blanco', '#F5F5F5')]),
            ('Gatitos', 'animales', 'gatitos-1.jpg', 'gatitos-2.jpg', 38000, [('Siamés', '#C9A27E'), ('Gris', '#B9BEC4')]),
        ]
        for nombre, c, f1, f2, precio, colores in amigurumis:
            p = Producto(nombre=nombre, categoria=cat[c], tipo='amigurumi', precio=precio, stock=10,
                         descripcion='Amigurumi tejido a mano en lana chenille, relleno siliconado y ojos de seguridad. Ideal para regalar.')
            asignar(p, 'foto', f1)
            asignar(p, 'foto_alterna', f2)
            p.save()
            for tamano, extra in [('pequeno', -8000), ('mediano', 0), ('grande', 15000)]:
                for color, hexa in colores:
                    VarianteProducto.objects.create(producto=p, tamano=tamano, color=color,
                                                    color_hex=hexa, precio=precio + extra)

        # ---------- Insumos ----------
        chenille = Producto(nombre='Lana chenille 100 g', categoria=cat['lanas'], tipo='insumo', precio=14000, stock=50,
                            descripcion='Lana chenille 100% acrílica, suave y ideal para amigurumis.')
        asignar(chenille, 'foto', 'lanas-chenille-surtido.png')
        chenille.save()
        for color, hexa in [('cafe', '#B08D6E'), ('blanco', '#F3EFE4'), ('celeste', '#BFD9F2'), ('gris', '#C9CDD2'),
                            ('negro', '#2B2B2B'), ('menta', '#7FD8C3'), ('verde', '#C8D96A')]:
            v = VarianteProducto(producto=chenille, color=color.capitalize(), color_hex=hexa, precio=14000)
            asignar(v, 'foto', f'chenille-{color}.png')
            v.save()

        agujas = Producto(nombre='Set de agujas ergonómicas', categoria=cat['herramientas'], tipo='insumo', precio=45000, stock=20,
                          descripcion='8 agujas de crochet de 2.5 a 6 mm, con marcadores y agujas laneras.')
        asignar(agujas, 'foto', 'agujas-crochet-set.png')
        agujas.save()
        VarianteProducto.objects.create(producto=agujas, color='Rosado', color_hex='#F2A7B5', precio=45000)

        marcadores = Producto(nombre='Marcadores de puntos x40', categoria=cat['herramientas'], tipo='insumo', precio=8000, stock=40,
                              descripcion='Para marcar el inicio de cada vuelta.')
        asignar(marcadores, 'foto', 'marcadores-caja.png')
        asignar(marcadores, 'foto_alterna', 'marcadores-colores.png')
        marcadores.save()
        VarianteProducto.objects.create(producto=marcadores, color='Surtido', color_hex='#F6D96B', precio=8000)

        # ---------- Patrones con piezas y vueltas ----------
        patrones = [
            ('Conejita con moños', 'animales', 'conejita-monos-1.jpg', 'principiante', True, 0, '20 cm',
             [('Cabeza', 1, ESFERA), ('Cuerpo', 1, ESFERA), ('Brazos', 2, EXTREMIDAD), ('Orejas', 2, OREJA)]),
            ('Solecitos', 'kawaii', 'solecito-1.jpg', 'principiante', False, 12000, '15 cm',
             [('Cuerpo', 1, ESFERA), ('Rayos', 6, OREJA), ('Piernas', 2, EXTREMIDAD)]),
            ('Pollito', 'animales', 'pollito-1.jpg', 'principiante', True, 0, '18 cm',
             [('Cuerpo', 1, ESFERA), ('Alas', 2, OREJA)]),
            ('Gatitos', 'animales', 'gatitos-3.jpg', 'intermedio', False, 15000, '14 cm',
             [('Cabeza', 1, ESFERA), ('Cuerpo', 1, ESFERA), ('Patas', 4, EXTREMIDAD), ('Cola', 1, EXTREMIDAD)]),
            ('Reno navideño', 'navidad', 'reno-1.jpg', 'avanzado', False, 18000, '22 cm',
             [('Cabeza', 1, ESFERA), ('Cuerpo', 1, ESFERA), ('Cuernos', 2, EXTREMIDAD), ('Orejas', 2, OREJA)]),
            ('Patitos con gorro de rana', 'mini', 'patitos-rana-3.jpg', 'intermedio', False, 10000, '8 cm',
             [('Cuerpo', 1, ESFERA), ('Gorro', 1, ESFERA), ('Pico', 1, OREJA)]),
        ]
        for titulo, c, foto, nivel, gratis, precio, tamano, piezas in patrones:
            pt = Patron(titulo=titulo, categoria=cat[c], nivel=nivel, es_gratuito=gratis, precio=precio,
                        tamano_final=tamano,
                        descripcion=f'Patrón paso a paso para tejer {titulo.lower()} en lana chenille. Incluye todas las piezas y vueltas.')
            asignar(pt, 'foto', foto)
            pt.save()
            for orden, (nombre, cantidad, vueltas) in enumerate(piezas, start=1):
                pieza = Pieza.objects.create(patron=pt, nombre=nombre, cantidad=cantidad, orden=orden)
                for numero, (instruccion, puntos) in enumerate(vueltas, start=1):
                    Vuelta.objects.create(pieza=pieza, numero=numero, instruccion=instruccion, puntos=puntos)
            MaterialPatron.objects.create(patron=pt, producto=chenille, cantidad=2)
            MaterialPatron.objects.create(patron=pt, producto=agujas, cantidad=1)
            MaterialPatron.objects.create(patron=pt, producto=marcadores, cantidad=1)
            Kit.objects.create(patron=pt, nombre=f'Kit {titulo}', precio=(precio or 0) + 30000)

        # ---------- Carrusel ----------
        for orden, (foto, titulo, enlace) in enumerate([
            ('patitos-rana-1.jpg', 'Nuevos: patitos con gorro de rana', '/patrones/'),
            ('lanas-chenille-surtido.png', 'Lana chenille en 7 colores', '/insumos/'),
            ('agujas-crochet-set.png', 'Agujas de 2.5 a 6 mm', '/insumos/'),
            ('gatitos-1.jpg', 'Patrón de gatitos disponible', '/patrones/'),
        ], start=1):
            img = ImagenCarrusel(titulo=titulo, enlace=enlace, orden=orden)
            asignar(img, 'imagen', foto)
            img.save()

        # ---------- Usuarios de prueba ----------
        if not Usuario.objects.filter(username='admin').exists():
            Usuario.objects.create_superuser('admin', 'admin@nudito.co', 'admin123', rol='administrador',
                                             first_name='Administrador')
        if not Usuario.objects.filter(username='ana').exists():
            Usuario.objects.create_user('ana', 'ana@correo.com', 'nudito123', first_name='Ana', last_name='Gómez',
                                        direccion='Calle 9 # 27-10, Bucaramanga', nivel='principiante')

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados. Admin: admin/admin123 · Cliente: ana/nudito123'))
