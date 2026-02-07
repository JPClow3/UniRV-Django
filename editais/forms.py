import os
from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from .models import Edital, Startup
from .utils import PHASE_CHOICES
from .constants import MAX_LOGO_FILE_SIZE


# Field-specific error messages for better UX
FIELD_ERROR_MESSAGES = {
    "required": {
        "default": "Este campo é obrigatório.",
        "email": "Por favor, informe seu e-mail.",
        "username": "Por favor, escolha um nome de usuário.",
        "password": "Por favor, crie uma senha.",
        "titulo": "Por favor, informe o título do edital.",
        "numero_edital": "Por favor, informe o número do edital.",
        "name": "Por favor, informe o nome da startup.",
        "description": "Por favor, forneça uma descrição.",
        "start_date": "Por favor, selecione a data de início.",
        "end_date": "Por favor, selecione a data de encerramento.",
        "url": "Por favor, informe a URL do edital.",
        "entidade_principal": "Por favor, informe a entidade responsável.",
        "first_name": "Por favor, informe seu nome.",
    },
    "invalid": {
        "default": "Valor inválido.",
        "email": "Por favor, informe um e-mail válido (ex: seu@email.com).",
        "url": "Por favor, informe uma URL válida (ex: https://exemplo.com).",
        "date": "Por favor, selecione uma data válida.",
    },
    "min_length": {
        "default": "Este campo deve ter pelo menos %(limit_value)d caracteres.",
        "password": "A senha deve ter pelo menos %(limit_value)d caracteres.",
        "username": "O nome de usuário deve ter pelo menos %(limit_value)d caracteres.",
    },
    "max_length": {
        "default": "Este campo deve ter no máximo %(limit_value)d caracteres.",
    },
}


def get_field_error_message(
    error_code: str, field_name: str, params: Optional[Dict] = None
) -> str:
    """Get a field-specific error message based on error code and field name."""
    error_category = FIELD_ERROR_MESSAGES.get(error_code, {})
    message = error_category.get(
        field_name, error_category.get("default", "Erro de validação.")
    )
    if params:
        try:
            message = message % params
        except (KeyError, TypeError):
            # If params don't match the message template, return the original message
            # This handles cases where the error message format differs from expected params
            pass
    return message


