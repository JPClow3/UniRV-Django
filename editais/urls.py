from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('editais/', views.index, name='editais_index'),
    path('comunidade/', views.comunidade, name='comunidade'),
    path('projetos-aprovados/', views.projetos_aprovados, name='projetos_aprovados'),
    path('passo-a-passo/', views.passo_a_passo, name='passo_a_passo'),
    path('edital/', RedirectView.as_view(pattern_name='editais_index', permanent=False)),
    
    # Slug-based URLs (primary)
    path('edital/<slug:slug>/', views.edital_detail, name='edital_detail_slug'),
    
    # PK-based URLs (legacy - redirect to slug)
    path('edital/<int:pk>/', views.edital_detail_redirect, name='edital_detail'),
    
    path('cadastrar/', views.edital_create, name='edital_create'),
    path('edital/<int:pk>/editar/', views.edital_update, name='edital_update'),
    path('edital/<int:pk>/excluir/', views.edital_delete, name='edital_delete'),

    # New features
    path('export/csv/', views.export_editais_csv, name='export_editais_csv'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('health/', views.health_check, name='health_check'),
    
    # Dashboard routes
    path('dashboard/home/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/editais/', views.dashboard_editais, name='dashboard_editais'),
    path('dashboard/editais/novo/', views.dashboard_novo_edital, name='dashboard_novo_edital'),
    path('dashboard/projetos/', views.dashboard_projetos, name='dashboard_projetos'),
    path('dashboard/projetos/submeter/', views.dashboard_submeter_projeto, name='dashboard_submeter_projeto'),
    path('dashboard/avaliacoes/', views.dashboard_avaliacoes, name='dashboard_avaliacoes'),
    path('dashboard/usuarios/', views.dashboard_usuarios, name='dashboard_usuarios'),
    path('dashboard/relatorios/', views.dashboard_relatorios, name='dashboard_relatorios'),
    path('dashboard/minhas-publicacoes/', views.dashboard_publicacoes, name='dashboard_publicacoes'),
]
