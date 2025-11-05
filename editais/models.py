from django.contrib.auth.models import User
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

    # User tracking for activity log
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_editais',
        verbose_name='Criado por'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_editais',
        verbose_name='Atualizado por'
    )

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
        verbose_name = 'Edital'
        verbose_name_plural = 'Editais'
        indexes = [
            models.Index(fields=['-data_atualizacao'], name='idx_data_atualizacao'),
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['entidade_principal'], name='idx_entidade'),
            models.Index(fields=['numero_edital'], name='idx_numero'),
        ]

    def get_summary(self):
        """Return a short summary for list views"""
        if self.objetivo:
            return self.objetivo[:200] + '...' if len(self.objetivo) > 200 else self.objetivo
        return ''

    def is_open(self):
        """Check if edital is currently open"""
        return self.status == 'aberto'

    def is_closed(self):
        """Check if edital is closed"""
        return self.status == 'fechado'

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
        verbose_name = 'Cronograma'
        verbose_name_plural = 'Cronogramas'

    def __str__(self):
        return f'{self.edital.titulo} - {self.descricao}'


class EditalFavorite(models.Model):
    """User favorites/bookmarks for editais"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorited_editais')
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'edital')
        ordering = ['-created_at']
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'

    def __str__(self):
        return f'{self.user.username} - {self.edital.titulo}'

