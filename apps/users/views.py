import string
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.urls import reverse
from .models import User
from .forms import LoginForm, StudentRegisterForm, TeacherRegisterForm, ParentRegisterForm
import logging
from validate_email import validate_email


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from .forms import TeacherRegisterForm, EmailVerificationForm
from .utils import send_verification_email, send_welcome_email


# Configuración centralizada para tipos de usuario
USER_TYPE_CONFIG = {
    1: {  # Estudiante
        'name': 'Estudiante',
        'background': 'images/forms/fondo.png',
        'registration_url': 'users:register_student',
        'dashboard_url': 'users:dashboard_student'
    },
    2: {  # Docente
        'name': 'Docente', 
        'background': 'images/forms/fondo_doc.png',
        'registration_url': 'users:register_teacher',
        'dashboard_url': 'users:dashboard_teacher'
    },
    3: {  # Padre
        'name': 'Padre',
        'background': 'images/forms/fondo_padres.png', 
        'registration_url': 'users:register_parent',
        'dashboard_url': 'users:dashboard_parent'
    },
    4: {  # Admin
        'name': 'Administrador',
        'background': 'images/forms/fondo_admin.png',
        'registration_url': None,  # Los admin no se registran públicamente
        'dashboard_url': 'users:dashboard_admin'
    }
}

def login_unificado(request):
    """Vista de login actualizada para verificar email"""
    if request.user.is_authenticated:
        return redirect_to_user_dashboard(request)
    
    if request.method == 'POST':
        from .forms import LoginForm
        form = LoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si el email está verificado
            if not user.is_email_verified:
                messages.warning(
                    request,
                    'Debes verificar tu email antes de iniciar sesión.'
                )
                return redirect('users:email_verification', user_id=user.id)
            
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.get_full_name()}!')
            return redirect_to_user_dashboard(request)
        else:
            messages.error(request, 'Credenciales inválidas.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def redirect_to_user_dashboard(request):
    """Redirige al dashboard según el tipo de usuario"""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    user = request.user
    
    if user.user_type == 1:  # Estudiante
        return redirect('users:dashboard_student', user_id=user.id)
    elif user.user_type == 2:  # Docente
        return redirect('users:dashboard_teacher', user_id=user.id)
    elif user.user_type == 3:  # Padre
        return redirect('users:dashboard_parent', user_id=user.id)
    elif user.user_type == 4:  # Admin
        return redirect('users:dashboard_admin', user_id=user.id)
    else:
        return redirect('users:login')

def mask_email(email):
    """Enmascara el email para mostrar solo primeros y últimos caracteres"""
    try:
        name, domain = email.split('@')
        if len(name) <= 2:
            masked_name = name
        else:
            masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
        return f"{masked_name}@{domain}"
    except:
        return email

def register_view(request, form_class, template, redirect_name='users:login'):
    """
    Vista genérica para registro de usuarios
    """
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} registrado exitosamente.")
            return redirect(redirect_name)
        else:
            messages.error(request, "Error en el registro. Por favor, revisa los datos.")
    else:
        form = form_class()
    
    return render(request, template, {'form': form})

logger = logging.getLogger(__name__)

def register_student(request):
    """Registro específico para estudiantes"""
    return register_view(request, StudentRegisterForm, 'accounts/signup_student.html')

def register_teacher(request):
    """Registro de docentes con verificación de email"""
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f'¡Registro exitoso! Se ha enviado un código de verificación a {user.email}'
            )
            # Redirigir a la página de verificación
            return redirect('users:verify_email', user_id=user.id)
    else:
        form = TeacherRegisterForm()
    
    return render(request, 'accounts/signup_teacher.html', {'form': form})

def register_parent(request):
    """Registro específico para padres"""
    return register_view(request, ParentRegisterForm, 'accounts/signup_parent.html')

