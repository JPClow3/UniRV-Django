"""
Views package for editais app.

This package contains all views organized by functionality:
- public: Public-facing views (home, index, detail, etc.)
- dashboard: Dashboard views for authenticated users
- editais_crud: CRUD operations for editais
"""

from .public import (
    home,
    ambientes_inovacao,
    projetos_aprovados,
    startups_showcase,
    startup_detail,
    startup_detail_redirect,
    login_view,
    register_view,
    index,
    edital_detail,
    edital_detail_redirect,
    health_check,
    build_search_query,
)
from .dashboard import (
    dashboard_home,
    dashboard_editais,
    dashboard_projetos,
    dashboard_usuarios,
    dashboard_submeter_projeto,
    dashboard_novo_edital,
    admin_dashboard,
)
from .editais_crud import (
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
    'startup_detail',
    'startup_detail_redirect',
    'login_view',
    'register_view',
    'index',
    'edital_detail',
    'edital_detail_redirect',
    'health_check',
    'build_search_query',
    # Dashboard views
    'dashboard_home',
    'dashboard_editais',
    'dashboard_projetos',
    'dashboard_usuarios',
    'dashboard_submeter_projeto',
    'dashboard_novo_edital',
    'admin_dashboard',
    # CRUD views
    'edital_create',
    'edital_update',
    'edital_delete',
]

