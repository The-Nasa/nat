from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, ParentProfile
from validate_email import validate_email
from .utils import send_verification_email
class StudentRegisterForm(UserCreationForm):
    GRADE_CHOICES = [
        ('', 'Selecciona tu grado'),
        ('primero', 'Primero'),
        ('segundo', 'Segundo'),
    ]

    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellido Paterno y Materno', required=True)
    school = forms.CharField(
        label='Institución educativa',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de tu colegio'})
    )
    grade = forms.ChoiceField(
        label='Grado de nivel educativo',
        choices=GRADE_CHOICES,
        required=False
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2', 'school', 'grade'
        )
        labels = {
            'username': 'Nombre de usuario',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        if not validate_email(email):
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 1  # Estudiante
        user.school = self.cleaned_data.get('school', '')
        user.grade = self.cleaned_data.get('grade', '')
        if commit:
            user.save()
        return user


class TeacherRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    school = forms.CharField(
        label='Institución educativa', 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de tu institución'})
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'password1', 'password2', 'school'
        )
        labels = {
            'username': 'Nombre de usuario',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Verificar si ya existe un usuario con este email
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        
        # Validar formato del email
        if not validate_email(email):
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        
        # Opcional: Validar dominio específico para docentes
        # dominio = email.split('@')[-1]
        # if dominio.lower() != 'minedu.edu.pe':
        #     raise ValidationError("❌ Solo se permiten correos institucionales del dominio minedu.edu.pe.")
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 2  # Docente
        user.school = self.cleaned_data.get('school', '')
        user.is_active = False
        
        if commit:
            user.save()
            send_verification_email(user)
        return user



class ParentRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'Nombre de usuario',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Verificar si ya existe un usuario con este email
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        
        # Validar formato del email
        if not validate_email(email):
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 3  # Tipo padre
        
        if commit:
            user.save()
            ParentProfile.objects.create(user=user)
            
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Correo o nombre de usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu email o nombre de usuario'
        })
    )
    password = forms.CharField(
        label='Contraseña', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        from django.contrib.auth import authenticate
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            try:
                # Buscar por email
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                username = username_or_email

            self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise ValidationError("❌ Credenciales inválidas. Verifica tu email/usuario y contraseña.")
        
            if not self.user_cache.is_active:
                raise ValidationError("❌ Tu cuenta está desactivada.")

            # ✅ Validar si el tipo es válido si deseas filtrar por correo institucional
            if self.user_cache.user_type == 2:  # Docente
                dominio = self.user_cache.email.split('@')[-1].lower()
                dominios_permitidos = ['minedu.edu.pe', 'ugel.edu.pe', 'dre.edu.pe']
                if dominio not in dominios_permitidos:
                    raise ValidationError("❌ Los docentes deben usar un correo institucional.")
        
        return self.cleaned_data


    def get_user(self):
        return self.user_cache


# Formulario adicional para validación de email institucional (opcional)
class TeacherRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    school = forms.CharField(
        label='Institución educativa', 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de tu institución'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school')
        labels = {'username': 'Nombre de usuario'}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        
        # Validar dominio específico para docentes (opcional)
        # dominio = email.split('@')[-1]
        # if dominio.lower() != 'minedu.edu.pe':
        #     raise ValidationError("❌ Solo se permiten correos institucionales.")
        
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 2  # Docente
        user.school = self.cleaned_data.get('school', '')
        user.is_active = False  # Usuario inactivo hasta verificar email
        
        if commit:
            user.save()
            # Enviar email de verificación
            send_verification_email(user)


# Formulario para cambio de contraseña personalizado
class CustomPasswordChangeForm(forms.Form):
    """
    Formulario personalizado para cambio de contraseña
    """
    old_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Debe contener al menos 8 caracteres.'
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("❌ La contraseña actual es incorrecta.")
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("❌ Las contraseñas no coinciden.")
        
        return new_password2

    def save(self):
        new_password = self.cleaned_data['new_password1']
        self.user.set_password(new_password)
        self.user.save()
        return self.user
    
    
class EmailVerificationForm(forms.Form):
    """Formulario para verificar código de email"""
    verification_code = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '123456',
            'autocomplete': 'off',
            'style': 'letter-spacing: 0.5rem; font-size: 1.5rem;'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        
        if not code:
            raise ValidationError("❌ Por favor ingresa el código de verificación.")
        
        if not self.user.is_verification_code_valid(code):
            raise ValidationError("❌ El código es inválido o ha expirado. Solicita uno nuevo.")
        
        return code