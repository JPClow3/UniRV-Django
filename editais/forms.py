from django import forms
from .models import Edital


class EditalForm(forms.ModelForm):
    class Meta:
        model = Edital
        fields = [
            'numero_edital', 'titulo', 'url', 'entidade_principal', 'status',
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
