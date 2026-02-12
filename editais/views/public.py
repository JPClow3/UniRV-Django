"""
Public views for the editais app.

This module contains all public-facing views that don't require authentication
or are accessible to all users.
"""

import logging
from typing import Optional, Union
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connection, DatabaseError, ProgrammingError
from django.core.exceptions import ValidationError
from django.http import (
    Http404,
    HttpResponse,
    JsonResponse,
    HttpRequest,
    HttpResponseRedirect,
)
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.urls import reverse

from ..constants import (
    CACHE_TTL_INDEX,
    PAGINATION_DEFAULT,
    ACTIVE_STARTUP_STATUSES,
    SECONDS_PER_DAY,
    CACHE_TTL_15_MINUTES,
    MAX_SEARCH_LENGTH,
    MAX_STARTUPS_DISPLAY,
)
from ..models import Edital, Startup
from ..utils import mark_edital_fields_safe, parse_date_filter, get_search_suggestions
from ..cache_utils import (
    get_index_cache_key,
    get_detail_cache_key,
    get_cached_response,
    cache_response,
)
from ..decorators import rate_limit
from ..forms import UserRegistrationForm
from ..tasks import send_welcome_email_async

logger = logging.getLogger(__name__)


def _parse_index_params(request: HttpRequest) -> dict:
    """Parse index view params (filters, page, cache keys)."""
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    orgao_filter = request.GET.get("orgao", "")
    start_date_filter = request.GET.get("start_date", "")
    end_date_filter = request.GET.get("end_date", "")
    only_open = request.GET.get("only_open", "") == "1"
    page_number = request.GET.get("page", "1")
    try:
        n = int(page_number)
        if n < 1:
            page_number = "1"
    except ValueError:
        page_number = "1"
    if search_query and len(search_query) > MAX_SEARCH_LENGTH:
        search_query = search_query[:MAX_SEARCH_LENGTH]
        messages.warning(
            request, f"A busca foi truncada para {MAX_SEARCH_LENGTH} caracteres."
        )
    has_filters = bool(
        search_query
        or status_filter
        or orgao_filter
        or start_date_filter
        or end_date_filter
        or only_open
    )
    use_cache = not has_filters and not request.user.is_authenticated
    cache_key = None
    if use_cache:
        version_key = "editais_index_cache_version"
        cache_version = cache.get(version_key, 0)
        cache_key = get_index_cache_key(page_number, cache_version)
    return {
        "search_query": search_query,
        "status_filter": status_filter,
        "orgao_filter": orgao_filter,
        "start_date_filter": start_date_filter,
        "end_date_filter": end_date_filter,
        "only_open": only_open,
        "page_number": page_number,
        "has_filters": has_filters,
        "use_cache": use_cache,
        "cache_key": cache_key,
    }


def _get_index_context(request: HttpRequest, params: dict) -> dict:
    """Build index view context from request and params."""
    editais = (
        Edital.objects.with_related()
        .prefetch_related("valores")
        .only(
            "id",
            "numero_edital",
            "titulo",
            "url",
            "entidade_principal",
            "status",
            "start_date",
            "end_date",
            "objetivo",
            "data_criacao",
            "data_atualizacao",
            "slug",
            "created_by",
            "updated_by",
        )
    )
    if not request.user.is_authenticated or not request.user.is_staff:
        editais = editais.active()
    if params["search_query"]:
        editais = editais.search(params["search_query"])
    if params["status_filter"]:
        editais = editais.filter(status=params["status_filter"])
    elif params["only_open"]:
        editais = editais.filter(status="aberto")
    if params["orgao_filter"]:
        editais = editais.filter(entidade_principal=params["orgao_filter"])
    start_date = parse_date_filter(params["start_date_filter"])
    if start_date:
        editais = editais.filter(start_date__gte=start_date)
    end_date = parse_date_filter(params["end_date_filter"])
    if end_date:
        editais = editais.filter(end_date__lte=end_date)
    per_page = getattr(settings, "EDITAIS_PER_PAGE", PAGINATION_DEFAULT)
    paginator = Paginator(editais, per_page)
    page_obj = paginator.get_page(params["page_number"])
    search_suggestions = []
    if page_obj.paginator.count == 0 and params["search_query"]:
        try:
            search_suggestions = get_search_suggestions(params["search_query"], limit=3)
        except (AttributeError, ValueError, TypeError, ProgrammingError) as e:
            # get_search_suggestions can raise database exceptions (ProgrammingError),
            # or other exceptions (AttributeError, ValueError, TypeError) from internal operations
            logger.warning("Error generating search suggestions: %s", e, exc_info=True)
    base_orgaos = Edital.objects
    if not request.user.is_authenticated or not request.user.is_staff:
        base_orgaos = base_orgaos.active()
    unique_orgaos = (
        base_orgaos.exclude(entidade_principal__isnull=True)
        .exclude(entidade_principal="")
        .values_list("entidade_principal", flat=True)
        .distinct()
        .order_by("entidade_principal")
    )
    return {
        "page_obj": page_obj,
        "search_query": params["search_query"],
        "status_filter": params["status_filter"],
        "orgao_filter": params["orgao_filter"],
        "start_date_filter": params["start_date_filter"],
        "end_date_filter": params["end_date_filter"],
        "only_open": params["only_open"],
        "status_choices": Edital.STATUS_CHOICES,
        "unique_orgaos": list(unique_orgaos),
        "total_count": page_obj.paginator.count,
        "search_suggestions": search_suggestions,
    }


