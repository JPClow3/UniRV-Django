from django.db import models
from django.urls import reverse


class Edital(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado'),
        ('em_andamento', 'Em Andamento'),
    ]

    numero_edital = models.CharField(max_length=100, blank=True, null=True)
    titulo = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    entidade_principal = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    # Conteúdo
    analise = models.TextField(blank=True)  # Nova seção: Análise do Edital
    objetivo = models.TextField(blank=True)
    etapas = models.TextField(blank=True)
    recursos = models.TextField(blank=True)
    itens_financiaveis = models.TextField(blank=True)
    criterios_elegibilidade = models.TextField(blank=True)
    criterios_avaliacao = models.TextField(blank=True)
    itens_essenciais_observacoes = models.TextField(blank=True)
    detalhes_unirv = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_atualizacao']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('edital_detail', kwargs={'pk': self.pk})


class EditalValor(models.Model):
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='valores')
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    moeda = models.CharField(max_length=10, default='BRL')

    def __str__(self):
        return f'{self.edital.titulo} - {self.valor_total} {self.moeda}'


class Cronograma(models.Model):
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='cronogramas')
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    descricao = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['data_inicio']

    def __str__(self):
        return f'{self.edital.titulo} - {self.descricao}'
