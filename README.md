# UniRV Django - AgroHub

Sistema de gerenciamento de editais de fomento para o AgroHub UniRV.

**Status do Projeto**: ✅ **95% Completo** - Pronto para homologação

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Setup Rápido](#-setup-rápido)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Testes](#-testes)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Segurança](#-segurança)
- [Deploy](#-deploy)
- [Contribuindo](#-contribuindo)

---

## ✨ Funcionalidades

### Funcionalidades Principais

- ✅ **Listagem de Editais**: Busca, filtros por status/data, paginação (12 itens por página)
- ✅ **Detalhes do Edital**: Visualização completa com cronogramas e valores
- ✅ **URLs Amigáveis**: URLs baseadas em slug com redirecionamento automático de URLs antigas
- ✅ **CRUD Completo**: Criar, editar e excluir editais (restrito a usuários `is_staff`)
- ✅ **Exportação CSV**: Exportar editais filtrados para CSV (restrito a usuários `is_staff`)
- ✅ **Dashboard Administrativo**: Estatísticas, atividade recente e prazos próximos
- ✅ **Histórico de Alterações**: Rastreamento completo de mudanças em editais
- ✅ **Notificações por Email**: Alertas para prazos próximos (management command)
- ✅ **Atualização Automática de Status**: Comando para atualizar status baseado em datas

### Recursos de Segurança

- ✅ **Sanitização de HTML**: Prevenção de XSS em views web e Django Admin
- ✅ **Controle de Acesso**: Operações administrativas restritas a usuários `is_staff`
- ✅ **Validação de Dados**: Validação de datas e campos obrigatórios
- ✅ **Headers de Segurança**: Configurados para produção

### Recursos de UX/UI

- ✅ **Design Responsivo**: Interface adaptável para mobile e desktop
- ✅ **Notificações Toast**: Feedback visual para ações do usuário
- ✅ **Breadcrumbs**: Navegação contextual
- ✅ **Indicador de Prazo Próximo**: Alerta visual para editais com prazo nos próximos 7 dias
- ✅ **Filtros Preservados**: Filtros mantidos durante paginação
- ✅ **Acessibilidade**: Suporte a leitores de tela e navegação por teclado

---

## 🚀 Setup Rápido

### Pré-requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Git

### 1. Clone o repositório

```bash
git clone <repository-url>
cd UniRV-Django
```

### 2. Crie e ative o ambiente virtual

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

**IMPORTANTE:** Copie o arquivo `.env.example` para `.env` e configure as variáveis:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edite o arquivo `.env` e configure as variáveis necessárias (veja seção [Configuração](#-configuração)).

#### Gerando uma SECRET_KEY segura

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Execute as migrações

```bash
python manage.py migrate
```

### 6. Crie um superusuário

```bash
python manage.py createsuperuser
```

Siga as instruções para criar um usuário administrador.

### 7. (Opcional) Popular o banco com dados de exemplo

```bash
python manage.py seed_editais
```

### 8. Inicie o servidor

```bash
python manage.py runserver
```

Acesse: <http://127.0.0.1:8000/>

---

## ⚙️ Configuração

### Variáveis de Ambiente

O projeto usa variáveis de ambiente para configuração. Veja `.env.example` para referência completa.

#### Variáveis Obrigatórias

- `SECRET_KEY`: Chave secreta do Django (gerar com comando acima)
- `DJANGO_DEBUG`: `True` para desenvolvimento, `False` para produção
- `ALLOWED_HOSTS`: Domínios permitidos (separados por vírgula)

### Variáveis Opcionais

- `EMAIL_BACKEND`: Backend de email (padrão: `console` para desenvolvimento)
- `EMAIL_HOST`: Servidor SMTP
- `EMAIL_PORT`: Porta SMTP (padrão: 587)
- `EMAIL_USE_TLS`: Usar TLS (padrão: `True`)
- `EMAIL_HOST_USER`: Usuário SMTP
- `EMAIL_HOST_PASSWORD`: Senha SMTP
- `DEFAULT_FROM_EMAIL`: Email remetente padrão
- `SITE_URL`: URL base do site (para links em emails)
- `DJANGO_LOG_LEVEL`: Nível de log (padrão: `INFO`)

### Configurações do Django

As principais configurações estão em `UniRV_Django/settings.py`:

- **Idioma**: Português (pt-BR)
- **Fuso Horário**: America/Sao_Paulo
- **Paginação**: 12 itens por página
- **Cache**: Configurado para produção
- **Logging**: Estruturado com handlers para console e arquivo

---

## 📖 Uso

### Acessando o Sistema

1. **Página Inicial**: `/editais/` - Lista todos os editais públicos
2. **Detalhes**: `/editais/edital/<slug>/` - Visualizar edital específico
3. **Admin Django**: `/admin/` - Interface administrativa completa
4. **Dashboard**: `/editais/dashboard/` - Dashboard administrativo (requer `is_staff`)

### Operações Administrativas

Todas as operações administrativas (criar, editar, excluir, exportar) requerem que o usuário seja `is_staff`.

#### Criar Edital

1. Faça login como usuário `is_staff`
2. Acesse "Cadastrar Edital" no menu
3. Preencha os campos obrigatórios (título, URL)
4. Configure datas de abertura e encerramento
5. Salve o edital

#### Editar Edital

1. Acesse o edital que deseja editar
2. Clique em "Editar" (visível apenas para `is_staff`)
3. Faça as alterações necessárias
4. Salve as alterações

#### Exportar Editais

1. Acesse a página de listagem
2. Aplique filtros se necessário
3. Clique em "EXPORTAR CSV" no menu (visível apenas para `is_staff`)
4. O arquivo CSV será baixado com os editais filtrados

### Management Commands

#### Atualizar Status dos Editais

Atualiza automaticamente o status dos editais baseado nas datas:

```bash
python manage.py update_edital_status
```

**Opções:**

- `--dry-run`: Executa sem fazer alterações (apenas mostra o que seria alterado)
- `--verbose`: Mostra informações detalhadas sobre cada edital atualizado

**Configuração para execução automática (cron/task scheduler):**

```bash
# Linux (crontab -e)
0 0 * * * cd /path/to/UniRV-Django && /path/to/venv/bin/python manage.py update_edital_status

# Windows Task Scheduler
# Criar tarefa agendada para executar diariamente
```

#### Enviar Notificações de Prazo

Envia emails para staff sobre editais com prazos próximos:

```bash
python manage.py send_deadline_notifications
```

**Opções:**

- `--days`: Número de dias para considerar "prazo próximo" (padrão: 7)
- `--dry-run`: Executa sem enviar emails

---

## 🧪 Testes

### Executar Testes

```bash
# Executar todos os testes
python manage.py test editais

# Executar testes específicos
python manage.py test editais.tests.EditaisCrudTest
python manage.py test editais.tests.test_permissions
python manage.py test editais.tests.test_admin
```

### Cobertura de Testes

**Status Atual**: 69% (Meta: 85%)

Para verificar a cobertura:

```bash
# Instalar coverage (se ainda não instalado)
pip install coverage

# Executar testes com cobertura
coverage run --source='editais' --omit='*/migrations/*' manage.py test editais

# Ver relatório
coverage report

# Gerar relatório HTML
coverage html
# Abrir htmlcov/index.html no navegador
```

**Testes Implementados** (34+ testes):

- ✅ CRUD de editais (7 testes)
- ✅ Busca e filtros (6 testes)
- ✅ Detalhes e redirecionamento (4 testes)
- ✅ Modelos (slug, validação, status) (5 testes)
- ✅ Formulários (6 testes)
- ✅ Permissões (12 testes)
- ✅ Exportação CSV (7 testes)
- ✅ Management commands (8 testes)
- ✅ Admin interface (15 testes)

**Áreas que precisam de mais testes** (para atingir 85%):

- ⚠️ View `admin_dashboard()` (não testada)
- ⚠️ Método `save_model()` no Admin (sanitização XSS)
- ⚠️ Management command `send_deadline_notifications` (não testado)
- ⚠️ Edge cases em views e models

---

## 📁 Estrutura do Projeto

```text
UniRV-Django/
├── editais/                      # App principal de editais
│   ├── management/
│   │   └── commands/
│   │       ├── seed_editais.py              # Popular banco com dados de exemplo
│   │       ├── update_edital_status.py      # Atualizar status automaticamente
│   │       └── send_deadline_notifications.py  # Notificações de prazo
│   ├── migrations/               # Migrações do banco de dados
│   ├── templatetags/
│   │   └── editais_filters.py   # Template tags customizados
│   ├── tests/                    # Testes organizados por módulo
│   │   ├── test_admin.py
│   │   ├── test_permissions.py
│   │   └── test_management_commands.py
│   ├── models.py                 # Modelos (Edital, EditalValor, Cronograma, EditalHistory)
│   ├── views.py                  # Views públicas e administrativas
│   ├── forms.py                  # Formulários
│   ├── urls.py                   # URLs do app
│   ├── admin.py                  # Configuração do Django Admin
│   └── tests.py                  # Testes principais
├── UniRV_Django/                 # Configurações do projeto
│   ├── settings.py               # Configurações Django
│   ├── urls.py                   # URLs principais
│   └── wsgi.py                   # WSGI para produção
├── templates/                    # Templates HTML
│   ├── base.html                 # Template base
│   └── editais/                  # Templates do app editais
│       ├── index.html            # Listagem de editais
│       ├── detail.html           # Detalhes do edital
│       ├── create.html           # Criar edital
│       ├── update.html           # Editar edital
│       ├── delete.html           # Excluir edital
│       ├── dashboard.html        # Dashboard administrativo
│       └── emails/               # Templates de email
├── static/                       # Arquivos estáticos
│   ├── css/
│   │   └── style.css             # Estilos principais
│   └── js/
│       └── main.js               # JavaScript principal
├── specs/                        # Documentação de especificação
│   └── 001-hub-editais/          # Especificação do módulo
│       ├── spec.md               # Especificação completa
│       ├── plan.md                # Plano de implementação
│       ├── tasks.md               # Lista de tarefas
│       ├── checklist.md           # Checklist de implementação
│       ├── analysis.md            # Análise do projeto
│       └── clarifications.md     # Clarificações
├── logs/                         # Logs da aplicação (gerado automaticamente)
├── requirements.txt              # Dependências do projeto
├── .env.example                  # Exemplo de variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
├── COVERAGE_REPORT.md            # Relatório de cobertura de testes
└── manage.py                     # Utilitário de gerenciamento Django
```

---

## 🔒 Segurança

### Melhorias de Segurança Implementadas

#### Sanitização de HTML (XSS Prevention)

- Sanitização com `bleach` em todas as views web
- Sanitização também no Django Admin (método `save_model()`)
- Tags e atributos HTML permitidos configurados

#### Controle de Acesso

- Operações administrativas restritas a usuários `is_staff`
- Editais em status 'draft' ocultos para não-autenticados
- Verificação de permissões em todas as views administrativas

#### Validação de Dados

- Validação de datas (end_date > start_date)
- Validação de campos obrigatórios
- Validação de slug (garantia de unicidade)

#### Headers de Segurança (em produção)

- `SECURE_REFERRER_POLICY`
- `SECURE_CROSS_ORIGIN_OPENER_POLICY`
- `X_FRAME_OPTIONS = 'DENY'`
- `SECURE_BROWSER_XSS_FILTER`
- `SECURE_CONTENT_TYPE_NOSNIFF`

#### Sessões Seguras

- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = 'Lax'`
- `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`

#### SECRET_KEY em variável de ambiente

- Nunca commit a `SECRET_KEY` no código
- Use `.env` para desenvolvimento local
- Configure variáveis de ambiente no servidor de produção

#### ALLOWED_HOSTS configurado corretamente

- Em desenvolvimento: `localhost`, `127.0.0.1`, `[::1]`
- Em produção: especifique seus domínios no `.env`

#### Arquivo .env no .gitignore

- Garante que credenciais não sejam commitadas

### Checklist de Segurança para Produção

Antes de fazer deploy em produção, certifique-se de:

- [ ] `DEBUG=False` no ambiente de produção
- [ ] `SECRET_KEY` única e segura configurada
- [ ] `ALLOWED_HOSTS` configurado com seus domínios
- [ ] HTTPS habilitado
- [ ] Database backup configurado
- [ ] Logs de aplicação monitorados
- [ ] Atualizar dependências regularmente: `pip list --outdated`
- [ ] Configurar email para notificações (se necessário)
- [ ] Revisar permissões de usuários (`is_staff`)

---

## 📦 Dependências

### Principais

- **Django 5.2.7**: Framework web
- **WhiteNoise 6.7.0**: Servir arquivos estáticos em produção
- **Bleach 6.1.0**: Sanitização de HTML (prevenção XSS)
- **Gunicorn 23.0.0**: WSGI server (produção)

### Opcionais (não utilizadas atualmente)

- **Requests 2.32.3**: HTTP client
- **BeautifulSoup4 4.12.3**: Web scraping
- **Markdown2 2.5.1**: Renderização de Markdown
- **Uvicorn 0.34.0**: ASGI server

---

## 🚀 Deploy

### Preparação

1. Configure todas as variáveis de ambiente no servidor
2. Execute `python manage.py collectstatic` para coletar arquivos estáticos
3. Execute `python manage.py migrate` para aplicar migrações
4. Crie um superusuário: `python manage.py createsuperuser`

### Heroku

```bash
# Instalar Heroku CLI e fazer login
heroku login

# Criar app
heroku create your-app-name

# Configurar variáveis de ambiente
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DJANGO_DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"

# Deploy
git push heroku main

# Executar migrações
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Render / Railway / Fly.io

- Configure as variáveis de ambiente no painel
- Certifique-se de que `requirements.txt` está na raiz
- Configure o comando de start: `gunicorn UniRV_Django.wsgi:application`
- Configure o comando de migração: `python manage.py migrate`

### Servidor VPS (Ubuntu/Debian)

```bash
# Instalar dependências do sistema
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Configurar Nginx como reverse proxy
# (configuração específica depende do seu setup)

# Usar Gunicorn como servidor WSGI
gunicorn UniRV_Django.wsgi:application --bind 0.0.0.0:8000

# Configurar systemd service para Gunicorn
# (criar arquivo de serviço em /etc/systemd/system/)
```

---

## 📊 Status do Projeto

### Implementação

- ✅ **95% das tarefas concluídas** (85/89)
- ✅ **34+ testes passando**
- ✅ **Todas as funcionalidades críticas implementadas**
- ⚠️ **Cobertura de testes**: 69% (meta: 85%)

### Melhorias Recentes

**Data**: 2025-01-15

- ✅ Correção de vulnerabilidade XSS no Django Admin
- ✅ Melhorias no banco de dados (índices, validações)
- ✅ Limpeza de código morto
- ✅ Arquivos de suporte completos (`.gitignore`, `.env.example`)

### Próximos Passos

1. Aumentar cobertura de testes para 85%+
2. Implementar testes para `admin_dashboard()`
3. Implementar testes para `save_model()` no Admin
4. Documentação de produção final

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- Siga as convenções do Django
- Escreva testes para novas funcionalidades
- Mantenha cobertura de testes acima de 85%
- Documente mudanças significativas

---

## 📝 Licença

[Adicionar licença aqui]

---

## 👥 Autores

### UniRV - Universidade de Rio Verde

---

## 📚 Documentação Adicional

- [Especificação Completa](./specs/001-hub-editais/spec.md)
- [Plano de Implementação](./specs/001-hub-editais/plan.md)
- [Análise do Projeto](./specs/001-hub-editais/analysis.md)
- [Relatório de Cobertura](./COVERAGE_REPORT.md)

---

**Última atualização**: 2025-01-15
