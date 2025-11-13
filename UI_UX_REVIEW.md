# UI/UX Code Review - AgroHub UniRV

**Data da Revisão**: 2025-01-XX  
**Escopo**: Templates, CSS, JavaScript, e interações do usuário

---

## 🔴 Críticos (Bugs e Problemas Graves)

### 1. **Página de Exclusão Muito Simples**
**Arquivo**: `templates/editais/delete.html`

**Problema**: A página de exclusão é muito básica e não segue o padrão visual do resto do site.

**Impacto**: UX inconsistente, falta de confirmação visual adequada.

**Solução**:
```html
{% extends 'base.html' %}
{% block title %}Excluir Edital - AgroHub{% endblock %}
{% block content %}
<div class="form-page">
    <div class="form-header">
        <h1>Confirmar Exclusão</h1>
        <p class="form-subtitle">Esta ação não pode ser desfeita</p>
    </div>
    
    <div class="delete-warning" role="alert">
        <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
        <p>Tem certeza que deseja excluir o edital <strong>"{{ edital.titulo }}"</strong>?</p>
        <p class="warning-text">Todos os dados relacionados serão permanentemente removidos.</p>
    </div>
    
    <form method="post" class="delete-form">
        {% csrf_token %}
        <div class="form-actions">
            <button type="submit" class="btn btn-danger">
                <i class="fas fa-trash"></i> Confirmar Exclusão
            </button>
            <a href="{% url 'edital_detail' edital.pk %}" class="btn btn-secondary">
                <i class="fas fa-times"></i> Cancelar
            </a>
        </div>
    </form>
</div>
{% endblock %}
```

### 2. **Mensagens Django Não Convertidas para Toast**
**Arquivo**: `templates/base.html`, `static/js/main.js`

**Problema**: As mensagens Django são exibidas como alertas simples, mas o sistema de toast já existe no JavaScript e não está sendo usado.

**Impacto**: Inconsistência visual, mensagens não aparecem no canto inferior direito como especificado.

**Solução**: Adicionar script no `base.html` para converter mensagens Django em toasts:
```javascript
// No final de base.html, antes de </body>
{% if messages %}
<script>
    {% for message in messages %}
        showToast('{{ message|escapejs }}', '{{ message.tags }}');
    {% endfor %}
</script>
{% endif %}
```

### 3. **Filtros Ativos Não Preservam Todos os Parâmetros**
**Arquivo**: `templates/editais/index.html` (linhas 113-137)

**Problema**: Ao remover um filtro, outros filtros (como `start_date`, `end_date`, `only_open`) são perdidos.

**Impacto**: UX frustrante - usuário perde filtros ao tentar remover um.

**Solução**: Usar JavaScript para construir URLs corretamente ou usar template tags customizadas.

### 4. **Paginação Não Preserva Todos os Filtros**
**Arquivo**: `templates/editais/index.html` (linhas 225-247)

**Problema**: A paginação só preserva `search` e `status`, mas não `start_date`, `end_date`, `only_open`.

**Impacto**: Ao navegar entre páginas, filtros de data são perdidos.

**Solução**: Criar template tag ou usar JavaScript para preservar todos os parâmetros.

---

## 🟡 Importantes (Melhorias de UX)

### 5. **Falta Indicador de "Prazo Próximo"**
**Arquivo**: `templates/editais/index.html`, `templates/editais/detail.html`

**Problema**: A especificação menciona aviso "prazo próximo" para editais com prazo nos últimos 7 dias, mas não está implementado.

**Impacto**: Funcionalidade especificada não implementada.

**Solução**: Adicionar lógica no template:
```django
{% if edital.end_date %}
    {% with days_remaining=edital.end_date|timeuntil %}
        {% if edital.end_date|days_until <= 7 and edital.end_date|days_until >= 0 %}
            <span class="deadline-warning" aria-label="Prazo próximo">
                <i class="fas fa-clock"></i> Prazo próximo
            </span>
        {% endif %}
    {% endwith %}
{% endif %}
```

### 6. **Falta Feedback Visual de Loading no Submit do Formulário**
**Arquivo**: `templates/editais/create.html`, `templates/editais/update.html`

**Problema**: O JavaScript tem lógica de loading, mas o botão não mostra feedback visual adequado.

**Impacto**: Usuário não sabe se o formulário está sendo processado.

**Solução**: Melhorar o JavaScript para mostrar spinner e desabilitar botão:
```javascript
// Já existe no main.js, mas precisa melhorar
submitBtn.classList.add('loading');
submitBtn.disabled = true;
submitBtn.querySelector('.btn-text').style.display = 'none';
submitBtn.querySelector('.btn-loading').style.display = 'inline-block';
```

### 7. **Falta Breadcrumb Navigation**
**Arquivo**: Todos os templates

**Problema**: Não há breadcrumbs para navegação contextual.

