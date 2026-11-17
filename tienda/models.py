"""Modelos de Nudito: tienda y patrones de amigurumis.

Corresponden a los modelos potenciales y al diagrama entidad-relación
del avance del proyecto.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg


NIVELES = [
    ('principiante', 'Principiante'),
    ('intermedio', 'Intermedio'),
    ('avanzado', 'Avanzado'),
]


class Usuario(AbstractUser):
    """Usuario del sitio. Hereda nombre, correo y contraseña de Django."""
    ROLES = [('cliente', 'Cliente'), ('administrador', 'Administrador')]

    telefono = models.CharField('teléfono', max_length=20, blank=True)
    direccion = models.CharField('dirección', max_length=200, blank=True)
    nivel = models.CharField('nivel tejiendo', max_length=15, choices=NIVELES, blank=True)
    rol = models.CharField(max_length=15, choices=ROLES, default='cliente')

    def es_administrador(self):
        return self.rol == 'administrador' or self.is_staff


class Categoria(models.Model):
    TIPOS = [('amigurumi', 'Amigurumi'), ('insumo', 'Insumo')]

    nombre = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    imagen = models.ImageField(upload_to='categorias/', blank=True)

    class Meta:
        verbose_name = 'categoría'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Amigurumis ya tejidos e insumos (hilos, agujas, marcadores...)."""
    TIPOS = [('amigurumi', 'Amigurumi'), ('insumo', 'Insumo')]

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField('descripción', blank=True)
    foto = models.ImageField(upload_to='productos/')
    foto_alterna = models.ImageField('segunda foto', upload_to='productos/', blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    precio = models.PositiveIntegerField(help_text='Precio base en pesos')
    stock = models.PositiveIntegerField(default=0)
    disponible = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def precio_desde(self):
        variante = self.variantes.order_by('precio').first()
        return variante.precio if variante else self.precio

    def calificacion(self):
        return self.resenas.aggregate(prom=Avg('calificacion'))['prom'] or 0


class VarianteProducto(models.Model):
    """Combinación de tamaño y color de un producto, con su propio precio."""
    TAMANOS = [('pequeno', 'Pequeño'), ('mediano', 'Mediano'), ('grande', 'Grande'), ('unico', 'Único')]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    tamano = models.CharField('tamaño', max_length=10, choices=TAMANOS, default='unico')
    color = models.CharField(max_length=30)
    color_hex = models.CharField('código de color', max_length=7, default='#CCCCCC')
    foto = models.ImageField(upload_to='variantes/', blank=True)
    precio = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'variante de producto'
        verbose_name_plural = 'variantes de producto'
        ordering = ['precio']

    def __str__(self):
        return f'{self.producto} – {self.get_tamano_display()} – {self.color}'


class Patron(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='patrones',
                                  limit_choices_to={'tipo': 'amigurumi'})
    titulo = models.CharField('título', max_length=100)
    descripcion = models.TextField('descripción')
    foto = models.ImageField(upload_to='patrones/')
    nivel = models.CharField(max_length=15, choices=NIVELES)
    tamano_final = models.CharField('tamaño final', max_length=30, blank=True)
    es_gratuito = models.BooleanField('es gratuito', default=False)
    precio = models.PositiveIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'patrón'
        verbose_name_plural = 'patrones'
        ordering = ['-creado']

    def __str__(self):
        return self.titulo

    def total_vueltas(self):
        return Vuelta.objects.filter(pieza__patron=self).count()

    def calificacion(self):
        return self.resenas.aggregate(prom=Avg('calificacion'))['prom'] or 0

    def usuario_tiene_acceso(self, usuario):
        """Regla de negocio: gratuito o comprado = acceso completo."""
        if self.es_gratuito:
            return True
        if not usuario.is_authenticated:
            return False
        return self.compras.filter(usuario=usuario).exists()


class Pieza(models.Model):
    patron = models.ForeignKey(Patron, on_delete=models.CASCADE, related_name='piezas')
    nombre = models.CharField(max_length=60, help_text='Cabeza, cuerpo, brazos...')
    cantidad = models.PositiveSmallIntegerField(default=1, help_text='Veces que se teje la pieza')
    orden = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f'{self.patron} – {self.nombre}'


class Vuelta(models.Model):
    pieza = models.ForeignKey(Pieza, on_delete=models.CASCADE, related_name='vueltas')
    numero = models.PositiveSmallIntegerField('número')
    instruccion = models.CharField('instrucción', max_length=200)
    puntos = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['pieza__orden', 'numero']

    def __str__(self):
        return f'V{self.numero}: {self.instruccion}'


class MaterialPatron(models.Model):
    """Insumos sugeridos para tejer un patrón."""
    patron = models.ForeignKey(Patron, on_delete=models.CASCADE, related_name='materiales')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, limit_choices_to={'tipo': 'insumo'})
    cantidad = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = 'material del patrón'
        verbose_name_plural = 'materiales del patrón'

    def __str__(self):
        return f'{self.cantidad} x {self.producto}'


