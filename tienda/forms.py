from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Resena, Usuario


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label='Nombre', max_length=60)
    last_name = forms.CharField(label='Apellido', max_length=60)
    email = forms.EmailField(label='Correo electrónico')

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'direccion', 'nivel']
        labels = {'username': 'Nombre de usuario'}


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion', 'nivel']
        labels = {'first_name': 'Nombre', 'last_name': 'Apellido', 'email': 'Correo'}


class ResenaForm(forms.ModelForm):
    calificacion = forms.TypedChoiceField(
        label='Calificación', coerce=int, widget=forms.RadioSelect,
        choices=[(i, '★' * i) for i in range(5, 0, -1)])

    class Meta:
        model = Resena
        fields = ['calificacion', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Cuéntanos qué te pareció'}),
        }