**Impacto**: Usuário perde contexto de onde está no site.

**Solução**: Adicionar breadcrumbs:
```django
<nav class="breadcrumb" aria-label="Breadcrumb">
    <ol>
        <li><a href="{% url 'editais_index' %}">Editais</a></li>
        {% if edital %}
            <li aria-current="page">{{ edital.titulo|truncatewords:5 }}</li>
        {% else %}
            <li aria-current="page">{% block breadcrumb_current %}{% endblock %}</li>
        {% endif %}
    </ol>
</nav>
```

### 8. **Cards de Edital Não Mostram Data de Encerramento**
**Arquivo**: `templates/editais/index.html` (linha 165-175)

**Problema**: Apenas data de abertura é mostrada, mas data de encerramento é mais importante.

**Impacto**: Usuário não vê quando o edital fecha.

**Solução**: Mostrar ambas as datas ou priorizar end_date:
```django
<small class="end-date">
    <i class="fas fa-calendar-times" aria-hidden="true"></i>
    <time datetime="{{ edital.end_date|date:'Y-m-d' }}">
        {% if edital.end_date %}
            Encerra: {{ edital.end_date|date:"d/m/Y" }}
        {% else %}
            Sem data de encerramento
        {% endif %}
    </time>
</small>
```

### 9. **Falta Validação de Datas no Frontend**
**Arquivo**: `templates/editais/create.html`, `templates/editais/update.html`

**Problema**: Validação de datas (end_date > start_date) só acontece no backend.

**Impacto**: Usuário só descobre erro após submit.

**Solução**: Adicionar validação JavaScript:
```javascript
const startDateInput = document.getElementById('id_start_date');
const endDateInput = document.getElementById('id_end_date');

function validateDates() {
    if (startDateInput.value && endDateInput.value) {
        const start = new Date(startDateInput.value);
        const end = new Date(endDateInput.value);
        if (end < start) {
            endDateInput.setCustomValidity('Data de encerramento deve ser posterior à data de abertura');
            return false;
        }
    }
    endDateInput.setCustomValidity('');
    return true;
}

startDateInput.addEventListener('change', validateDates);
endDateInput.addEventListener('change', validateDates);
```

### 10. **Falta Indicador de Campos Obrigatórios Mais Visível**
**Arquivo**: `templates/editais/create.html`, `templates/editais/update.html`

**Problema**: Apenas asterisco (*) indica campos obrigatórios, pode não ser óbvio.

**Impacto**: Usuário pode não perceber campos obrigatórios.

**Solução**: Adicionar texto explicativo no topo do formulário:
```django
<div class="form-help-text">
    <i class="fas fa-info-circle"></i>
    Campos marcados com <span class="required-mark">*</span> são obrigatórios
</div>
```

---

## 🟢 Melhorias (Polimento e Acessibilidade)

### 11. **Console.log em Produção**
**Arquivo**: `static/js/main.js` (linhas 997-1002)

**Problema**: Console.log statements deixados no código de produção.

**Impacto**: Poluição do console, possível vazamento de informações.

**Solução**: Remover ou usar condicional:
```javascript
if (process.env.NODE_ENV !== 'production') {
    console.log('✓ Back to top button initialized');
    // ...
}
```

### 12. **Falta Tratamento de Erro para Busca AJAX**
**Arquivo**: `static/js/main.js` (linha 110)

**Problema**: Erro é logado no console, mas usuário não vê feedback visual adequado.

**Impacto**: Usuário não sabe que a busca falhou.

**Solução**: Já existe `showToast` no catch, mas verificar se está funcionando corretamente.

### 13. **Falta Aria-Labels em Alguns Elementos Interativos**
**Arquivo**: Vários templates

**Problema**: Alguns botões e links não têm aria-labels adequados.

**Impacto**: Acessibilidade reduzida para leitores de tela.

**Solução**: Revisar e adicionar aria-labels onde faltam.

### 14. **Falta Feedback de Sucesso Após Ações**
**Arquivo**: `editais/views.py`

**Problema**: Mensagens de sucesso são adicionadas, mas podem não estar sendo exibidas corretamente.

**Impacto**: Usuário não tem confirmação visual de ações bem-sucedidas.

**Solução**: Verificar se mensagens estão sendo exibidas e converter para toast.

### 15. **Falta Skeleton Loading na Primeira Carga**
**Arquivo**: `templates/editais/index.html`

**Problema**: Skeleton loading só aparece em buscas AJAX, não na primeira carga.

**Impacto**: Página pode parecer "travada" durante carregamento inicial.

**Solução**: Adicionar skeleton loading inicial no template.

### 16. **Falta Tooltip/Help Text em Filtros**
**Arquivo**: `templates/editais/index.html`

**Problema**: Filtros não têm explicação do que fazem.

**Impacto**: Usuário pode não entender como usar os filtros.