class Kit(models.Model):
    patron = models.OneToOneField(Patron, on_delete=models.CASCADE, related_name='kit')
    nombre = models.CharField(max_length=100)
    precio = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre


class CompraPatron(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='patrones_comprados')
    patron = models.ForeignKey(Patron, on_delete=models.CASCADE, related_name='compras')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'compra de patrón'
        verbose_name_plural = 'compras de patrones'
        unique_together = ['usuario', 'patron']

    def __str__(self):
        return f'{self.usuario} – {self.patron}'


class ProgresoPatron(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='progresos')
    patron = models.ForeignKey(Patron, on_delete=models.CASCADE, related_name='progresos')
    vueltas_completadas = models.ManyToManyField(Vuelta, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'progreso de patrón'
        verbose_name_plural = 'progresos de patrones'
        unique_together = ['usuario', 'patron']

    def __str__(self):
        return f'{self.usuario} – {self.patron} ({self.porcentaje()}%)'

    def porcentaje(self):
        total = self.patron.total_vueltas()
        if total == 0:
            return 0
        return round(self.vueltas_completadas.count() * 100 / total)


class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de pago'),
        ('pagado', 'Pagado'),
        ('elaboracion', 'En elaboración'),
        ('despachado', 'Despachado'),
    ]
    ESTADOS_PAGADOS = ['pagado', 'elaboracion', 'despachado']

    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='pendiente')
    total = models.PositiveIntegerField(default=0)
    direccion_envio = models.CharField('dirección de envío', max_length=200)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'Pedido #{self.pk} – {self.usuario}'

    def esta_pagado(self):
        return self.estado in self.ESTADOS_PAGADOS

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Cuando el administrador confirma el pago, se desbloquean los patrones del pedido
        if self.esta_pagado():
            self.entregar_patrones()

    def entregar_patrones(self):
        for detalle in self.detalles.select_related('patron', 'kit__patron'):
            patron = detalle.patron or (detalle.kit.patron if detalle.kit else None)
            if patron:
                CompraPatron.objects.get_or_create(usuario=self.usuario, patron=patron)


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    variante = models.ForeignKey(VarianteProducto, on_delete=models.PROTECT, null=True, blank=True)
    kit = models.ForeignKey(Kit, on_delete=models.PROTECT, null=True, blank=True)
    patron = models.ForeignKey(Patron, on_delete=models.PROTECT, null=True, blank=True)
    cantidad = models.PositiveSmallIntegerField(default=1)
    subtotal = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'detalle de pedido'
        verbose_name_plural = 'detalles de pedido'

    def __str__(self):
        return f'{self.cantidad} x {self.variante or self.kit or self.patron}'


class Resena(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True, related_name='resenas')
    patron = models.ForeignKey(Patron, on_delete=models.CASCADE, null=True, blank=True, related_name='resenas')
    calificacion = models.PositiveSmallIntegerField('calificación', choices=[(i, '★' * i) for i in range(1, 6)])
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True, help_text='Desmarcar para moderar (ocultar) la reseña')

    class Meta:
        verbose_name = 'reseña'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.usuario} – {self.calificacion}★'


class ImagenCarrusel(models.Model):
    imagen = models.ImageField(upload_to='carrusel/')
    titulo = models.CharField('título', max_length=100)
    enlace = models.CharField(max_length=200, blank=True)
    orden = models.PositiveSmallIntegerField(default=1)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'imagen del carrusel'
        verbose_name_plural = 'imágenes del carrusel'
        ordering = ['orden']

    def __str__(self):
        return self.titulo
