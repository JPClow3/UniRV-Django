# UniRV Django - YPETEC

Sistema de gerenciamento de editais de fomento para a YPETEC - Incubadora UniRV.

**Status do Projeto**: ✅ **Produção Ready** - Otimizado e seguro para deploy

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

- ✅ **Listagem de Editais**: Busca, filtros por status/data/tipo, paginação (12 itens por página)
- ✅ **Detalhes do Edital**: Visualização completa com cronogramas e valores
- ✅ **URLs Amigáveis**: URLs baseadas em slug com redirecionamento automático de URLs antigas
- ✅ **CRUD Completo**: Criar, editar e excluir editais (restrito a usuários `is_staff`)
- ✅ **Dashboard Completo**: Home, Editais, Projetos, Usuários, Avaliações, Relatórios, Publicações
- ✅ **Histórico de Alterações**: Rastreamento completo de mudanças em editais
- ✅ **Atualização Automática de Status**: Comando para atualizar status baseado em datas
- ✅ **Registro de Usuários**: Sistema de cadastro com validação de email e senha
- ✅ **Página de Comunidade**: Feed de publicações com interações (curtir/compartilhar)
- ✅ **Projetos Aprovados**: Listagem de projetos aprovados
- ✅ **Passo a Passo**: Guia de como participar dos editais

### Recursos de Segurança

- ✅ **Sanitização de HTML**: Prevenção de XSS em views web e Django Admin
- ✅ **Controle de Acesso**: Operações administrativas restritas a usuários `is_staff`
- ✅ **Validação de Dados**: Validação de datas e campos obrigatórios
- ✅ **Headers de Segurança**: Configurados para produção

### Recursos de UX/UI

- ✅ **Design Responsivo**: Interface adaptável para mobile e desktop
- ✅ **Notificações Toast**: Feedback visual para ações do usuário
- ✅ **Indicador de Prazo Próximo**: Alerta visual para editais com prazo nos próximos 7 dias
- ✅ **Filtros Preservados**: Filtros mantidos durante paginação
- ✅ **Acessibilidade**: Suporte a leitores de tela e navegação por teclado

---

## 🚀 Setup Rápido

### Pré-requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Node.js 18+ e npm (para Tailwind CSS)
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

### 3. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 4. Instale as dependências npm (Tailwind CSS)

**Opção 1: Usando o script de setup automático (recomendado)**

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh

# Ou usando Python
python setup.py
```

**Opção 2: Usando django-tailwind diretamente**

```bash
python manage.py tailwind install
```

Isso irá:
- Instalar automaticamente todas as dependências npm necessárias
- Compilar o CSS do Tailwind para produção

> **Nota:** Se você não tiver Node.js instalado, baixe em https://nodejs.org/

### 5. Configure as variáveis de ambiente

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

### 6. Execute as migrações

```bash
python manage.py migrate
```

### 7. Crie um superusuário

```bash
python manage.py createsuperuser
```

Siga as instruções para criar um usuário administrador.

### 8. (Opcional) Popular o banco com dados de exemplo

```bash
python manage.py seed_editais
```

### 9. Inicie o servidor

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
- `REDIS_HOST`: Host do Redis para cache (opcional, usa LocMemCache se não configurado)
- `REDIS_PORT`: Porta do Redis (padrão: `6379`)

### Configurações do Django

As principais configurações estão em `UniRV_Django/settings.py`:

- **Idioma**: Português (pt-BR)
- **Fuso Horário**: America/Sao_Paulo
- **Paginação**: 12 itens por página
- **Cache**: Redis (produção) ou LocMemCache (desenvolvimento) com TTL de 5 minutos
- **Logging**: Estruturado com rotação de arquivos, logs de segurança e performance
- **Minificação**: CSS/JS minificados em produção via django-compressor
- **SSL/HTTPS**: Configurado para produção com headers de segurança

---

## 📖 Uso

### Acessando o Sistema

1. **Página Inicial**: `/` - Landing page com hero, estatísticas e features
2. **Listagem de Editais**: `/editais/` - Lista todos os editais públicos
3. **Detalhes**: `/editais/edital/<slug>/` - Visualizar edital específico
4. **Comunidade**: `/comunidade/` - Feed de publicações da comunidade
5. **Projetos Aprovados**: `/projetos-aprovados/` - Lista de projetos aprovados
6. **Como Participar**: `/passo-a-passo/` - Guia passo a passo
7. **Registro**: `/register/` - Criar nova conta
8. **Login**: `/login/` - Fazer login
9. **Admin Django**: `/admin/` - Interface administrativa completa
10. **Dashboard**: `/dashboard/home/` - Dashboard principal (requer autenticação)

### Operações Administrativas

Todas as operações administrativas (criar, editar, excluir) requerem que o usuário seja `is_staff`.

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

---

## 🔍 Lighthouse CI - Performance Audits

O projeto inclui integração com Lighthouse CI para auditorias automatizadas de performance, acessibilidade, SEO e boas práticas.

### Executar Auditorias Localmente

#### Pré-requisitos

Certifique-se de ter instalado as dependências npm:

```bash
cd theme/static_src
npm install
```

#### Usando o Management Command (Recomendado)

O comando Django gerencia automaticamente o servidor e executa as auditorias:

```bash
# Executar auditorias em todas as URLs configuradas
python manage.py run_lighthouse