class UserRegistrationForm(UserCreationForm):
    """Form for user registration with field-specific error messages"""

    email = forms.EmailField(
        required=True,
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"placeholder": "seu@email.com", "autocomplete": "email"}
        ),
        error_messages={
            "required": "Por favor, informe seu e-mail.",
            "invalid": "Por favor, informe um e-mail válido (ex: seu@email.com).",
        },
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nome",
        widget=forms.TextInput(
            attrs={"placeholder": "Seu nome", "autocomplete": "given-name"}
        ),
        error_messages={
            "required": "Por favor, informe seu nome.",
            "max_length": "O nome deve ter no máximo 150 caracteres.",
        },
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={"placeholder": "Seu sobrenome", "autocomplete": "family-name"}
        ),
        error_messages={
            "max_length": "O sobrenome deve ter no máximo 150 caracteres.",
        },
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "nomeusuario", "autocomplete": "username"}
            ),
        }
        error_messages = {
            "username": {
                "required": "Por favor, escolha um nome de usuário.",
                "unique": "Este nome de usuário já está em uso.",
                "invalid": "Use apenas letras, números e @/./+/-/_.",
            },
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nome de usuário"
        self.fields["password1"].label = "Senha"
        self.fields["password2"].label = "Confirmar senha"
        self.fields["password1"].widget.attrs.update(
            {"placeholder": "••••••••", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "••••••••", "autocomplete": "new-password"}
        )
        # Update password field error messages
        self.fields["password1"].error_messages.update(
            {
                "required": "Por favor, crie uma senha.",
            }
        )
        self.fields["password2"].error_messages.update(
            {
                "required": "Por favor, confirme sua senha.",
            }
        )

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email")
        if email:
            # Check if email exists (race condition handled in save() via IntegrityError)
            if User.objects.filter(email=email).exists():
                raise ValidationError("Este e-mail já está cadastrado.")
        return email

    def save(self, commit: bool = True) -> User:
        """
        Save user with race condition handling for email uniqueness.

        RACE CONDITION HANDLING:
        Email uniqueness is checked in clean_email(), but between validation and save(),
        another request may register the same email. The IntegrityError catch here
        handles this race condition by providing a user-friendly error message.
        The transaction.atomic() wrapper ensures the save operation is atomic.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            try:
                with transaction.atomic():
                    user.save()
            except IntegrityError:
                # Handle race condition: if email was registered between check and save
                # This is an acceptable race condition pattern - catch and provide user feedback
                # Note: We don't parse the error string as it's database-backend dependent
                raise ValidationError(
                    {
                        "email": "Este e-mail já está cadastrado. Por favor, tente novamente."
                    }
                )
        return user


class EditalForm(forms.ModelForm):
    """Form for creating and editing Edital instances with field-specific error messages"""

    class Meta:
        model = Edital
        fields = [
            "numero_edital",
            "titulo",
            "url",
            "entidade_principal",
            "status",
            "start_date",
            "end_date",
            "analise",
            "objetivo",
            "etapas",
            "recursos",
            "itens_financiaveis",
            "criterios_elegibilidade",
            "criterios_avaliacao",
            "itens_essenciais_observacoes",
            "detalhes_unirv",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "analise": forms.Textarea(
                attrs={"rows": 12, "placeholder": "Análise do Edital"}
            ),
            "objetivo": forms.Textarea(attrs={"rows": 4}),
            "etapas": forms.Textarea(attrs={"rows": 4}),
            "recursos": forms.Textarea(attrs={"rows": 3}),
            "itens_financiaveis": forms.Textarea(attrs={"rows": 3}),
            "criterios_elegibilidade": forms.Textarea(attrs={"rows": 3}),
            "criterios_avaliacao": forms.Textarea(attrs={"rows": 3}),
            "itens_essenciais_observacoes": forms.Textarea(attrs={"rows": 3}),
            "detalhes_unirv": forms.Textarea(attrs={"rows": 3}),
        }
        error_messages = {
            "numero_edital": {
                "required": "Por favor, informe o número do edital (ex: 001/2024).",
                "max_length": "O número do edital deve ter no máximo 100 caracteres.",
            },
            "titulo": {
                "required": "Por favor, informe o título do edital.",
                "max_length": "O título deve ter no máximo 500 caracteres.",
            },
            "url": {
                "required": "Por favor, informe a URL do edital.",
                "invalid": "Por favor, informe uma URL válida (ex: https://exemplo.com/edital).",
            },
            "entidade_principal": {
                "required": "Por favor, informe a entidade responsável pelo edital.",
            },
            "status": {
                "required": "Por favor, selecione o status do edital.",
                "invalid_choice": "Por favor, selecione um status válido.",
            },
            "start_date": {
                "required": "Por favor, selecione a data de abertura.",
                "invalid": "Por favor, informe uma data válida.",
            },
            "end_date": {
                "invalid": "Por favor, informe uma data válida.",
            },
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs["aria-required"] = "true"
            # Build aria-describedby referencing helptext and/or error elements
            if self.auto_id:
                field_id = self.auto_id % field_name
            else:
                field_id = f"id_{field_name}"
            describedby_ids = []
            if field.help_text:
                describedby_ids.append(f"{field_id}_helptext")
            if self.is_bound and self.errors.get(field_name):
                describedby_ids.append(f"{field_id}_error")
                field.widget.attrs["aria-invalid"] = "true"
            if describedby_ids:
                field.widget.attrs["aria-describedby"] = " ".join(describedby_ids)

    def clean(self) -> Dict[str, Any]:
        """Validação de datas: end_date deve ser posterior ou igual a start_date"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise ValidationError(
                {
                    "end_date": "A data de encerramento deve ser posterior à data de abertura."
                }
            )
        # Allow same dates (end_date == start_date is valid)

        return cleaned_data


