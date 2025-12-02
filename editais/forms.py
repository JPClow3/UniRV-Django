from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from .models import Edital


class TailwindFormMixin:
    """
    Aplica classes padrão do Tailwind aos campos do formulário para evitar repetição.
    """
    input_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    textarea_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    select_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    date_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'

    def apply_tailwind_styles(self) -> None:
        for field in self.fields.values():
            base_class = self._get_base_class(field.widget)
            if not base_class:
                continue
            existing = field.widget.attrs.get('class', '').strip()
            if existing:
                field.widget.attrs['class'] = f"{base_class} {existing}".strip()
            else:
                field.widget.attrs['class'] = base_class

    def _get_base_class(self, widget: forms.Widget) -> Optional[str]:
        if isinstance(widget, forms.CheckboxInput):
            return None
        if isinstance(widget, forms.Textarea):
            return self.textarea_class
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            return self.select_class
        if isinstance(widget, (forms.DateInput, forms.DateTimeInput, forms.TimeInput)):
            return self.date_class
        return self.input_class


class UserRegistrationForm(TailwindFormMixin, UserCreationForm):
    """Form for user registration"""
    input_class = 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent'
    date_class = input_class
    email = forms.EmailField(
        required=True,
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'placeholder': 'seu@email.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Nome',
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu nome',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Sobrenome',
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu sobrenome',
            'autocomplete': 'family-name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'nomeusuario',
                'autocomplete': 'username'
            }),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nome de usuário'
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirmar senha'
        self.fields['password1'].widget.attrs.update({
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
        # Aplicar classes Tailwind depois de definir placeholders/autocomplete
        self.apply_tailwind_styles()

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email')
        if email:
            # Check if email exists (race condition handled in save() via IntegrityError)
            if User.objects.filter(email=email).exists():
                raise ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            try:
                with transaction.atomic():
                    user.save()
            except IntegrityError as e:
                # Handle race condition: if email was registered between check and save
                if 'email' in str(e).lower() or 'unique' in str(e).lower():
                    raise ValidationError({
                        'email': 'Este e-mail já está cadastrado. Por favor, tente novamente.'
                    })
                raise
        return user


class EditalForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Edital
        fields = [
            'numero_edital', 'titulo', 'url', 'entidade_principal', 'status',
            'start_date', 'end_date',
            'analise',
            'objetivo', 'etapas', 'recursos', 'itens_financiaveis',
            'criterios_elegibilidade', 'criterios_avaliacao',
            'itens_essenciais_observacoes', 'detalhes_unirv'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'analise': forms.Textarea(attrs={'rows': 12, 'placeholder': 'Análise do Edital'}),
            'objetivo': forms.Textarea(attrs={'rows': 4}),
            'etapas': forms.Textarea(attrs={'rows': 4}),
            'recursos': forms.Textarea(attrs={'rows': 3}),
            'itens_financiaveis': forms.Textarea(attrs={'rows': 3}),
            'criterios_elegibilidade': forms.Textarea(attrs={'rows': 3}),
            'criterios_avaliacao': forms.Textarea(attrs={'rows': 3}),
            'itens_essenciais_observacoes': forms.Textarea(attrs={'rows': 3}),
            'detalhes_unirv': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.apply_tailwind_styles()

    def clean(self) -> Dict[str, Any]:
        """Validação de datas: end_date deve ser posterior a start_date"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError({
                'end_date': 'A data de encerramento deve ser posterior à data de abertura.'
            })
        
        return cleaned_data
