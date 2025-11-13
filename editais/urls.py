from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.index, name='editais_index'),
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
]
