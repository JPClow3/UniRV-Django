"""Autocomplete views for django-autocomplete-light (DAL).

Provides Select2-powered autocomplete endpoints for Tag and Edital models,
used in the admin and public-facing forms.
"""

from dal import autocomplete
from django.db.models import Q, QuerySet

from .models import Tag, Edital


class TagAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for :model:`editais.Tag`.

    Accessible to all authenticated users.  Results are ordered
    alphabetically and filtered by the user's typed query via
    ``icontains`` on the tag name.
    """

    def get_queryset(self) -> QuerySet:
        """Return filtered Tag queryset."""
        if not self.request.user.is_authenticated:
            return Tag.objects.none()

        qs: QuerySet = Tag.objects.all().order_by("name")

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class EditalAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for :model:`editais.Edital`.

    Accessible to all authenticated users.  Searches ``titulo`` and
    ``numero_edital`` via ``icontains``.
    """

    def get_queryset(self) -> QuerySet:
        """Return filtered Edital queryset."""
        if not self.request.user.is_authenticated:
            return Edital.objects.none()

        qs: QuerySet = Edital.objects.all().order_by("-data_atualizacao")

        if self.q:
            qs = qs.filter(
                Q(titulo__icontains=self.q) | Q(numero_edital__icontains=self.q)
            )

        return qs
