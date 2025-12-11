"""
Views module for editais app.

This module has been split into separate files for better organization:
- views/public.py: Public-facing views
- views/dashboard.py: Dashboard views
- views/editais_crud.py: CRUD operations

All views are re-exported here for backward compatibility with existing URL configurations.
"""

# Import all views from the new structure
from .views.public import (
    home,
    ambientes_inovacao,
    projetos_aprovados,
    startups_showcase,
    login_view,
    register_view,
    index,
    edital_detail,
    edital_detail_redirect,
    startup_detail,
    startup_detail_redirect,
    health_check,
)
from .views.dashboard import (
    dashboard_home,
    dashboard_editais,
    dashboard_projetos,
    dashboard_usuarios,
    dashboard_submeter_projeto,
    dashboard_startup_update,
    dashboard_novo_edital,
    admin_dashboard,
)
from .views.editais_crud import (
    edital_create,
    edital_update,
    edital_delete,
)

__all__ = [
    # Public views
    'home',
    'ambientes_inovacao',
    'projetos_aprovados',
    'startups_showcase',
    'login_view',
    'register_view',
    'index',
    'edital_detail',
    'edital_detail_redirect',
    'startup_detail',
    'startup_detail_redirect',
    'health_check',
    # Dashboard views
    'dashboard_home',
    'dashboard_editais',
    'dashboard_projetos',
    'dashboard_usuarios',
    'dashboard_submeter_projeto',
    'dashboard_startup_update',
    'dashboard_novo_edital',
    'admin_dashboard',
    # CRUD views
    'edital_create',
    'edital_update',
    'edital_delete',
]
