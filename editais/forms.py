from typing import Any, Dict
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Edital


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(
        required=True,
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent',
            'placeholder': 'seu@email.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Nome',
        widget=forms.TextInput(attrs={
            'class': 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent',
            'placeholder': 'Seu nome',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Sobrenome',
        widget=forms.TextInput(attrs={
            'class': 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent',
            'placeholder': 'Seu sobrenome',
            'autocomplete': 'family-name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent',
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
            'class': 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'h-11 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
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
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'required': True}),
            'numero_edital': forms.TextInput(attrs={'class': 'form-control'}),
            'entidade_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'analise': forms.Textarea(attrs={'class': 'form-control', 'rows': 12, 'placeholder': 'Análise do Edital'}),
            'objetivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'etapas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recursos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'itens_financiaveis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'criterios_elegibilidade': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'criterios_avaliacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'itens_essenciais_observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'detalhes_unirv': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

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
