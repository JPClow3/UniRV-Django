from django import forms
from django.core.exceptions import ValidationError
from .models import Edital


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

    def clean(self):
        """Validação de datas: end_date deve ser posterior a start_date"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError({
                'end_date': 'A data de encerramento deve ser posterior à data de abertura.'
            })
        
        return cleaned_data