def _get_index_template_name(request: HttpRequest) -> str:
    """Return index template (partial for AJAX, full otherwise)."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return "editais/index_partial.html"
    return "editais/index.html"


def _index_empty_context() -> dict:
    """Context for index error state."""
    page_obj = Paginator(Edital.objects.none(), PAGINATION_DEFAULT).get_page(1)
    return {
        "page_obj": page_obj,
        "search_query": "",
        "status_filter": "",
        "orgao_filter": "",
        "start_date_filter": "",
        "end_date_filter": "",
        "only_open": False,
        "status_choices": Edital.STATUS_CHOICES,
        "unique_orgaos": [],
        "total_count": 0,
        "search_suggestions": [],
    }


def home(request: HttpRequest) -> HttpResponse:
    """Home page - landing page with hero, stats, features, etc."""
    # Fetch active startups for Innovation Deck
    # Use ACTIVE_STARTUP_STATUSES (pre_incubacao, incubacao, graduada)
    active_startups = (
        Startup.objects.filter(status__in=ACTIVE_STARTUP_STATUSES)
        .only("id", "name", "logo", "category", "slug")
        .order_by("-submitted_on")[:12]
    )

    context = {
        "startups": active_startups,
        "partners": settings.PARTNERS,
    }
    return render(request, "home.html", context)


def ambientes_inovacao(request: HttpRequest) -> HttpResponse:
    """Ambientes de Inovação page - list of innovation environments"""
    return render(request, "ambientes_inovacao/index.html")


def startups_showcase(request: HttpRequest) -> HttpResponse:
    """Public startups showcase page - modern design with filters"""
    try:
        category_filter = request.GET.get("category", "").strip()
        search_query = request.GET.get("search", "").strip()

        base_queryset = (
            Startup.objects.select_related("edital", "proponente")
            .filter(proponente__isnull=False, status__in=ACTIVE_STARTUP_STATUSES)
            .only(
                "id",
                "name",
                "description",
                "category",
                "status",
                "submitted_on",
                "edital__id",
                "edital__titulo",
                "edital__slug",
                "proponente__id",
                "proponente__first_name",
                "proponente__last_name",
            )
        )

        if search_query:
            base_queryset = base_queryset.search(search_query)

        all_active_startups = Startup.objects.filter(
            proponente__isnull=False, status__in=ACTIVE_STARTUP_STATUSES
        )
        graduadas_count = all_active_startups.filter(status="graduada").count()
        stats = {
            "total_active": base_queryset.count(),
            "graduadas": graduadas_count,
        }

        startups = base_queryset
        if category_filter and category_filter != "all":
            startups = startups.filter(category=category_filter)

        startups = startups.order_by("-submitted_on")[:MAX_STARTUPS_DISPLAY]

        context = {
            "startups": startups,
            "category_filter": category_filter,
            "search_query": search_query,
            "stats": stats,
        }

        return render(request, "startups/index.html", context)

    except DatabaseError as e:
        logger.error(
            f"Erro ao carregar showcase de startups - erro: {str(e)}", exc_info=True
        )
        return render(request, "503.html", status=503)


class RateLimitedLoginView(LoginView):
    """Login view with rate limiting; uses existing registration/login.html template.

    Rate limiting is implemented using Django's cache framework directly,
    matching the fail-open pattern used by the custom @rate_limit decorator.
    This replaces the previous django-ratelimit dependency.
    """

    template_name = "registration/login.html"
    redirect_authenticated_user = True
    success_url = None  # use LOGIN_REDIRECT_URL from settings via RedirectURLMixin

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Apply rate limiting to POST requests before dispatch."""
        from ..decorators import get_client_ip
        from ..constants import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

        if request.method == "POST" and not getattr(settings, "TESTING", False):
            client_ip = get_client_ip(request)
            cache_key = f"rate_limit_login_{client_ip}"
            try:
                key_added = cache.add(cache_key, 1, RATE_LIMIT_WINDOW)
                if not key_added:
                    try:
                        current_count = cache.incr(cache_key)
                    except (ConnectionError, OSError, AttributeError, TypeError):
                        # Fail-open: allow request if cache is unavailable
                        logger.warning(
                            "Rate limit bypass due to cache error on login",
                            extra={"cache_key": cache_key, "client_ip": client_ip},
                        )
                        return super().dispatch(request, *args, **kwargs)
                    if current_count > RATE_LIMIT_REQUESTS:
                        logger.warning(
                            f"Rate limit excedido no login: ip={client_ip}, "
                            f"count={current_count}"
                        )
                        return HttpResponse(
                            "Muitas tentativas de login. Por favor, tente novamente em alguns instantes.",
                            status=429,
                        )
            except (ConnectionError, OSError, AttributeError, TypeError):
                # Fail-open: allow request if cache is unavailable
                logger.warning(
                    "Rate limit bypass due to cache error on login",
                    extra={"cache_key": cache_key, "client_ip": client_ip},
                )
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self) -> str:
        """
        Override to validate redirect URL and prevent open redirect attacks.
        Only allows redirects to internal URLs (same host).
        """
        from django.utils.http import url_has_allowed_host_and_scheme

        redirect_to = self.request.POST.get(
            self.redirect_field_name, self.request.GET.get(self.redirect_field_name, "")
        )
        # Validate the URL is safe (internal only)
        if redirect_to and url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return redirect_to
        return ""

    def get_success_url(self) -> str:
        url = self.get_redirect_url()
        if url:
            return url
        return getattr(settings, "LOGIN_REDIRECT_URL", None) or reverse(
            "dashboard_home"
        )