# Auditar TODAS as páginas (incluindo páginas protegidas com autenticação)
python manage.py run_lighthouse --all-pages

# Auditar URLs específicas
python manage.py run_lighthouse --url /editais/ --url /login/

# Especificar diretório de saída
python manage.py run_lighthouse --output-dir ./custom_reports

# Ajustar thresholds
python manage.py run_lighthouse --thresholds performance=0.85,accessibility=0.95

# Usar servidor já em execução
python manage.py run_lighthouse --no-server

# Pular autenticação (apenas páginas públicas)
python manage.py run_lighthouse --no-auth
```

**Opções disponíveis:**

- `--all-pages`: Auditar todas as páginas incluindo páginas protegidas (dashboard, admin, etc.). Usa superuser automaticamente
- `--url`: URL específica para auditar (pode ser usado múltiplas vezes)
- `--output-dir`: Diretório para salvar os relatórios (padrão: `./lighthouse_reports`)
- `--thresholds`: Sobrescrever thresholds no formato `performance=0.85,accessibility=0.90`
- `--port`: Porta para executar o servidor Django (padrão: 7000)
- `--no-server`: Não iniciar servidor Django (assume que já está rodando)
- `--no-auth`: Pular autenticação (apenas páginas públicas serão auditadas)

#### Usando Lighthouse CI diretamente

```bash
cd theme/static_src
npx @lhci/cli autorun
```

### Configuração

A configuração do Lighthouse CI está em `.lighthouserc.js` na raiz do projeto. Você pode:

- **Ajustar URLs auditadas**: Edite o array `url` em `ci.collect`
- **Modificar thresholds**: Edite os valores em `ci.assert.assertions`
- **Configurar via variáveis de ambiente**:
  - `LHCI_PERFORMANCE_THRESHOLD`: Threshold de performance (padrão: 0.80)
  - `LHCI_ACCESSIBILITY_THRESHOLD`: Threshold de acessibilidade (padrão: 0.90)
  - `LHCI_BEST_PRACTICES_THRESHOLD`: Threshold de boas práticas (padrão: 0.90)
  - `LHCI_SEO_THRESHOLD`: Threshold de SEO (padrão: 0.90)

### Thresholds Padrão

- **Performance**: 80+
- **Acessibilidade**: 90+
- **Boas Práticas**: 90+
- **SEO**: 90+

### CI/CD Integration

O Lighthouse CI é executado automaticamente via GitHub Actions em:

- Pull requests para `main` ou `master`
- Pushes para `main` ou `master`
- Manualmente via `workflow_dispatch`

Os relatórios são:
- Salvos como artifacts do workflow
- Comentados automaticamente em Pull Requests com os scores
- Falham o build se os thresholds não forem atingidos

### URLs Auditadas

Por padrão, as seguintes URLs são auditadas:

- `/` (home)
- `/editais/` (index)
- `/login/`
- `/register/`
- `/dashboard/home/`
- `/dashboard/editais/`
- `/health/` (health check)

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
- ✅ Management commands (8 testes)
- ✅ Admin interface (15 testes)

**Áreas que precisam de mais testes** (para atingir 85%):

- ⚠️ View `admin_dashboard()` (não testada)
- ⚠️ Método `save_model()` no Admin (sanitização XSS)
- ⚠️ Edge cases em views e models

---

## 📁 Estrutura do Projeto

```text
UniRV-Django/
├── editais/                      # App principal de editais
│   ├── management/
│   │   └── commands/
│   │       ├── seed_editais.py              # Popular banco com dados de exemplo
│   │       └── update_edital_status.py      # Atualizar status automaticamente
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
- **django-compressor 4.6.0**: Minificação de CSS/JS em produção
- **django-tailwind 3.8.0+**: Integração do Tailwind CSS com Django
  - Fornece comandos de gerenciamento: `tailwind install`, `tailwind build`, `tailwind dev`
  - Gerencia automaticamente as dependências npm do Tailwind CSS
  - **Necessário** para compilar o CSS do projeto