class StartupForm(forms.ModelForm):
    """Form for creating and editing Startup instances with field-specific error messages"""

    class Meta:
        model = Startup
        fields = [
            "name",
            "description",
            "category",
            "edital",
            "contato",
            "website",
            "incubacao_start_date",
            "tags",
            "logo",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ex: AgroTech Solutions",
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Descreva a startup, problema que resolve e solução proposta...",
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg resize-none",
                }
            ),
            "category": forms.Select(
                attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded-lg"}
            ),
            "edital": forms.Select(
                attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded-lg"}
            ),
            "contato": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Email, telefone, website, etc.",
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg resize-none",
                }
            ),
            "logo": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/gif,image/svg+xml",
                    "class": "hidden",
                }
            ),
            "status": forms.Select(
                attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded-lg"}
            ),
        }
        error_messages = {
            "name": {
                "required": "Por favor, informe o nome da sua startup.",
                "max_length": "O nome da startup deve ter no máximo 200 caracteres.",
                "unique": "Já existe uma startup com este nome.",
            },
            "description": {
                "required": "Por favor, descreva sua startup.",
            },
            "category": {
                "required": "Por favor, selecione uma categoria.",
                "invalid_choice": "Por favor, selecione uma categoria válida.",
            },
            "website": {
                "invalid": "Por favor, informe uma URL válida (ex: https://suastartup.com).",
            },
            "incubacao_start_date": {
                "invalid": "Por favor, informe uma data válida para início da incubação.",
            },
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Make edital optional and add empty option
        self.fields["edital"].required = False
        self.fields["edital"].queryset = Edital.objects.all().order_by(
            "-data_atualizacao"
        )
        self.fields["edital"].empty_label = "Selecione um edital (opcional)"

        # Make optional fields not required
        self.fields["logo"].required = False
        self.fields["website"].required = False
        self.fields["incubacao_start_date"].required = False
        self.fields["tags"].required = False

        # Import Tag model for tags queryset
        from .models import Tag

        self.fields["tags"].queryset = Tag.objects.all().order_by("name")

        # Phase (maturity) – symbolic, not pass/fail. Use phase labels instead of status labels.
        self.fields["status"].label = "Fase de maturidade"
        self.fields["status"].help_text = (
            "Estágio da startup (ideação, MVP, escala). Indicador de maturidade, não de aprovação."
        )
        self.fields["status"].choices = PHASE_CHOICES

        # Add aria labels for accessibility
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs["aria-required"] = "true"
            # Build aria-describedby referencing helptext and/or error elements
            if self.auto_id:
                field_id = self.auto_id % field_name
            else:
                field_id = f"id_{field_name}"
            describedby_ids = []
            if field.help_text:
                describedby_ids.append(f"{field_id}_helptext")
            if self.is_bound and self.errors.get(field_name):
                describedby_ids.append(f"{field_id}_error")
                field.widget.attrs["aria-invalid"] = "true"
            if describedby_ids:
                field.widget.attrs["aria-describedby"] = " ".join(describedby_ids)

    def clean_logo(self) -> Optional[Any]:
        """Validate logo file"""
        logo = self.cleaned_data.get("logo")

        # If no new logo is uploaded, Django will automatically keep the existing one
        # (for ImageField/FileField, if no file is provided, existing file is preserved)
        # So we only need to validate if a new file is actually uploaded
        if logo:
            # Check file size (5MB limit)
            if logo.size > MAX_LOGO_FILE_SIZE:
                raise ValidationError(
                    "O arquivo de logo é muito grande. Tamanho máximo: 5MB."
                )

            # Check file extension
            ext = os.path.splitext(logo.name)[1].lower()
            allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".svgz"]
            if ext not in allowed_extensions:
                raise ValidationError(
                    f'Formato de arquivo não permitido. Use: {", ".join(allowed_extensions)}'
                )

        return logo