login_view = RateLimitedLoginView.as_view()


@rate_limit(key="ip", rate=3, window=3600, method="POST")
def register_view(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """User registration view with rate limiting to prevent abuse."""
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            logger.info(
                f"User registered successfully - username: {user.username}, "
                f"email: {user.email}, IP: {request.META.get('REMOTE_ADDR')}"
            )

            send_welcome_email_async(user.email, user.first_name or "")

            messages.success(request, "Conta criada com sucesso! Bem-vindo ao AgroHub!")
            return redirect("dashboard_home")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/register.html", {"form": form})


def index(request: HttpRequest) -> HttpResponse:
    """Landing page com todos os editais"""
    try:
        params = _parse_index_params(request)
        if params["use_cache"] and params["cache_key"]:
            cached = get_cached_response(params["cache_key"])
            if cached:
                return cached
        context = _get_index_context(request, params)
        template_name = _get_index_template_name(request)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        cache_ttl = getattr(settings, "EDITAIS_CACHE_TTL", CACHE_TTL_INDEX)
        rendered = render_to_string(template_name, context, request=request)
        if params["use_cache"] and params["cache_key"] and not is_ajax:
            cache_response(params["cache_key"], rendered, cache_ttl)
        return HttpResponse(rendered)
    except (DatabaseError, EmptyPage, PageNotAnInteger) as e:
        logger.error(
            "Erro ao carregar página de editais - IP: %s, erro: %s",
            request.META.get("REMOTE_ADDR"),
            e,
            exc_info=True,
        )
        context = _index_empty_context()
        template_name = _get_index_template_name(request)
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            messages.error(request, "Erro ao carregar editais. Tente novamente.")
        return render(request, template_name, context)


def edital_detail(
    request: HttpRequest, slug: Optional[str] = None, pk: Optional[int] = None
) -> HttpResponse:
    """
    Página de detalhes do edital - suporta slug ou PK.
    """
    identifier = slug if slug else f"pk_{pk}"
    cache_key = get_detail_cache_key("edital", identifier, request.user)

    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response

    try:
        if slug:
            edital = get_object_or_404(
                Edital.objects.with_related().with_prefetch(), slug=slug
            )
        elif pk:
            edital = get_object_or_404(
                Edital.objects.with_related().with_prefetch(), pk=pk
            )
        else:
            raise Http404("Edital não encontrado")

        if edital.status == "draft":
            if not request.user.is_authenticated or not request.user.is_staff:
                raise Http404("Edital não encontrado")

        valores = edital.valores.all()
        cronogramas = edital.cronogramas.all()
        mark_edital_fields_safe(edital)

        is_recent_update = False
        if edital.data_atualizacao:
            time_diff = timezone.now() - edital.data_atualizacao
            # Check if update was within the last day
            is_recent_update = time_diff.total_seconds() < SECONDS_PER_DAY

        context = {
            "edital": edital,
            "valores": valores,
            "cronogramas": cronogramas,
            "is_recent_update": is_recent_update,
        }

        rendered_content = render_to_string(
            "editais/detail.html", context, request=request
        )
        cache_response(cache_key, rendered_content, CACHE_TTL_15_MINUTES)
        return HttpResponse(rendered_content)
    except Http404:
        raise
    except (DatabaseError, ValidationError) as e:
        logger.error(f"Erro inesperado em edital_detail: {e}", exc_info=True)
        raise Http404("Erro ao carregar edital")


def edital_detail_redirect(
    request: HttpRequest, pk: int
) -> Union[HttpResponseRedirect, HttpResponse]:
    """
    Redireciona URLs baseadas em PK para URLs baseadas em slug.

    Redirecionamento permanente (301) para melhorar SEO e consistência de URLs.
    Se o slug não existir, exibe a página de detalhes usando PK.

    Args:
        request: HttpRequest
        pk: Primary key do edital

    Returns:
        HttpResponseRedirect: Redirecionamento permanente para URL com slug
        HttpResponse: Página de detalhes se slug não existir
    """
    edital = get_object_or_404(Edital, pk=pk)

    if edital.status == "draft":
        if not request.user.is_authenticated or not request.user.is_staff:
            raise Http404("Edital não encontrado")

    if edital.slug:
        return redirect("edital_detail_slug", slug=edital.slug, permanent=True)
    # Fallback to PK-based view if slug is missing (None or empty string)
    return edital_detail(request, pk=pk)


def health_check(request: HttpRequest) -> JsonResponse:
    """
    Endpoint de health check para monitoramento.

    Verifica o status do banco de dados e cache.

    Args:
        request: HttpRequest

    Returns:
        JsonResponse: Status do sistema
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        test_key = "health_check_test"
        cache.set(test_key, "ok", 10)
        cache_status = cache.get(test_key) == "ok"
        cache.delete(test_key)

        return JsonResponse(
            {
                "status": "healthy",
                "database": "ok",
                "cache": "ok" if cache_status else "error",
                "timestamp": timezone.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Health check falhou: {e}", exc_info=True)
        # Don't expose error details in production to prevent information disclosure
        error_message = str(e) if settings.DEBUG else "Internal server error"
        return JsonResponse(
            {
                "status": "unhealthy",
                "error": error_message,
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )


def startup_detail(
    request: HttpRequest, slug: Optional[str] = None, pk: Optional[int] = None
) -> HttpResponse:
    """
    Página de detalhes da startup - suporta slug ou PK.
    """
    identifier = slug if slug else f"pk_{pk}"
    cache_key = get_detail_cache_key("startup", identifier, request.user)

    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response

    try:
        qs = Startup.objects.select_related("proponente", "edital").prefetch_related(
            "tags"
        )
        if slug:
            startup = get_object_or_404(qs, slug=slug)
        elif pk:
            startup = get_object_or_404(qs, pk=pk)
        else:
            raise Http404("Startup não encontrada")

        context = {
            "startup": startup,
        }

        rendered_content = render_to_string(
            "startups/detail.html", context, request=request
        )
        cache_response(cache_key, rendered_content, CACHE_TTL_15_MINUTES)
        return HttpResponse(rendered_content)
    except Http404:
        raise
    except (DatabaseError, ValidationError) as e:
        logger.error(f"Erro ao carregar startup: {e}", exc_info=True)
        raise Http404("Erro ao carregar startup")


def startup_detail_redirect(
    request: HttpRequest, pk: int
) -> Union[HttpResponseRedirect, HttpResponse]:
    """
    Redireciona URLs baseadas em PK para URLs baseadas em slug.

    Redirecionamento permanente (301) para melhorar SEO e consistência de URLs.
    Se o slug não existir, exibe a página de detalhes usando PK.

    Args:
        request: HttpRequest
        pk: Primary key da startup

    Returns:
        HttpResponseRedirect: Redirecionamento permanente para URL com slug
        HttpResponse: Página de detalhes se slug não existir
    """
    startup = get_object_or_404(Startup, pk=pk)

    if startup.slug:
        return redirect("startup_detail_slug", slug=startup.slug, permanent=True)
    # Fallback to PK-based view if slug is missing (None or empty string)
    return startup_detail(request, pk=pk)
