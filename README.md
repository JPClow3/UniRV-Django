# AgroHub - Hub de Inovação e Fomento da UniRV

Plataforma oficial do **AgroHub** - Hub de Inovação e Fomento da Universidade de Rio Verde (UniRV), destinada a promover o ecossistema de inovação através do gerenciamento de editais de fomento, incubação de startups e desenvolvimento tecnológico.

**Status do Projeto**: ✅ **Produção Ready** - Otimizado, seguro e pronto para deploy

---

## 🏛️ Sobre o AgroHub

O **AgroHub** é o Hub de Inovação e Fomento da Universidade de Rio Verde (UniRV), composto por dois ambientes principais:

- **YPETEC** - Incubadora de startups da UniRV, voltada para o desenvolvimento e aceleração de novos negócios inovadores, especialmente no agronegócio e tecnologias relacionadas.

- **InovaLab** - Ambiente de desenvolvimento tecnológico equipado com laboratório de software, impressoras 3D e outras ferramentas para prototipagem e desenvolvimento de soluções tecnológicas.

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Stack Tecnológica](#-stack-tecnológica)
3. [Pré-requisitos](#-pré-requisitos)
4. [Instalação e Setup](#-instalação-e-setup)
5. [Configuração](#-configuração)
6. [Estrutura do Projeto](#-estrutura-do-projeto)
7. [Funcionalidades](#-funcionalidades)
8. [Banco de Dados](#-banco-de-dados)
9. [APIs e URLs](#-apis-e-urls)
10. [Management Commands](#-management-commands)
11. [Desenvolvimento](#-desenvolvimento)
12. [Testes](#-testes)
13. [Deploy](#-deploy)
14. [Docker](#-docker)
15. [Performance e Otimização](#-performance-e-otimização)
16. [Segurança](#-segurança)
17. [Troubleshooting](#-troubleshooting)
18. [Contribuindo](#-contribuindo)
19. [Licença e Autores](#-licença-e-autores)

---

## 🎯 Visão Geral

O **AgroHub** é uma plataforma web desenvolvida para apresentar e gerenciar o ecossistema de inovação da UniRV. O sistema oferece:

- **Gerenciamento de Editais**: Divulgação e busca de oportunidades de fomento para startups e projetos de inovação
- **Vitrine de Startups**: Showcase das startups incubadas na YPETEC
- **Ambientes de Inovação**: Apresentação da YPETEC (incubadora) e do InovaLab (laboratório de desenvolvimento)

### Principais Características

- 🎨 **Interface Moderna**: Design responsivo com Tailwind CSS v4
- 🔍 **Busca Avançada**: Sistema de busca full-text com PostgreSQL
- 📊 **Dashboard Completo**: Painel administrativo com estatísticas e gerenciamento
- 🔒 **Segurança Robusta**: Proteção XSS, CSRF, rate limiting e sanitização de dados
- ⚡ **Performance Otimizada**: Cache, queries otimizadas, minificação de assets
- 📱 **Responsivo**: Interface adaptável para desktop, tablet e mobile
- 🔐 **Auditoria Completa**: Histórico de alterações em todos os editais
- 🚀 **Deploy Fácil**: Configuração Docker pronta para produção

---

## 🛠 Stack Tecnológica

### Backend

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Python** | 3.12+ | Linguagem principal |
| **Django** | >=5.2.8 | Framework web |
| **PostgreSQL** | 16+ | Banco de dados (todos os ambientes) |
| **Redis** | 7+ | Cache (todos os ambientes) |

### Frontend

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Tailwind CSS** | 4.1.16 | Framework CSS utilitário |
| **PostCSS** | 8.5.6 | Processamento de CSS |
| **JavaScript (Vanilla)** | ES6+ | Interatividade e animações |
| **Terser** | 5.36.0 | Minificação de JavaScript |

### Infraestrutura e Ferramentas

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Gunicorn** | >=23.0.0 | Servidor WSGI (produção) |
| **WhiteNoise** | >=6.11.0 | Servir arquivos estáticos |
| **Docker** | Latest | Containerização |
| **Node.js** | 20 LTS | Build de assets frontend |
| **Nginx** | Latest | Reverse proxy (opcional) |

### Bibliotecas Python Principais

- **django-simple-history** (>=3.11.0): Auditoria e histórico de alterações
- **django-redis** (>=6.0.0): Backend de cache Redis
- **django-tailwind** (>=3.8.0): Integração Tailwind CSS
- **django-widget-tweaks** (>=1.5.1): Customização de formulários
- **bleach** (>=6.3.0): Sanitização HTML (prevenção XSS)
- **Pillow** (>=11.0.0): Processamento de imagens
- **psycopg2-binary** (>=2.9.10): Driver PostgreSQL

### Ferramentas de Desenvolvimento

- **django-browser-reload** (>=1.21.0): Auto-reload em desenvolvimento
- **pip-audit** (>=2.9.0): Auditoria de segurança de dependências
- **@lhci/cli** (^0.12.0): Lighthouse CI para auditorias de performance

---

## 📦 Pré-requisitos

### Obrigatórios

- **Python 3.12** ou superior
- **pip** (gerenciador de pacotes Python)
- **Node.js 18+** e **npm** (para compilar Tailwind CSS)
- **Git** para versionamento
- **PostgreSQL 16+** (todos os ambientes)
- **Redis 7+** (todos os ambientes)

### Opcionais (para produção)

- **Docker** e **Docker Compose** (para containerização)
- **Nginx** (para reverse proxy)
- **Certbot** (para SSL/HTTPS)

### Verificação de Versões

```bash
# Verificar Python
python --version  # Deve ser 3.12 ou superior

# Verificar pip
pip --version

# Verificar Node.js
node --version  # Deve ser 18 ou superior

# Verificar npm
npm --version

# Verificar Git
git --version
```

---

## 🚀 Instalação e Setup

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd AgroHub
```

### 2. Crie e Ative o Ambiente Virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Verificar ativação:**
O prompt deve mostrar `(.venv)` no início da linha.

### 3. Instale as Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Instale as Dependências Node.js (Tailwind CSS)

```bash
cd theme/static_src
npm ci
cd ../..
```

**Alternativa usando django-tailwind:**
```bash
python manage.py tailwind install
```

### 5. Compile os Assets Frontend

```bash
cd theme/static_src
npm run build
cd ../..
```

Isso irá:
- Limpar arquivos antigos de build
- Compilar Tailwind CSS para produção (minificado)
- Minificar arquivos JavaScript

### 6. Configure as Variáveis de Ambiente

Copie o arquivo de exemplo e configure:

```bash
# Windows
copy .env.production.example .env

# Linux/Mac
cp .env.production.example .env
```

Edite o arquivo `.env` com suas configurações (veja seção [Configuração](#-configuração)).

#### Gerando SECRET_KEY Segura

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie o resultado e adicione ao `.env`:

```text
SECRET_KEY=seu-secret-key-aqui
```

### 7. Execute as Migrações do Banco de Dados

```bash
python manage.py migrate
```

### 8. Crie um Superusuário

```bash
python manage.py createsuperuser
```

Siga as instruções para criar o primeiro usuário administrador.

### 9. (Opcional) Popule o Banco com Dados de Exemplo

```bash
# Popular editais de exemplo
python manage.py seed_editais

# Popular startups de exemplo
python manage.py seed_startups
```

### 10. Colete Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 11. Inicie o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

Acesse: <http://127.0.0.1:8000/>

---

## ⚙️ Configuração

### Variáveis de Ambiente

O projeto usa variáveis de ambiente para configuração. Todas as variáveis são opcionais exceto em produção (onde `SECRET_KEY` e `ALLOWED_HOSTS` são obrigatórias).

#### Variáveis Críticas (Produção)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `SECRET_KEY` | Chave secreta do Django (obrigatória em produção) | Gerar com comando acima |
| `DJANGO_DEBUG` | Modo debug (`False` em produção) | `False` |
| `ALLOWED_HOSTS` | Domínios permitidos (separados por vírgula) | `example.com,www.example.com` |

#### Banco de Dados

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DB_NAME` | Nome do banco de dados | **Obrigatório** |
| `DB_USER` | Usuário do banco | `postgres` |
| `DB_PASSWORD` | Senha do banco | **Obrigatório** |
| `DB_HOST` | Host do banco | `localhost` |
| `DB_PORT` | Porta do banco | `5432` |

**Nota:** PostgreSQL é obrigatório para todos os ambientes. Use Docker para desenvolvimento local.

#### Cache (Redis)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `REDIS_HOST` | Host do Redis | **Obrigatório** |
| `REDIS_PORT` | Porta do Redis | `6379` |

**Nota:** Redis é obrigatório para todos os ambientes. Use Docker para desenvolvimento local.

#### Email

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `EMAIL_BACKEND` | Backend de email | `console` (dev) |
| `EMAIL_HOST` | Servidor SMTP | `localhost` |
| `EMAIL_PORT` | Porta SMTP | `587` |
| `EMAIL_USE_TLS` | Usar TLS | `True` |
| `EMAIL_HOST_USER` | Usuário SMTP | - |
| `EMAIL_HOST_PASSWORD` | Senha SMTP | - |
| `DEFAULT_FROM_EMAIL` | Email remetente | `noreply@agrohub.unirv.edu.br` |

#### Opcionais

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `SITE_URL` | URL base do site | `http://localhost:8000` |
| `DJANGO_LOG_LEVEL` | Nível de log | `INFO` |
| `DJANGO_LOG_TO_FILE` | Habilitar logs em arquivo | `False` |
| `DJANGO_LOG_DIR` | Diretório de logs | `./logs` |
| `COOKIE_DOMAIN` | Domínio dos cookies | - |
| `WHITENOISE_MAX_AGE` | Cache de arquivos estáticos (segundos) | `3600` (dev) |
| `CDN_BASE_URL` | URL base do CDN para imagens | - |

### Configurações do Django

Principais configurações em `UniRV_Django/settings.py`:

#### Idioma e Localização

- **Idioma:** Português (pt-BR)
- **Fuso Horário:** America/Sao_Paulo
- **Formato de Data:** DD/MM/YYYY

#### Paginação

- **Editais por página:** 12 itens
- Configurável via `EDITAIS_PER_PAGE` em settings.py

#### Cache

- **Desenvolvimento:** LocMemCache (memória local)
- **Produção:** Redis (se configurado)
- **TTL padrão:** 5 minutos (300 segundos)
- Configurável via `EDITAIS_CACHE_TTL`

#### Logging

- **Desenvolvimento:** Console
- **Produção:** Arquivos rotativos (opcional)
- **Logs separados:** Aplicação, segurança, performance
- **Tamanho máximo:** 10MB por arquivo
- **Backup count:** 5 arquivos

#### Segurança

As configurações de segurança são habilitadas automaticamente quando `DEBUG=False`:

- SSL/HTTPS obrigatório
- Headers de segurança (HSTS, X-Frame-Options, etc.)
- Cookies seguros (HttpOnly, Secure, SameSite)
- CSRF protection
- XSS protection (sanitização HTML)

---

## 📁 Estrutura do Projeto

```text
AgroHub/
├── editais/                          # App principal de editais
│   ├── __init__.py
│   ├── apps.py                       # Configuração do app
│   ├── admin.py                      # Configuração do Django Admin
│   ├── models.py                     # Modelos de dados
│   ├── views.py                      # Views principais
│   ├── views/                        # Views organizadas por módulo
│   │   ├── __init__.py
│   │   ├── public.py                 # Views públicas
│   │   ├── dashboard.py              # Views do dashboard
│   │   ├── editais_crud.py           # CRUD de editais
│   │   └── mixins.py                 # Mixins reutilizáveis
│   ├── forms.py                      # Formulários
│   ├── urls.py                       # URLs do app
│   ├── utils.py                      # Funções utilitárias
│   ├── services.py                   # Lógica de negócio
│   ├── decorators.py                 # Decoradores customizados
│   ├── exceptions.py                 # Exceções customizadas
│   ├── constants.py                  # Constantes do app
│   ├── constants/                    # Módulos de constantes
│   │   ├── __init__.py
│   │   ├── cache.py                  # Constantes de cache
│   │   ├── limits.py                 # Limites e rate limiting
│   │   └── status.py                 # Status de editais
│   ├── cache_utils.py                # Utilitários de cache
│   ├── templatetags/                 # Template tags customizados
│   │   ├── __init__.py
│   │   ├── editais_filters.py        # Filtros para templates
│   │   └── image_helpers.py          # Helpers de imagem
│   ├── management/                   # Management commands
│   │   └── commands/
│   │       ├── seed_editais.py       # Popular editais de exemplo
│   │       ├── seed_startups.py      # Popular startups de exemplo
│   │       ├── update_edital_status.py  # Atualizar status automaticamente
│   │       ├── run_lighthouse.py     # Auditorias Lighthouse
│   │       ├── run_lighthouse_audit.py
│   │       ├── get_auth_cookie.py    # Utilitário de autenticação
│   │       └── populate_from_pdfs.py # Popular de PDFs
│   ├── migrations/                   # Migrações do banco de dados
│   │   ├── 0001_initial.py
│   │   └── ...                       # Outras migrações
│   └── tests/                        # Testes
│       ├── __init__.py
│       ├── test_admin.py             # Testes do admin
│       ├── test_permissions.py       # Testes de permissões
│       ├── test_public_views.py      # Testes de views públicas
│       ├── test_dashboard_views.py   # Testes do dashboard
│       ├── test_security.py          # Testes de segurança
│       ├── test_cache.py             # Testes de cache
│       ├── test_forms.py             # Testes de formulários
│       └── ...                       # Outros testes
│
├── UniRV_Django/                     # Configurações do projeto Django
│   ├── __init__.py
│   ├── settings.py                   # Configurações principais
│   ├── urls.py                       # URLs raiz do projeto
│   ├── wsgi.py                       # WSGI para produção
│   └── asgi.py                       # ASGI (não usado atualmente)
│
├── theme/                            # App do tema Tailwind
│   ├── __init__.py
│   ├── apps.py
│   ├── static/                       # Assets estáticos compilados
│   │   └── fonts/                    # Fontes
│   └── static_src/                   # Código fonte dos assets
│       ├── package.json              # Dependências npm
│       ├── package-lock.json         # Lock de dependências
│       ├── tailwind.config.js        # Configuração Tailwind
│       ├── postcss.config.js        # Configuração PostCSS
│       └── src/
│           ├── styles.css            # CSS principal
│           └── fonts/                # Fontes fonte
│
├── templates/                        # Templates HTML
│   ├── base.html                     # Template base
│   ├── home.html                     # Página inicial
│   ├── 403.html                      # Erro 403
│   ├── 404.html                      # Erro 404
│   ├── 500.html                      # Erro 500
│   ├── components/                   # Componentes reutilizáveis
│   │   ├── button.html
│   │   ├── edital_skeleton_card.html
│   │   └── empty_state.html
│   ├── editais/                      # Templates de editais
│   │   ├── index.html                # Listagem
│   │   ├── detail.html               # Detalhes
│   │   ├── create.html               # Criar
│   │   ├── update.html               # Editar
│   │   ├── delete.html               # Excluir
│   │   ├── dashboard.html            # Dashboard
│   │   └── index_partial.html        # Partial para AJAX
│   ├── dashboard/                    # Templates do dashboard
│   │   ├── base.html                 # Base do dashboard
│   │   ├── home.html                 # Home do dashboard
│   │   ├── editais.html              # Lista de editais
│   │   ├── novo_edital.html          # Novo edital
│   │   ├── startups.html             # Lista de startups incubadas
│   │   ├── startup_update.html       # Atualizar startup
│   │   ├── submeter_startup.html     # Cadastrar startup
│   │   └── usuarios.html             # Usuários
│   ├── registration/                 # Templates de autenticação
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── password_reset_*.html     # Recuperação de senha
│   │   └── password_reset_subject.txt
│   ├── startups/                     # Templates de startups
│   │   ├── index.html
│   │   └── detail.html
│   ├── ambientes_inovacao/           # Ambientes de inovação
│   │   └── index.html
│   └── admin/                        # Templates do admin
│       └── login.html
│
├── static/                           # Arquivos estáticos não compilados
│   ├── css/                          # CSS adicional
│   │   ├── animations.css
│   │   ├── detail.css
│   │   └── print.css
│   ├── js/                           # JavaScript
│   │   ├── main.js                   # JavaScript principal
│   │   ├── animations.js             # Animações
│   │   ├── detail.js                 # Detalhes
│   │   └── *.min.js                  # Versões minificadas
│   ├── img/                          # Imagens
│   │   ├── hero/                     # Imagens hero
│   │   ├── favicon.svg
│   │   ├── logo-agrohub.svg
│   │   └── logo_inovalab.svg
│   └── fonts/                        # Fontes (Montserrat)
│       ├── Montserrat-Regular.ttf
│       └── Montserrat-SemiBold.ttf
│
├── staticfiles/                      # Coletados pelo collectstatic (gerado, não versionado)
│   └── ...
│
├── media/                            # Arquivos de mídia (uploaded) (gerado)
│   └── ...                           # Uploads de usuários
│
├── logs/                             # Logs da aplicação (gerado)
│   ├── django.log                    # Log principal
│   ├── security.log                  # Logs de segurança
│   └── performance.log               # Logs de performance
│
├── scripts/                          # Scripts utilitários
│   ├── generate_hero_images.py       # Gerar imagens hero
│   └── track_lighthouse_scores.py    # Rastreamento de scores
│
├── manage.py                         # Utilitário de gerenciamento Django
├── requirements.txt                  # Dependências Python
├── Dockerfile                        # Configuração Docker
├── docker-entrypoint.sh              # Script de entrada Docker
├── .dockerignore                     # Arquivos ignorados pelo Docker
├── .gitignore                        # Arquivos ignorados pelo Git
├── .env.production.example           # Exemplo de variáveis de ambiente
└── README.md                         # Este arquivo
```

### Descrição dos Diretórios Principais

#### `editais/`
App principal do Django contendo toda a lógica de negócio relacionada a editais e startups.

#### `UniRV_Django/`
Configurações do projeto Django, incluindo settings, URLs principais e configurações WSGI.

#### `theme/`
App Django para o tema Tailwind CSS. Contém o código fonte dos assets frontend e a configuração de build.

#### `templates/`
Templates HTML organizados por funcionalidade. Usa herança de templates com `base.html` como template principal.

#### `static/`
Arquivos estáticos não compilados (CSS adicional, JavaScript, imagens, fontes).

#### `staticfiles/` *(gerado — não versionado)*
Diretório gerado pelo `collectstatic` contendo todos os arquivos estáticos coletados e processados.

---

## ✨ Funcionalidades

### Funcionalidades Principais

#### 1. Gerenciamento de Editais

- **Criação**: Criar novos editais com todos os campos necessários
- **Edição**: Editar editais existentes com validação
- **Exclusão**: Excluir editais (soft delete recomendado)
- **Visualização**: Visualizar editais com informações completas
- **Status Automático**: Atualização automática de status baseado em datas

#### 2. Sistema de Busca Avançada

- **Busca Full-Text**: Usa PostgreSQL full-text search quando disponível
- **Busca por Múltiplos Campos**: Busca em título, entidade, número, análise, etc.
- **Ranking de Resultados**: Resultados ordenados por relevância
- **Sugestões de Busca**: Sugestões usando trigram similarity (PostgreSQL)
- **Full-Text Search**: Busca avançada com PostgreSQL full-text search

#### 3. Dashboard Administrativo

- **Home**: Estatísticas e visão geral
- **Editais**: Gerenciamento completo de editais
- **Startups**: Gerenciamento de startups incubadas
- **Usuários**: Gerenciamento de usuários
- **Relatórios**: Estatísticas e relatórios (futuro)

#### 4. Sistema de Autenticação

- **Registro de Usuários**: Cadastro com validação de email
- **Login/Logout**: Autenticação segura
- **Recuperação de Senha**: Reset de senha via email
- **Permissões**: Controle de acesso baseado em roles (`is_staff`)

#### 5. Páginas Públicas

- **Home**: Landing page com hero, estatísticas e features
- **Listagem de Editais**: Página com busca, filtros e paginação
- **Detalhes do Edital**: Página completa com todas as informações
- **Vitrine de Startups**: Listagem pública de startups incubadas
- **Ambientes de Inovação**: Informações sobre ambientes
- **Passo a Passo**: Guia para participação em editais

#### 6. Histórico e Auditoria

- **Histórico de Alterações**: Todas as mudanças em editais são rastreadas
- **Rastreamento de Usuário**: Registro de quem fez cada alteração
- **Timestamps**: Datas de criação e atualização

### Recursos de Segurança

#### Sanitização HTML (XSS Prevention)
- Sanitização automática com `bleach` em todos os campos HTML
- Configuração de tags e atributos permitidos
- Proteção no Django Admin e nas views web

#### Rate Limiting
- Limitação de taxa de requisições por IP
- Proteção contra abuso de APIs e formulários
- Configurável por rota

#### Headers de Segurança
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy
- Content-Security-Policy (futuro)

#### Controle de Acesso
- Operações administrativas restritas a `is_staff`
- Editais em draft ocultos para não-autenticados
- Validação de permissões em todas as views

### Recursos de Performance

#### Cache
- **Cache de Páginas**: Cache de páginas de listagem
- **Cache de Consultas**: Cache de resultados de busca
- **Cache de Sugestões**: Cache de sugestões de busca
- **TTL Configurável**: Tempos de cache configuráveis

#### Otimização de Queries
- **select_related**: Para relações ForeignKey
- **prefetch_related**: Para relações ManyToMany e Reverse ForeignKey
- **QuerySets Customizados**: Métodos otimizados para queries comuns

#### Minificação
- **CSS Minificado**: Tailwind CSS compilado e minificado
- **JavaScript Minificado**: Terser para minificação JS

### Recursos de UX/UI

#### Design Responsivo
- Layout adaptável para mobile, tablet e desktop
- Breakpoints do Tailwind CSS
- Navegação otimizada para mobile

#### Animações
- Animações suaves para transições
- Loading states e skeletons
- Feedback visual para ações do usuário

#### Acessibilidade
- Suporte a leitores de tela
- Navegação por teclado
- Contraste adequado
- Labels e ARIA attributes

---

## � Guia de Uso Rápido

### Painel Administrativo

O AgroHub possui um painel administrativo completo para gerenciar editais e startups.

1. **Acesso**: Faça login e navegue para `/dashboard/home/`
2. **Dashboard**: Visualize estatísticas gerais de editais e startups

### Gerenciamento de Editais

1. **Criar Edital**: 
   - No Dashboard, clique em "Novo Edital" ou navegue para `/dashboard/editais/novo/`
   - Preencha o status inicial (Ex: "Rascunho")
   - Adicione datas de abertura e encerramento

2. **Cronograma**:
   - Após criar o edital, você pode adicionar etapas do cronograma
   - Importante para manter os candidatos informados

### Gerenciamento de Startups

1. **Submissão**:
   - Usuários podem submeter startups via `/dashboard/startups/submeter/`
   - É necessário preencher nome, descrição, categoria e logo

2. **Aprovação**:
   - Administradores revisam as submissões no Dashboard
   - Status pode ser alterado para "Incubada" ou "Graduada"

---

## �🗄️ Banco de Dados

### Modelos Principais

#### Edital
Modelo principal representando um edital de fomento.

**Campos Principais:**
- `titulo`: Título do edital
- `slug`: URL amigável (único)
- `status`: Status (draft, programado, aberto, fechado)
- `numero_edital`: Número do edital
- `entidade_principal`: Entidade responsável
- `url`: URL do edital original
- `data_abertura`: Data de abertura
- `data_encerramento`: Data de encerramento
- `analise`: Análise do edital (HTML)
- `objetivo`: Objetivo (HTML)
- `etapas`: Etapas (HTML)
- `recursos`: Recursos disponíveis (HTML)
- Campos de metadados: `created_by`, `updated_by`, `created_at`, `updated_at`

**Relações:**
- `valores`: Relacionamento 1:N com EditalValor
- `cronogramas`: Relacionamento 1:N com Cronograma
- `created_by`: ForeignKey para User
- `updated_by`: ForeignKey para User

#### EditalValor
Valores financeiros do edital.

**Campos:**
- `edital`: ForeignKey para Edital
- `tipo`: Tipo de valor (total, por projeto, etc.)
- `valor_total`: Valor total
- `moeda`: Moeda (BRL, USD, etc.)

#### Cronograma
Cronograma de atividades do edital.

**Campos:**
- `edital`: ForeignKey para Edital
- `atividade`: Nome da atividade
- `data`: Data da atividade
- `observacoes`: Observações adicionais

#### Startup
Startup incubada no AgroHub.

**Campos:**
- `name`: Nome da startup
- `slug`: URL amigável
- `category`: Categoria da startup
- `description`: Descrição (HTML)
- `logo`: Logo da startup
- `status`: Fase de maturidade (Ideação, MVP, Escala, Suspensa)
- `contato`: Informações de contato
- `submitted_on`: Data de entrada
- `proponente`: ForeignKey para User

### Índices do Banco de Dados

#### PostgreSQL

- **Índices GIN**: Para busca full-text
- **Índices Trigram**: Para sugestões de busca (pg_trgm)
- **Índices B-tree**: Para campos frequentemente consultados (status, data_atualizacao)

#### Migrações Especiais

- `0018_enable_pg_trgm_extension.py`: Habilita extensão pg_trgm
- `0019_add_trigram_indexes.py`: Adiciona índices trigram
- `0020_add_fulltext_search_index.py`: Adiciona índice full-text search

### Backup e Migração

#### Backup Manual
```bash
# PostgreSQL
pg_dump -U usuario -d nome_banco > backup.sql

# PostgreSQL
pg_dump -U agrohub_user agrohub_dev > backup_$(date +%Y%m%d).sql
```

#### Restore
```bash
# PostgreSQL
psql -U usuario -d nome_banco < backup.sql

# PostgreSQL
psql -U agrohub_user agrohub_dev < backup.sql
```

---

## 🔗 APIs e URLs

### URLs Públicas

| URL | Nome | Descrição |
|-----|------|-----------|
| `/` | `home` | Página inicial |
| `/editais/` | `editais_index` | Listagem de editais |
| `/edital/<slug>/` | `edital_detail_slug` | Detalhes do edital (por slug) |
| `/edital/<int:pk>/` | `edital_detail` | Detalhes do edital (por ID, redireciona) |
| `/startups/` | `startups_showcase` | Vitrine de startups |
| `/startup/<slug>/` | `startup_detail_slug` | Detalhes da startup |
| `/projetos-aprovados/` | (redirect) | Redireciona para `/startups/` |
| `/ambientes-inovacao/` | `ambientes_inovacao` | Ambientes de inovação |
| `/register/` | `register` | Registro de usuário |
| `/login/` | `login` | Login |
| `/logout/` | `logout` | Logout |

### URLs de Autenticação

| URL | Nome | Descrição |
|-----|------|-----------|
| `/password-reset/` | `password_reset` | Solicitar reset de senha |
| `/password-reset/done/` | `password_reset_done` | Confirmação de solicitação |
| `/password-reset-confirm/<uidb64>/<token>/` | `password_reset_confirm` | Confirmar reset |
| `/password-reset-complete/` | `password_reset_complete` | Reset completo |

### URLs do Dashboard (Requer Autenticação)

| URL | Nome | Descrição | Permissão |
|-----|------|-----------|-----------|
| `/dashboard/home/` | `dashboard_home` | Home do dashboard | Autenticado |
| `/dashboard/editais/` | `dashboard_editais` | Lista de editais | Autenticado |
| `/dashboard/editais/novo/` | `dashboard_novo_edital` | Novo edital | `is_staff` |
| `/dashboard/startups/` | `dashboard_startups` | Startups incubadas | Autenticado |
| `/dashboard/startups/submeter/` | `dashboard_submeter_startup` | Cadastrar startup | Autenticado |
| `/dashboard/startups/<pk>/editar/` | `dashboard_startup_update` | Editar startup | Autenticado |
| `/dashboard/usuarios/` | `dashboard_usuarios` | Usuários | `is_staff` |

### URLs Administrativas (Requer `is_staff`)

| URL | Nome | Descrição |
|-----|------|-----------|
| `/cadastrar/` | `edital_create` | Criar edital |
| `/edital/<pk>/editar/` | `edital_update` | Editar edital |
| `/edital/<pk>/excluir/` | `edital_delete` | Excluir edital |
| `/admin/` | - | Django Admin |

### URLs Utilitárias

| URL | Nome | Descrição |
|-----|------|-----------|
| `/health/` | `health_check` | Health check da aplicação |

---

## 🛠️ Management Commands

### Comandos Disponíveis

#### `seed_editais`
Popula o banco de dados com editais de exemplo.

```bash
python manage.py seed_editais
```

**Opções:**
- `--count N`: Número de editais a criar (padrão: 10)

#### `seed_startups`
Popula o banco de dados com startups de exemplo.

```bash
python manage.py seed_startups
```

**Opções:**
- `--count N`: Número de startups a criar (padrão: 5)

#### `update_edital_status`
Atualiza automaticamente o status dos editais baseado nas datas.

```bash
python manage.py update_edital_status
```

**Opções:**
- `--dry-run`: Executa sem fazer alterações (apenas mostra)
- `--verbose`: Mostra informações detalhadas

**Uso em Produção:**
Configure no cron para executar diariamente:
```bash
# Crontab (Linux)
0 0 * * * cd /path/to/AgroHub && /path/to/venv/bin/python manage.py update_edital_status
```

#### `run_lighthouse`
Executa auditorias Lighthouse CI.

```bash
python manage.py run_lighthouse
```

**Opções:**
- `--all-pages`: Auditar todas as páginas (incluindo protegidas)
- `--url URL`: URL específica para auditar (pode repetir)
- `--output-dir DIR`: Diretório de saída (padrão: `./lighthouse_reports`)
- `--thresholds KEY=VALUE`: Thresholds customizados
- `--port PORT`: Porta do servidor (padrão: 7000)
- `--no-server`: Não iniciar servidor (já está rodando)
- `--no-auth`: Pular autenticação

### Criando Novos Commands

1. Crie um arquivo em `editais/management/commands/`
2. Estenda `BaseCommand` do Django
3. Implemente o método `handle()`

Exemplo:
```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Descrição do comando'

    def add_arguments(self, parser):
        parser.add_argument('--option', type=str, help='Descrição')

    def handle(self, *args, **options):
        # Lógica do comando
        pass
```

---

## 💻 Desenvolvimento

### Workflow de Desenvolvimento

1. **Criar branch**: `git checkout -b feature/nova-funcionalidade`
2. **Fazer alterações**: Desenvolver a funcionalidade
3. **Rodar testes**: `python manage.py test`
4. **Verificar lint**: Verificar código
5. **Commit**: `git commit -m "Adiciona nova funcionalidade"`
6. **Push**: `git push origin feature/nova-funcionalidade`
7. **Pull Request**: Abrir PR para revisão

### Desenvolvimento Frontend

#### Modo Desenvolvimento (Watch Mode)

```bash
cd theme/static_src
npm run dev
```

Isso compila Tailwind CSS em modo watch, recarregando automaticamente ao salvar.

#### Build de Produção

```bash
cd theme/static_src
npm run build
```

Isso:
- Limpa arquivos antigos
- Compila Tailwind CSS minificado
- Minifica JavaScript
- Copia Font Awesome e GSAP para `static/vendor/` (uso local, sem CDN)

#### Estrutura de Build

```text
theme/static_src/
├── src/styles.css                    # CSS fonte
└── (build) → ../../static/css/dist/styles.css  # CSS compilado

static/js/
├── main.js                           # JS fonte
└── main.min.js                       # JS minificado (build)

static/js/
├── animations.js                     # JS fonte
└── animations.min.js                 # JS minificado (build)
```

### Django Browser Reload

Em desenvolvimento (`DEBUG=True`), o `django-browser-reload` está habilitado para auto-reload do navegador ao salvar arquivos Python ou templates.

**URL:** `http://localhost:8000/__reload__/`

### Debugging

#### Django Debug Toolbar (Opcional)

Para instalar:
```bash
pip install django-debug-toolbar
```

Adicionar ao `INSTALLED_APPS` e `MIDDLEWARE` em desenvolvimento.

#### Logging em Desenvolvimento

Os logs são exibidos no console. Para logs mais detalhados:
```bash
export DJANGO_LOG_LEVEL=DEBUG
python manage.py runserver
```

---

## 🧪 Testes

### Executar Testes

#### Todos os Testes
```bash
python manage.py test editais
```

#### Testes Específicos
```bash
# Teste específico
python manage.py test editais.tests.test_public_views.EditaisIndexTest

# Módulo de testes
python manage.py test editais.tests.test_permissions

# Arquivo de testes
python manage.py test editais.tests.test_admin
```

#### Com Cobertura

```bash
# Instalar coverage
pip install coverage

# Executar testes com cobertura
coverage run --source='editais' --omit='*/migrations/*' manage.py test editais

# Relatório no terminal
coverage report

# Relatório HTML
coverage html
# Abrir htmlcov/index.html no navegador
```

### Estrutura de Testes

```text
editais/tests/
├── test_admin.py              # Testes do Django Admin
├── test_permissions.py         # Testes de permissões
├── test_public_views.py        # Testes de views públicas
├── test_dashboard_views.py     # Testes do dashboard
├── test_security.py            # Testes de segurança
├── test_cache.py               # Testes de cache
├── test_forms.py              # Testes de formulários
├── test_integration.py         # Testes de integração
└── ...
```

### Cobertura Atual

**Status:** 69% (Meta: 85%)

**Testes Implementados:**
- ✅ CRUD de editais (7 testes)
- ✅ Busca e filtros (6 testes)
- ✅ Detalhes e redirecionamento (4 testes)
- ✅ Modelos (slug, validação, status) (5 testes)
- ✅ Formulários (6 testes)
- ✅ Permissões (12 testes)
- ✅ Management commands (8 testes)
- ✅ Admin interface (15 testes)

**Áreas que Precisam de Mais Testes:**
- ⚠️ View `admin_dashboard()` 
- ⚠️ Método `save_model()` no Admin
- ⚠️ Edge cases em views e models

### Testes de Performance

Para testar performance de queries:
```bash
python manage.py test editais.tests.test_performance
```

---

## 🚀 Deploy

### Checklist Pré-Deploy

- [ ] Todas as variáveis de ambiente configuradas
- [ ] `DEBUG=False` em produção
- [ ] `SECRET_KEY` única e segura
- [ ] `ALLOWED_HOSTS` configurado
- [ ] Banco de dados PostgreSQL configurado
- [ ] Redis configurado (recomendado)
- [ ] Email SMTP configurado
- [ ] SSL/HTTPS configurado
- [ ] Arquivos estáticos coletados
- [ ] Migrações aplicadas
- [ ] Superusuário criado
- [ ] Logs configurados
- [ ] Backup do banco de dados configurado

### Preparação

1. **Coletar arquivos estáticos:**

   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Aplicar migrações:**

   ```bash
   python manage.py migrate
   ```

3. **Criar superusuário:**

   ```bash
   python manage.py createsuperuser
   ```

4. **Verificar configurações:**

   ```bash
   python manage.py check --deploy
   ```

### Deploy com Docker

#### Build da Imagem

```bash
docker build -t agrohub:latest .
```

#### Executar Container

```bash
docker run -d \
  --name agrohub \
  -p 8000:8000 \
  -e SECRET_KEY="sua-secret-key" \
  -e DJANGO_DEBUG=False \
  -e ALLOWED_HOSTS="seu-dominio.com" \
  -e DB_NAME="nome_banco" \
  -e DB_USER="usuario" \
  -e DB_PASSWORD="senha" \
  -e DB_HOST="host" \
  agrohub:latest
```

#### Docker Compose (Recomendado)

Crie um arquivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DJANGO_DEBUG=False
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Execute:
```bash
docker-compose up -d
```

### Deploy em VPS (Ubuntu/Debian)

#### 1. Instalar Dependências do Sistema

```bash
sudo apt update
sudo apt install -y python3.12 python3-pip python3-venv nginx redis-server postgresql postgresql-contrib
```

#### 2. Configurar PostgreSQL

```bash
sudo -u postgres psql

# No PostgreSQL:
CREATE DATABASE nome_banco;
CREATE USER usuario WITH PASSWORD 'senha';
ALTER ROLE usuario SET client_encoding TO 'utf8';
ALTER ROLE usuario SET default_transaction_isolation TO 'read committed';
ALTER ROLE usuario SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE nome_banco TO usuario;
\q
```

#### 3. Configurar Aplicação

```bash
# Clonar repositório
cd /var/www
sudo git clone <repository-url> agrohub
cd agrohub

# Criar ambiente virtual
sudo python3.12 -m venv .venv
sudo chown -R $USER:$USER .

# Ativar e instalar dependências
source .venv/bin/activate
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.production.example .env
nano .env  # Editar configurações

# Coletar estáticos e migrar
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

#### 4. Configurar Gunicorn

Criar arquivo `/etc/systemd/system/agrohub.service`:

```ini
[Unit]
Description=AgroHub Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/agrohub
ExecStart=/var/www/agrohub/.venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    UniRV_Django.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agrohub
sudo systemctl start agrohub
sudo systemctl status agrohub
```

#### 5. Configurar Nginx

Criar arquivo `/etc/nginx/sites-available/agrohub`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/agrohub/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/agrohub/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

Ativar site:
```bash
sudo ln -s /etc/nginx/sites-available/agrohub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. Configurar SSL com Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

O Certbot irá configurar SSL automaticamente e renovação automática.

### Deploy em Plataformas Cloud

#### Heroku

```bash
# Instalar Heroku CLI
# Fazer login
heroku login

# Criar app
heroku create seu-app-name

# Configurar variáveis
heroku config:set SECRET_KEY="sua-secret-key"
heroku config:set DJANGO_DEBUG=False
heroku config:set ALLOWED_HOSTS="seu-app-name.herokuapp.com"

# Adicionar add-ons
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini

# Deploy
git push heroku main

# Migrar banco
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

#### Render

1. Conectar repositório GitHub
2. Configurar variáveis de ambiente no painel
3. Definir build command: `pip install -r requirements.txt && cd theme/static_src && npm ci && npm run build && cd ../.. && python manage.py collectstatic --noinput`
4. Definir start command: `gunicorn UniRV_Django.wsgi:application`
5. Deploy automático

#### Railway

1. Conectar repositório
2. Configurar variáveis de ambiente
3. Adicionar serviços PostgreSQL e Redis
4. Deploy automático

---

## 🐳 Docker

### Estrutura do Dockerfile

O Dockerfile usa **multi-stage build** com 3 estágios:

1. **node-builder**: Compila assets frontend (Tailwind CSS, JavaScript)
2. **python-builder**: Instala dependências Python e coleta arquivos estáticos
3. **runtime**: Imagem final otimizada apenas com runtime

### Build da Imagem

```bash
docker build -t agrohub:latest .
```

### Executar Container

```bash
docker run -d \
  --name agrohub \
  -p 8000:8000 \
  -e SECRET_KEY="sua-secret-key" \
  -e DJANGO_DEBUG=False \
  -e ALLOWED_HOSTS="localhost" \
  agrohub:latest
```

### Variáveis de Ambiente no Docker

Passe variáveis via `-e` ou use arquivo `.env`:

```bash
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  agrohub:latest
```

### Docker Compose

Veja exemplo completo na seção [Deploy com Docker](#deploy-com-docker).

### Entrypoint Script

O Dockerfile usa `docker-entrypoint.sh` que:
- Executa migrações automaticamente
- Fornece mensagens de erro claras
- Inicia o servidor Gunicorn

---

## ⚡ Performance e Otimização

### Cache

#### Cache de Páginas
- Cache de páginas de listagem de editais
- TTL: 5 minutos (configurável)
- Invalidação automática ao criar/editar editais

#### Cache de Consultas
- Cache de resultados de busca
- Cache de sugestões de busca
- Cache de estatísticas

#### Estratégias de Cache

```python
# Cache manual
from django.core.cache import cache

cache.set('key', 'value', 300)  # 5 minutos
value = cache.get('key')
```

### Otimização de Queries

#### select_related (ForeignKey)
```python
editais = Edital.objects.select_related('created_by', 'updated_by')
```

#### prefetch_related (ManyToMany, Reverse FK)
```python
editais = Edital.objects.prefetch_related('valores', 'cronogramas')
```

#### QuerySets Customizados
```python
# Usar métodos otimizados
editais = Edital.objects.with_related().with_prefetch().active()
```

### Minificação e Compressão

#### CSS
- Tailwind CSS compilado e minificado via PostCSS

#### JavaScript
- Minificação via Terser

#### HTML
- GZip compression habilitado
- Configurável via middleware

### Índices do Banco de Dados

#### PostgreSQL
- **GIN indexes**: Para busca full-text
- **Trigram indexes**: Para sugestões de busca
- **B-tree indexes**: Para campos frequentemente consultados

### Monitoramento

#### Logs de Performance
- Query time logging (quando `DEBUG=True`)
- Logs de cache hits/misses
- Logs de tempo de resposta

#### Ferramentas
- Django Debug Toolbar (desenvolvimento)
- Django Silk (profiling)
- Lighthouse CI (auditorias automatizadas)

---

## 🔒 Segurança

### Medidas de Segurança Implementadas

#### 1. Sanitização HTML (XSS Prevention)

- **Biblioteca**: `bleach`
- **Aplicação**: Todos os campos HTML em editais
- **Configuração**: Tags e atributos permitidos definidos

```python
# Em utils.py
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', ...]
ALLOWED_ATTRIBUTES = {'a': ['href', 'title'], ...}
```

#### 2. Rate Limiting

- **Implementação**: Decorator customizado usando cache do Django (`editais/decorators.py`)
- **Aplicação**: Views de login, criação de editais, registro
- **Configuração**: 5 requisições por minuto por IP
- **Design**: Fail-open — requisições são permitidas quando o cache está indisponível

#### 3. CSRF Protection

- Habilitado por padrão no Django
- Tokens CSRF em todos os formulários
- Verificação automática em requisições POST

#### 4. SQL Injection Prevention

- Django ORM previne SQL injection automaticamente
- Queries parametrizadas
- Nunca usar strings SQL diretas

#### 5. Headers de Segurança

Habilitados automaticamente quando `DEBUG=False`:

- **HSTS**: HTTP Strict Transport Security (1 ano)
- **X-Frame-Options**: DENY
- **X-Content-Type-Options**: nosniff
- **Referrer-Policy**: strict-origin-when-cross-origin
- **X-XSS-Protection**: Enabled

#### 6. Sessões Seguras

- **HttpOnly**: Impede acesso JavaScript
- **Secure**: Apenas HTTPS (produção)
- **SameSite**: Lax (proteção CSRF)
- **Expiração**: 1 hora ou ao fechar navegador

#### 7. Autenticação

- Senhas hasheadas com algoritmo seguro (PBKDF2)
- Validação de senha forte
- Proteção contra brute force (rate limiting)

#### 8. Controle de Acesso

- Operações administrativas restritas a `is_staff`
- Editais em draft ocultos para não-autenticados
- Validação de permissões em todas as views

### Checklist de Segurança

Antes de deploy em produção:

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` única e segura
- [ ] `ALLOWED_HOSTS` configurado
- [ ] HTTPS habilitado
- [ ] Senhas fortes para banco de dados
- [ ] Firewall configurado
- [ ] Backup do banco de dados
- [ ] Logs monitorados
- [ ] Dependências atualizadas (`pip-audit`)
- [ ] Usuários com permissões mínimas necessárias

### Auditoria de Segurança

#### pip-audit

```bash
pip-audit -r requirements.txt
```

#### npm audit

```bash
cd theme/static_src
npm audit
```

#### Atualizar Dependências

```bash
# Verificar dependências desatualizadas
pip list --outdated

# Atualizar (cuidado com breaking changes)
pip install --upgrade package-name
```

---

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro: "No module named 'django'"

**Solução:**
```bash
# Verificar se ambiente virtual está ativado
which python  # Deve apontar para .venv

# Reinstalar dependências
pip install -r requirements.txt
```

#### 2. Erro: "TemplateDoesNotExist"

**Solução:**
```bash
# Verificar se templates estão no diretório correto
# Verificar INSTALLED_APPS em settings.py
# Verificar TEMPLATES['DIRS'] em settings.py
```

#### 3. Erro: "Static files not found"

**Solução:**
```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Verificar STATIC_ROOT e STATIC_URL em settings.py
# Verificar se WhiteNoise está no MIDDLEWARE
```

#### 4. Erro de Migração

**Solução:**
```bash
# Verificar estado das migrações
python manage.py showmigrations

# Fazer fake migration (cuidado!)
python manage.py migrate --fake

# Ou resetar migrações (desenvolvimento apenas)
# Deletar arquivos de migração (exceto __init__.py)
# python manage.py makemigrations
# python manage.py migrate
```

#### 5. Erro: "Connection refused" (PostgreSQL)

**Solução:**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar credenciais no .env
# Verificar se banco existe
psql -U usuario -d nome_banco
```

#### 6. Tailwind CSS não compila

**Solução:**
```bash
# Limpar node_modules e reinstalar
cd theme/static_src
rm -rf node_modules package-lock.json
npm ci
npm run build
```

#### 7. Cache não funciona

**Solução:**
```bash
# Limpar cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Verificar configuração de cache em settings.py
# Verificar se Redis está rodando (se usando)
```

#### 8. Erro 500 em Produção

**Solução:**
```bash
# Verificar logs
tail -f logs/django.log

# Verificar variáveis de ambiente
# Verificar DEBUG=False
# Verificar ALLOWED_HOSTS
# Verificar permissões de arquivos
```

### Logs

#### Localização dos Logs

- **Desenvolvimento**: Console
- **Produção**: `logs/` (se `DJANGO_LOG_TO_FILE=true`)
  - `logs/django.log`: Log principal
  - `logs/security.log`: Logs de segurança
  - `logs/performance.log`: Logs de performance

#### Verificar Logs

```bash
# Últimas 100 linhas
tail -n 100 logs/django.log

# Seguir logs em tempo real
tail -f logs/django.log

# Filtrar erros
grep ERROR logs/django.log
```

### Debug Mode

**Nunca deixe `DEBUG=True` em produção!**

Para debug em desenvolvimento:
```bash
export DJANGO_DEBUG=True
export DJANGO_LOG_LEVEL=DEBUG
python manage.py runserver
```

### Suporte

Para problemas não resolvidos:
1. Verificar logs
2. Verificar documentação do Django
3. Abrir issue no repositório
4. Contatar equipe de desenvolvimento

---

## ❓ Perguntas Frequentes (FAQ)

### Instalação e Setup

#### Como criar o ambiente virtual?

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Erro: "No module named 'django'"

**Solução:**
1. Verifique se o ambiente virtual está ativado (deve mostrar `(.venv)` no prompt)
2. Reinstale as dependências: `pip install -r requirements.txt`

#### Tailwind CSS não compila

**Solução:**
```bash
cd theme/static_src
rm -rf node_modules package-lock.json
npm ci
npm run build
```

#### Erro ao instalar dependências Node.js

**Solução:**
- Verifique se Node.js 18+ está instalado: `node --version`
- Limpe o cache: `npm cache clean --force`
- Tente novamente: `npm ci`

### Configuração

#### Como gerar uma SECRET_KEY segura?

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie o resultado e adicione ao arquivo `.env`:
```
SECRET_KEY=sua-secret-key-aqui
```

#### Como configurar o banco de dados PostgreSQL?

1. Crie o banco de dados:
```bash
sudo -u postgres psql
CREATE DATABASE nome_banco;
CREATE USER usuario WITH PASSWORD 'senha';
GRANT ALL PRIVILEGES ON DATABASE nome_banco TO usuario;
```

2. Configure no `.env`:
```
DB_NAME=nome_banco
DB_USER=usuario
DB_PASSWORD=senha
DB_HOST=localhost
DB_PORT=5432
```

#### Erro: "Connection refused" (PostgreSQL)

**Solução:**
1. Verifique se PostgreSQL está rodando: `sudo systemctl status postgresql`
2. Verifique credenciais no `.env`
3. Teste a conexão: `psql -U usuario -d nome_banco`

### Desenvolvimento

#### Como rodar os testes?

```bash
# Todos os testes
python manage.py test editais

# Teste específico
python manage.py test editais.tests.test_public_views

# Com cobertura
coverage run --source='editais' manage.py test editais
coverage report
```

#### Como debugar problemas?

1. Ative o modo debug:
```bash
export DJANGO_DEBUG=True
export DJANGO_LOG_LEVEL=DEBUG
python manage.py runserver
```

2. Verifique os logs em `logs/django.log`

3. Use Django Debug Toolbar (opcional):
```bash
pip install django-debug-toolbar
```

#### Como verificar se há problemas no código?

```bash
# Verificar configurações
python manage.py check

# Verificar para produção
python manage.py check --deploy

# Verificar migrações
python manage.py showmigrations
```

### Banco de Dados

#### Como aplicar migrações?

```bash
# Aplicar todas as migrações
python manage.py migrate

# Aplicar migração específica
python manage.py migrate editais 0024

# Ver estado das migrações
python manage.py showmigrations
```

#### Erro de migração

**Solução:**
1. Verifique o estado: `python manage.py showmigrations`
2. Se necessário, faça backup do banco
3. Tente fazer fake migration (cuidado!): `python manage.py migrate --fake`
4. Ou resetar migrações (apenas desenvolvimento):
   - Delete arquivos de migração (exceto `__init__.py`)
   - `python manage.py makemigrations`
   - `python manage.py migrate`

#### Como fazer backup do banco?

**PostgreSQL:**
```bash
pg_dump -U usuario -d nome_banco > backup_$(date +%Y%m%d).sql
```

### Deployment

#### Arquivos estáticos não aparecem

**Solução:**
```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Verificar STATIC_ROOT e STATIC_URL em settings.py
# Verificar se WhiteNoise está no MIDDLEWARE
```

#### Erro 500 em produção

**Solução:**
1. Verifique logs: `tail -f logs/django.log`
2. Verifique `DEBUG=False` no `.env`
3. Verifique `ALLOWED_HOSTS` configurado
4. Verifique permissões de arquivos
5. Verifique variáveis de ambiente

#### Como configurar SSL/HTTPS?

Use Let's Encrypt com Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

#### Docker não inicia

**Solução:**
1. Verifique logs: `docker logs agrohub`
2. Verifique variáveis de ambiente
3. Verifique se as portas estão disponíveis
4. Rebuild a imagem: `docker build -t agrohub:latest .`

### Performance

#### Cache não funciona

**Solução:**
```bash
# Limpar cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Verificar configuração de cache em settings.py
# Verificar se Redis está rodando (se usando)
```

#### Queries lentas

**Solução:**
1. Use `select_related()` para ForeignKey
2. Use `prefetch_related()` para ManyToMany
3. Verifique índices no banco de dados
4. Use Django Debug Toolbar para identificar N+1 queries

### Segurança

#### Como verificar vulnerabilidades?

```bash
# Python dependencies
pip-audit -r requirements.txt

# Node.js dependencies
cd theme/static_src
npm audit
```

#### Como atualizar dependências?

```bash
# Verificar dependências desatualizadas
pip list --outdated

# Atualizar (cuidado com breaking changes)
pip install --upgrade package-name
```

### Troubleshooting

#### Template não encontrado

**Solução:**
1. Verifique se o template está no diretório correto
2. Verifique `INSTALLED_APPS` em `settings.py`
3. Verifique `TEMPLATES['DIRS']` em `settings.py`

#### Erro de importação

**Solução:**
1. Verifique se o ambiente virtual está ativado
2. Verifique se o módulo está no `PYTHONPATH`
3. Verifique `INSTALLED_APPS` em `settings.py`

#### Problemas com timezone

**Solução:**
- O projeto usa `America/Sao_Paulo`
- Verifique `TIME_ZONE` em `settings.py`
- Use `USE_TZ = True` para timezone-aware datetimes

### Outras Perguntas

#### Onde encontrar mais ajuda?

1. Consulte a [documentação do Django](https://docs.djangoproject.com/)
2. Consulte a [documentação de arquitetura](./docs/architecture/)
3. Consulte a [revisão do banco de dados](./docs/database/DATABASE_REVIEW.md)
4. Abra uma issue no repositório

#### Como reportar bugs?

1. Verifique se o bug já foi reportado
2. Crie uma issue com:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs. atual
   - Versão do Python, Django, etc.
   - Logs relevantes

---

## 🤝 Contribuindo

### Como Contribuir

1. **Fork o projeto**
2. **Crie uma branch**: `git checkout -b feature/nova-funcionalidade`
3. **Desenvolva**: Implemente sua funcionalidade
4. **Teste**: Certifique-se de que os testes passam
5. **Commit**: `git commit -m "Adiciona nova funcionalidade"`
6. **Push**: `git push origin feature/nova-funcionalidade`
7. **Pull Request**: Abra um PR para revisão

### Padrões de Código

#### Python

- Seguir PEP 8
- Usar type hints quando possível
- Documentar funções e classes
- Máximo 120 caracteres por linha

#### Django

- Seguir convenções do Django
- Usar class-based views quando apropriado
- Separar lógica de negócio em services.py
- Validar dados em forms.py

#### Frontend

- Usar Tailwind CSS para estilização
- JavaScript vanilla (sem frameworks)
- Seguir convenções de nomenclatura
- Comentar código complexo

### Testes

- Escrever testes para novas funcionalidades
- Manter cobertura acima de 85%
- Testar casos de erro e edge cases
- Usar nomes descritivos para testes

### Documentação

- Atualizar README.md se necessário
- Documentar novas funcionalidades
- Adicionar comentários em código complexo
- Atualizar docstrings

### Code Review

- PRs são revisados antes de merge
- Responder a comentários de revisão
- Fazer alterações solicitadas
- Manter PRs pequenos e focados

---

## 📝 Licença e Autores

### Licença

Este projeto é propriedade da Universidade de Rio Verde (UniRV) e está destinado ao uso do AgroHub - Hub de Inovação e Fomento.

### Autores

**UniRV** - Universidade de Rio Verde

- **AgroHub** - Hub de Inovação e Fomento
- **YPETEC** - Incubadora de Startups UniRV
- **InovaLab** - Laboratório de Desenvolvimento Tecnológico

### Agradecimentos

- Comunidade Django
- Desenvolvedores de todas as bibliotecas utilizadas
- Contribuidores do projeto

---

## 📚 Documentação Adicional

- [Documentação do Django](https://docs.djangoproject.com/)
- [Documentação do Tailwind CSS](https://tailwindcss.com/docs)
- [Índice da Documentação](./docs/README.md) - Índice completo de toda a documentação
- [Arquitetura do Sistema](./docs/architecture/system-architecture.md) - Visão geral da arquitetura
- [Schema do Banco de Dados](./docs/architecture/database-schema.md) - Diagrama do schema
- [Arquitetura de Deploy](./docs/architecture/deployment.md) - Arquitetura de deployment
- [Revisão do Banco de Dados](./docs/database/DATABASE_REVIEW.md) - Análise detalhada da estrutura do banco de dados
- [Revisão das Migrações](./docs/migrations/MIGRATION_REVIEW.md) - Análise completa das migrações do Django
- [Documentação de Testes](./editais/tests/README.md) - Guia completo para testes
- [CHANGELOG](./CHANGELOG.md) - Histórico de versões e mudanças

---

## 📞 Contato

Para dúvidas, sugestões ou problemas:

- **Email**: Entre em contato através do departamento de tecnologia da UniRV
- **Repositório**: Consulte o repositório Git do projeto
- **Documentação**: Consulte este README e os documentos de revisão (DATABASE_REVIEW.md, MIGRATION_REVIEW.md)

---

**Última atualização**: 2025-01-15  
**Versão**: 1.0.0

---

Desenvolvido com ❤️ pela equipe UniRV