### Opcionais (não utilizadas atualmente)

- **Requests 2.32.3**: HTTP client
- **BeautifulSoup4 4.12.3**: Web scraping
- **Markdown2 2.5.1**: Renderização de Markdown
- **Uvicorn 0.34.0**: ASGI server

---

## 🚀 Deploy

### Preparação

1. Configure todas as variáveis de ambiente no servidor (veja `.env.example`)
2. Execute `python manage.py collectstatic` para coletar e minificar arquivos estáticos
3. Execute `python manage.py compress` para comprimir CSS/JS (se usando django-compressor)
4. Execute `python manage.py migrate` para aplicar migrações
5. Crie um superusuário: `python manage.py createsuperuser`
6. Configure Redis para cache (opcional, mas recomendado para produção)
7. Configure SSL/HTTPS com certificado válido (Let's Encrypt recomendado)

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
sudo apt install python3-pip python3-venv nginx redis-server

# Configurar Nginx como reverse proxy (veja nginx.conf.example)
# Copiar nginx.conf.example para /etc/nginx/sites-available/ypetec
sudo cp nginx.conf.example /etc/nginx/sites-available/ypetec
sudo ln -s /etc/nginx/sites-available/ypetec /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Configurar SSL com Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ypetec.unirv.edu.br

# Usar Gunicorn como servidor WSGI
gunicorn UniRV_Django.wsgi:application --bind 127.0.0.1:8000

# Configurar systemd service para Gunicorn
# (criar arquivo de serviço em /etc/systemd/system/)
```

Veja `nginx.conf.example` para configuração completa do Nginx com SSL/HTTPS.

---

## 📊 Status do Projeto

### Implementação

- ✅ **100% das funcionalidades principais implementadas**
- ✅ **34+ testes passando**
- ✅ **Otimizações de performance**: Cache, query optimization, minificação
- ✅ **Segurança**: CSRF, XSS, SQL injection prevention, security headers
- ✅ **Logging**: Rotação de logs, logs de segurança e performance
- ✅ **Produção Ready**: SSL/HTTPS, caching, monitoring
- ⚠️ **Cobertura de testes**: 69% (meta: 85%)

### Melhorias Recentes

**Data**: 2025-01-XX

- ✅ Migração completa do design React/TypeScript para Django
- ✅ Sistema de registro de usuários implementado
- ✅ Dashboard completo com todas as páginas (home, editais, projetos, usuários, avaliações, relatórios, publicações)
- ✅ Páginas públicas: Comunidade, Projetos Aprovados, Passo a Passo
- ✅ Otimização de queries: select_related/prefetch_related em todas as views
- ✅ Sistema de cache: Redis (produção) ou LocMemCache (desenvolvimento)
- ✅ Minificação de CSS/JS em produção via django-compressor
- ✅ Logging aprimorado: rotação de arquivos, logs de segurança e performance
- ✅ Configuração SSL/HTTPS com exemplo de Nginx
- ✅ Correção de vulnerabilidade XSS no Django Admin
- ✅ Melhorias no banco de dados (índices, validações)
- ✅ Arquivos de suporte completos (`.gitignore`, `.env.example`, `nginx.conf.example`)

### Próximos Passos

1. Aumentar cobertura de testes para 85%+
2. Implementar testes para views do dashboard
3. Implementar testes para registro de usuários
4. Implementar testes de segurança (CSRF, XSS, SQL injection)
5. Testes de performance (query counts)

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
