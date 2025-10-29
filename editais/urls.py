from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='editais_index'),
    path('edital/<int:pk>/', views.edital_detail, name='edital_detail'),
    path('cadastrar/', views.edital_create, name='edital_create'),
    path('edital/<int:pk>/editar/', views.edital_update, name='edital_update'),
    path('edital/<int:pk>/excluir/', views.edital_delete, name='edital_delete'),
]

