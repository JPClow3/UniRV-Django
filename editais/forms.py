from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from .models import Edital


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
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

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email')
        if email:
            # Check if email exists (race condition handled in save() via IntegrityError)
            if User.objects.filter(email=email).exists():
                raise ValidationError('Este e-mail já está cadastrado.')
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
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            try:
                with transaction.atomic():
                    user.save()
            except IntegrityError:
                # Handle race condition: if email was registered between check and save
                # This is an acceptable race condition pattern - catch and provide user feedback
                # Note: We don't parse the error string as it's database-backend dependent
                raise ValidationError({
                    'email': 'Este e-mail já está cadastrado. Por favor, tente novamente.'
                })
        return user


class EditalForm(forms.ModelForm):
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
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['aria-required'] = 'true'
            if self.is_bound and self.errors.get(field_name):
                # Generate field ID using form's auto_id format
                # auto_id is a form-level property, not field-level
                if self.auto_id:
                    field_id = self.auto_id % field_name
                else:
                    field_id = f'id_{field_name}'
                field.widget.attrs['aria-describedby'] = f'{field_id}_error'
                field.widget.attrs['aria-invalid'] = 'true'

    def clean(self) -> Dict[str, Any]:
        """Validação de datas: end_date deve ser posterior ou igual a start_date"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError({
                'end_date': 'A data de encerramento deve ser posterior à data de abertura.'
            })
        # Allow same dates (end_date == start_date is valid)
        
        return cleaned_data
