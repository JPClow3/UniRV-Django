from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # Password reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('editais/', views.index, name='editais_index'),
    path('ambientes-inovacao/', views.ambientes_inovacao, name='ambientes_inovacao'),
    path('projetos-aprovados/', views.projetos_aprovados, name='projetos_aprovados'),
    path('startups/', views.startups_showcase, name='startups_showcase'),
    path('startup/<slug:slug>/', views.startup_detail, name='startup_detail_slug'),
    path('startup/<int:pk>/', views.startup_detail_redirect, name='startup_detail'),
    path('edital/', RedirectView.as_view(pattern_name='editais_index', permanent=True)),
    
    path('edital/<slug:slug>/', views.edital_detail, name='edital_detail_slug'),
    path('edital/<int:pk>/', views.edital_detail_redirect, name='edital_detail'),
    
    path('cadastrar/', views.edital_create, name='edital_create'),
    path('edital/<int:pk>/editar/', views.edital_update, name='edital_update'),
    path('edital/<int:pk>/excluir/', views.edital_delete, name='edital_delete'),

    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('health/', views.health_check, name='health_check'),
    
    # Dashboard routes
    path('dashboard/home/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/editais/', views.dashboard_editais, name='dashboard_editais'),
    path('dashboard/editais/novo/', views.dashboard_novo_edital, name='dashboard_novo_edital'),
    path('dashboard/startups/', views.dashboard_projetos, name='dashboard_startups'),
    path('dashboard/startups/submeter/', views.dashboard_submeter_projeto, name='dashboard_submeter_startup'),
    path('dashboard/startups/<int:pk>/editar/', views.dashboard_startup_update, name='dashboard_startup_update'),
    # URL aliases for backward compatibility
    path('dashboard/projetos/', views.dashboard_projetos, name='dashboard_projetos'),
    path('dashboard/projetos/submeter/', views.dashboard_submeter_projeto, name='dashboard_submeter_projeto'),
    path('dashboard/usuarios/', views.dashboard_usuarios, name='dashboard_usuarios'),
]