def verify_email(request, user_id):
    """Vista para verificar el código de email"""
    user = get_object_or_404(User, id=user_id)
    
    # Si ya está verificado, redirigir
    if user.is_email_verified:
        messages.info(request, 'Tu email ya está verificado.')
        return redirect('users:login')
    
    if request.method == 'POST':
        form = EmailVerificationForm(user, request.POST)
        if form.is_valid():
            # Verificar y activar la cuenta
            user.verify_email()
            user.is_active = True
            user.save()
            
            # Enviar email de bienvenida
            send_welcome_email(user)
            
            messages.success(request, '¡Email verificado exitosamente! Ya puedes iniciar sesión.')
            return redirect('users:login')
    else:
        form = EmailVerificationForm(user)
    
    return render(request, 'accounts/verify_email.html', {
        'form': form,
        'user': user
    })
def resend_verification_code(request, user_id):
    """Vista para reenviar código de verificación"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        if user.is_email_verified:
            return JsonResponse({
                'success': False,
                'message': 'El email ya está verificado.'
            })
        
        # Verificar límite de tiempo (1 minuto entre envíos)
        if (user.email_verification_created and 
            timezone.now() - user.email_verification_created < timezone.timedelta(minutes=1)):
            return JsonResponse({
                'success': False,
                'message': 'Debes esperar 1 minuto antes de solicitar otro código.'
            })
        
        # Enviar nuevo código
        if send_verification_email(user):
            return JsonResponse({
                'success': True,
                'message': 'Código reenviado exitosamente.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error enviando el código. Intenta nuevamente.'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})



@login_required
def dashboard_view(request, user_id, user_type, template):
    """
    Vista genérica para dashboards con validación de acceso
    """
    user = get_object_or_404(User, id=user_id, user_type=user_type)
    
    # Verificar que el usuario logueado sea el mismo que está accediendo
    if request.user != user:
        messages.error(request, "No tienes permisos para acceder a este dashboard.")
        # Redirigir al dashboard correcto del usuario actual
        if request.user.user_type in USER_TYPE_CONFIG:
            dashboard_url = USER_TYPE_CONFIG[request.user.user_type]['dashboard_url']
            return redirect(dashboard_url, user_id=request.user.id)
        return redirect('users:login')
    
    context = {
        'user': user,
        'user_type_name': USER_TYPE_CONFIG.get(user_type, {}).get('name', 'Usuario'),
    }
    
    return render(request, template, context)

@login_required
def dashboard_student(request, user_id):
    """Dashboard para estudiantes"""
    return dashboard_view(request, user_id, 1, 'dashboards/dashboard_student.html')

@login_required
def dashboard_teacher(request, user_id):
    """Dashboard para docentes"""
    return dashboard_view(request, user_id, 2, 'dashboards/dashboard_teacher.html')

@login_required
def dashboard_parent(request, user_id):
    """Dashboard para padres"""
    return dashboard_view(request, user_id, 3, 'dashboards/dashboard_parent.html')

@login_required
def dashboard_admin(request, user_id):
    """Dashboard para administradores"""
    logging.debug(f"Accediendo a dashboard_admin con user_id: {user_id}")
    return dashboard_view(request, user_id, 4, 'dashboards/dashboard_admin.html')

def get_user_dashboard_url(user):
    """
    Función auxiliar para obtener la URL del dashboard según el tipo de usuario
    """
    if user.user_type in USER_TYPE_CONFIG:
        dashboard_url = USER_TYPE_CONFIG[user.user_type]['dashboard_url']
        return reverse(dashboard_url, kwargs={'user_id': user.id})
    return reverse('users:login')





@login_required
def redirect_to_user_dashboard(request):
    """
    Redirige al usuario a su dashboard correspondiente según su tipo
    """
    user = request.user
    if user.user_type in USER_TYPE_CONFIG:
        dashboard_url = USER_TYPE_CONFIG[user.user_type]['dashboard_url']
        return redirect(dashboard_url, user_id=user.id)
    else:
        messages.error(request, "Tipo de usuario no reconocido.")
        return redirect('users:login')

def home_redirect(request):
    """
    Redirecciona desde la raíz del sitio
    """
    if request.user.is_authenticated:
        return redirect_to_user_dashboard(request)
    else:
        return redirect('users:login')

# Función auxiliar para usar en templates
def get_registration_links():
    """
    Devuelve los enlaces de registro disponibles
    """
    return {
        'estudiante': reverse('users:register_student'),
        'docente': reverse('users:register_teacher'),
        'padre': reverse('users:register_parent'),
    }