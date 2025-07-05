from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # ========== AUTENTICACIÓN ==========
    path('login/', views.login_unificado, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),
    
    # ========== REGISTRO POR TIPO DE USUARIO ==========
    path('registro/estudiante/', views.register_student, name='register_student'),
    path('registro/docente/', views.register_teacher, name='register_teacher'),
    path('registro/padre/', views.register_parent, name='register_parent'),

    # ========== REDIRECCIONES ==========
    path('perfil/', views.redirect_to_user_dashboard, name='profile'),
    path('', views.home_redirect, name='home'),
    
    # ========== RECUPERACIÓN DE CONTRASEÑA ==========
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