**Solução**: Adicionar tooltips ou help text:
```django
<div class="filter-group">
    <label for="status-filter" class="filter-label">
        Filtrar por status
        <i class="fas fa-question-circle" 
           data-tooltip="Filtre editais por status (aberto, fechado, etc.)"
           aria-label="Ajuda sobre filtro de status"></i>
    </label>
    ...
</div>
```

### 17. **Falta Indicador de "Nenhum Resultado" Mais Amigável**
**Arquivo**: `templates/editais/index.html` (linha 189-221)

**Problema**: Estado vazio existe, mas pode ser mais visual e útil.

**Impacto**: UX pode ser melhorada com ilustrações ou sugestões.

**Solução**: Melhorar o empty state com ilustração e sugestões mais específicas.

### 18. **Falta Animações de Transição Suaves**
**Arquivo**: CSS geral

**Problema**: Algumas transições podem ser mais suaves.

**Impacto**: Experiência menos polida.

**Solução**: Adicionar transições CSS onde apropriado.

### 19. **Falta Responsividade em Alguns Elementos**
**Arquivo**: CSS geral

**Problema**: Alguns elementos podem não estar totalmente responsivos.

**Impacto**: Experiência ruim em dispositivos móveis.

**Solução**: Revisar e melhorar media queries.

### 20. **Falta Feedback de "Salvando..." no Autosave**
**Arquivo**: `static/js/main.js` (linha 465)

**Problema**: Autosave existe mas feedback visual pode ser melhor.

**Impacto**: Usuário pode não perceber que rascunho foi salvo.

**Solução**: Melhorar indicador de autosave.

---

## 📋 Dead Code e Limpeza

### 21. **Código de Favoritos Removido Mas Ainda Presente**
**Arquivo**: `static/js/main.js` (linhas 536-577)

**Problema**: Código para remover favoritos ainda está presente, mas favoritos já foram removidos.

**Impacto**: Código desnecessário aumenta tamanho do bundle.

**Solução**: Remover completamente o código de favoritos.

### 22. **Comentários e Código Não Utilizado**
**Arquivo**: Vários

**Problema**: Pode haver código comentado ou não utilizado.

**Impacto**: Confusão e manutenção mais difícil.

**Solução**: Revisar e remover código não utilizado.

---

## 🎨 Melhorias de Design

### 23. **Consistência de Cores e Espaçamento**
**Arquivo**: `static/css/style.css`

**Problema**: Verificar se há inconsistências em cores e espaçamentos.

**Impacto**: Design menos profissional.

**Solução**: Criar design system com variáveis CSS consistentes.

### 24. **Hierarquia Visual**
**Arquivo**: Templates e CSS

**Problema**: Verificar se hierarquia visual está clara.

**Impacto**: Usuário pode ter dificuldade em entender importância dos elementos.

**Solução**: Revisar tipografia, tamanhos e pesos.

---

## 🔧 Melhorias Técnicas

### 25. **Otimização de Imagens**
**Arquivo**: `static/img/`

**Problema**: Verificar se imagens estão otimizadas.

**Impacto**: Performance ruim, especialmente em mobile.

**Solução**: Otimizar imagens e usar formatos modernos (WebP).

### 26. **Lazy Loading de Imagens**
**Arquivo**: Templates

**Problema**: Imagens podem não estar com lazy loading.

**Impacto**: Performance inicial ruim.

**Solução**: Adicionar `loading="lazy"` em imagens.

### 27. **Cache de Assets**
**Arquivo**: Settings

**Problema**: Verificar se cache de assets está configurado.

**Impacto**: Performance ruim em requisições repetidas.

**Solução**: Configurar cache headers adequados.

---

## 📊 Priorização

### Alta Prioridade (Implementar Imediatamente)
1. ✅ Mensagens Django para Toast (item 2)
2. ✅ Página de Exclusão Melhorada (item 1)
3. ✅ Preservar Filtros na Paginação (item 4)
4. ✅ Indicador de Prazo Próximo (item 5)

### Média Prioridade (Próxima Sprint)
5. ✅ Validação Frontend de Datas (item 9)
6. ✅ Breadcrumb Navigation (item 7)
7. ✅ Feedback de Loading (item 6)
8. ✅ Data de Encerramento nos Cards (item 8)

### Baixa Prioridade (Backlog)
9. ✅ Remover Dead Code (item 21)
10. ✅ Melhorias de Acessibilidade (item 13)
11. ✅ Otimizações de Performance (itens 25-27)

---

## 📝 Notas Finais

- A base do sistema está sólida
- Acessibilidade está bem implementada na maioria dos lugares
- JavaScript está bem estruturado
- Faltam alguns polimentos e melhorias de UX
- Algumas funcionalidades especificadas não foram implementadas

**Recomendação**: Focar nas melhorias de Alta Prioridade primeiro, depois partir para as de Média Prioridade.

