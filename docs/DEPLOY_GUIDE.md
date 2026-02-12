# Guia de Deploy — AgroHub (UniRV-Django)

> Documento de referência para deploy, rollback e checklist de QA das 8 novas dependências integradas ao projeto.

---

## Sumário

1. [Pré-requisitos](#1-pré-requisitos)
2. [Ordem de Deploy (staging → production)](#2-ordem-de-deploy-staging--production)
3. [Variáveis de Ambiente Obrigatórias](#3-variáveis-de-ambiente-obrigatórias)
4. [Migrações de Banco de Dados](#4-migrações-de-banco-de-dados)
5. [Deploy com Docker Compose](#5-deploy-com-docker-compose)
6. [Deploy no Railway](#6-deploy-no-railway)
7. [Feature Flags e Rollout Gradual](#7-feature-flags-e-rollout-gradual)
8. [Rollback](#8-rollback)
9. [Checklist de QA por Dependência](#9-checklist-de-qa-por-dependência)
10. [Checklist de Revisão de Código (PR)](#10-checklist-de-revisão-de-código-pr)
11. [Perguntas Abertas para o Implementador](#11-perguntas-abertas-para-o-implementador)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Pré-requisitos

| Componente     | Versão Mínima | Verificação                       |
| -------------- | ------------- | --------------------------------- |
| Python         | 3.12          | `python --version`                |
| PostgreSQL     | 16            | `psql --version`                  |
| Redis          | 7.0           | `redis-cli ping` → `PONG`        |
| Node.js        | 20 LTS        | `node --version`                  |
| Docker Compose | 2.x           | `docker compose version`          |

---

## 2. Ordem de Deploy (staging → production)

### Fase 1 — Staging

```bash
# 1. Atualizar dependências
pip install -r requirements.txt -r requirements-dev.txt

# 2. Rodar migrações (django-celery-beat cria tabelas automaticamente)
python manage.py migrate

# 3. Coletar estáticos (inclui assets do dal_select2)
python manage.py collectstatic --noinput

# 4. Validar health check
curl -s http://localhost:8000/ht/ | python -m json.tool

# 5. Rodar testes completos
pytest -n auto --cov=editais --cov-report=term -q

# 6. Validar Celery (com USE_CELERY=True)
celery -A UniRV_Django inspect ping
celery -A UniRV_Django inspect active

# 7. Testar envio de e-mail via MailerSend (sandbox)
python manage.py shell -c "
from editais.tasks import send_welcome_email_async
send_welcome_email_async('teste@sandbox.mailersend.net', 'Usuário Teste')
"
```

### Fase 2 — Validação em Staging

- [ ] Health endpoints `/ht/` e `/health/` retornam HTTP 200
- [ ] Dashboard admin carrega com autocomplete (DAL) nos campos Tag e Edital
- [ ] Celery worker processa tasks (verificar logs + Flower)
- [ ] E-mail de boas-vindas chega (sandbox MailerSend)
- [ ] Silk não aparece em staging (a menos que `ENABLE_SILK=True`)
- [ ] Arquivos de mídia removidos ao deletar objetos (django-cleanup)
- [ ] Testes passam com cobertura ≥ 85%

### Fase 3 — Production

```bash
# 1. Configurar variáveis de ambiente de produção (ver seção 3)
# 2. Deploy via git push (Railway) ou docker compose up -d (VPS)
# 3. Rodar migrações em produção
python manage.py migrate --no-input

# 4. Validar health check
curl -sf https://seu-dominio.com/ht/ || echo "HEALTH CHECK FALHOU"

# 5. Monitorar logs do Celery worker
docker compose logs -f celery-worker --tail=50
```

---

## 3. Variáveis de Ambiente Obrigatórias

### Novas variáveis (adicionar ao ambiente de produção)

| Variável                | Obrigatória? | Exemplo                                  | Notas                                         |
| ----------------------- | ------------ | ---------------------------------------- | --------------------------------------------- |
| `CELERY_BROKER_URL`     | Sim*         | `redis://redis:6379/0`                   | *Apenas se `USE_CELERY=True`                  |
| `CELERY_RESULT_BACKEND` | Sim*         | `redis://redis:6379/0`                   | Pode ser a mesma URL do broker                |
| `USE_CELERY`            | Não          | `True`                                   | Default: `False` (fallback para threads)      |
| `MAILERSEND_API_TOKEN`  | Sim*         | `mlsn.abc123...`                         | *Apenas se usando MailerSend como backend     |
| `ANYMAIL_WEBHOOK_SECRET` | Recomendada | `whsec_...`                              | Segurança para webhooks de tracking           |
| `ENABLE_SILK`           | Não          | `False`                                  | Default: `False`. **Nunca True em produção**  |
| `FLOWER_BASIC_AUTH`     | Recomendada | `admin:senha-forte-aqui`                 | Proteção do painel Flower                     |

### Variáveis existentes (sem alteração)

`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_HOSTS` — formato já documentado em `.env.example`.

---

## 4. Migrações de Banco de Dados

### Tabelas criadas automaticamente

| App                  | Tabelas                                      | Reversível? |
| -------------------- | -------------------------------------------- | ----------- |
| `django_celery_beat` | `django_celery_beat_periodictask`, etc. (6+)  | Sim         |
| `health_check`       | Nenhuma (não usa banco)                      | N/A         |
| `dal` / `dal_select2` | Nenhuma                                     | N/A         |
| `silk`               | `silk_request`, `silk_response`, etc. (5+)   | Sim         |
| `anymail`            | Nenhuma                                      | N/A         |
| `django_cleanup`     | Nenhuma                                      | N/A         |

### Comando de migração

```bash
# Em staging/prod — sempre com --no-input em ambientes automatizados
python manage.py migrate --no-input

# Verificar migrações pendentes
python manage.py showmigrations | grep "\[ \]"
```

> **Nota**: Nenhuma migração altera tabelas existentes do app `editais`. Todas as novas tabelas são de apps terceiros, portanto **zero risco de breaking changes** nos dados existentes.

---

## 5. Deploy com Docker Compose

### Subir todos os serviços

```bash
# Produção
docker compose up -d

# Verificar status de todos os containers
docker compose ps

# Verificar saúde do sistema
docker compose exec web python manage.py check --deploy
```

### Serviços adicionados

| Serviço         | Porta   | Depende de     | Health Check                                  |
| --------------- | ------- | -------------- | --------------------------------------------- |
| `celery-worker` | —       | Redis, Postgres | `celery -A UniRV_Django inspect ping`         |
| `celery-beat`   | —       | Redis, Postgres | PID file exists                               |
| `flower`        | `5555`  | Redis          | HTTP 200 em `localhost:5555`                   |

### Escalar workers

```bash
# Aumentar workers para processar mais tasks
docker compose up -d --scale celery-worker=3
```

---

## 6. Deploy no Railway

### Build automático

O `Dockerfile` multi-stage já inclui instalação de todas as dependências. Não é necessário alterar o `railway.toml`.

### Variáveis no Dashboard Railway

Adicionar no painel **Variables** do Railway:

```env
USE_CELERY=True
CELERY_BROKER_URL=redis://<railway-redis-host>:6379/0
CELERY_RESULT_BACKEND=redis://<railway-redis-host>:6379/0
MAILERSEND_API_TOKEN=mlsn.seu-token-aqui
```

### Workers separados no Railway

Para Celery no Railway, criar um **novo serviço** apontando para o mesmo repo com override de start command:

```bash
# Start command do serviço Celery Worker
celery -A UniRV_Django worker --loglevel=info --concurrency=2

# Start command do serviço Celery Beat (opcional)
celery -A UniRV_Django beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 7. Feature Flags e Rollout Gradual

### Estratégia de ativação por feature flag

| Feature         | Flag              | Default  | Comportamento quando `False`                  |
| --------------- | ----------------- | -------- | --------------------------------------------- |
| Celery          | `USE_CELERY`      | `False`  | E-mails enviados via daemon threads (como antes) |
| Silk Profiler   | `ENABLE_SILK`     | `False`  | Silk completamente desativado (nem carrega)    |
| MailerSend      | `EMAIL_BACKEND`   | Console  | E-mails aparecem no console (dev)              |

### Plano de rollout recomendado

```
Semana 1: Deploy com USE_CELERY=False (só instalar, sem ativar)
          ↓ Monitorar: migrações OK, health checks OK, testes passando
Semana 2: Ativar USE_CELERY=True em staging
          ↓ Monitorar: Flower, logs do worker, e-mails chegando
Semana 3: Ativar USE_CELERY=True em produção
          ↓ Monitorar 48h: latência, falhas, retries no Flower
Semana 4: Ativar ENABLE_SILK=True em staging para profiling (nunca em prod)
```

---

## 8. Rollback

### Rollback rápido (sem reverter código)

```bash
# 1. Desativar Celery (volta para threads)
export USE_CELERY=False

# 2. Desativar Silk
export ENABLE_SILK=False

# 3. Reiniciar web server
docker compose restart web

# 4. Parar serviços Celery (opcionais — não afetam o app)
docker compose stop celery-worker celery-beat flower
```

### Rollback completo (reverter código)

```bash
# 1. Reverter para commit anterior
git revert HEAD --no-commit
# OU
git checkout <commit-anterior> -- requirements.txt UniRV_Django/settings.py

# 2. Reverter migrações do django-celery-beat
python manage.py migrate django_celery_beat zero

# 3. Reverter migrações do Silk (se ativado)
python manage.py migrate silk zero

# 4. Reinstalar dependências antigas
pip install -r requirements.txt

# 5. Reiniciar
docker compose up -d web
```

### Pontos de não-retorno

> **Atenção**: As seguintes ações são irreversíveis:
> - Se periodic tasks foram criadas no `django_celery_beat`, reverter a migração **deleta** esses registros
> - Dados de profiling do Silk são perdidos ao reverter
> - **Não há** alterações nas tabelas do app `editais` — rollback dos modelos é sempre seguro

---

## 9. Checklist de QA por Dependência

### 1. django-environ

- [ ] `settings.py` carrega sem erros com arquivo `.env` presente
- [ ] `settings.py` carrega sem erros **sem** arquivo `.env` (usa defaults)
- [ ] `DEBUG=False` em produção ativa validação de `ALLOWED_HOSTS`
- [ ] Variáveis sensíveis não aparecem em logs

### 2. Celery + django-celery-beat

- [ ] Worker inicia sem erros: `celery -A UniRV_Django worker --loglevel=info`
- [ ] Beat inicia sem erros: `celery -A UniRV_Django beat --loglevel=info`
- [ ] Task `send_welcome_email` executa corretamente (verificar no Flower)
- [ ] Retry automático funciona (simular falha de conexão)
- [ ] Fallback para threads funciona com `USE_CELERY=False`
- [ ] `CELERY_TASK_ALWAYS_EAGER=True` ativa corretamente nos testes
- [ ] Flower acessível em `localhost:5555` com autenticação

### 3. django-health-check

- [ ] `GET /ht/` retorna JSON com status de cada backend
- [ ] `GET /health/` (legado) continua funcionando
- [ ] DatabaseBackend reporta erro quando BD está offline
- [ ] CacheBackend reporta erro quando Redis está offline
- [ ] Health check não requer autenticação

### 4. django-autocomplete-light (DAL)

- [ ] Autocomplete de Tags funciona no admin (StartupAdmin)
- [ ] Autocomplete de Edital funciona no admin (StartupAdmin)
- [ ] Autocomplete requer autenticação (retorna 403 para anônimos)
- [ ] Busca por substring funciona (digitar 3+ caracteres)
- [ ] Assets do Select2 carregam corretamente (CSS/JS)
- [ ] `collectstatic` inclui arquivos do dal_select2

### 5. django-silk

- [ ] Com `ENABLE_SILK=False`: Silk não aparece no INSTALLED_APPS
- [ ] Com `ENABLE_SILK=True`: painel acessível em `/silk/`
- [ ] Silk requer autenticação de staff
- [ ] Profiler Python funciona (`SILKY_PYTHON_PROFILER=True`)
- [ ] **Nunca ativar em produção** (overhead de performance)

### 6. django-anymail (MailerSend)

- [ ] E-mail de boas-vindas enviado via MailerSend (verificar inbox)
- [ ] Webhook endpoint `/anymail/mailersend/tracking/` responde
- [ ] Token inválido retorna erro claro nos logs
- [ ] Fallback para console backend funciona sem token configurado

### 7. django-cleanup

- [ ] Upload de logo em Startup salva arquivo
- [ ] Alterar logo remove arquivo anterior automaticamente
- [ ] Deletar Startup remove arquivo de logo do disco/storage
- [ ] Não interfere com `easy-thumbnails` (thumbnails também limpas)

### 8. pytest + plugins

- [ ] `pytest` roda todos os testes existentes sem falhas
- [ ] `pytest -n auto` executa em paralelo sem conflitos
- [ ] `pytest --cov=editais` reporta cobertura ≥ 85%
- [ ] Fixtures do `conftest.py` (auth_client, staff_client) funcionam
- [ ] Factory fixtures via `pytest-factoryboy` estão registradas
- [ ] CI workflow usa pytest (não `manage.py test`)
- [ ] `freezegun` funciona nos testes de timestamp

---

## 10. Checklist de Revisão de Código (PR)

### Geral

- [ ] Sem secrets hardcoded (tokens, senhas, chaves)
- [ ] Todas as novas funções/métodos têm type hints
- [ ] Docstrings em português para funções públicas
- [ ] Imports organizados (stdlib → third-party → local)
- [ ] Sem `except Exception` sem tratamento adequado
- [ ] Sem `print()` — usar `logging` ou `logger`

### settings.py

- [ ] Novos `env()` calls têm defaults sensatos para desenvolvimento
- [ ] Cast types corretos (`env.bool`, `env.int`, `env.list`, `env.db`)
- [ ] `.env.example` atualizado com todas as novas variáveis
- [ ] Comentários explicam configurações não-óbvias

### Celery

- [ ] Tasks usam `@shared_task` (não `@app.task`)
- [ ] Tasks idempotentes (seguras para retry)
- [ ] `max_retries` e `retry_backoff` configurados
- [ ] `autoretry_for` lista exceções transientes (não `Exception`)
- [ ] Task time limits definidos

### Docker

- [ ] Novos serviços dependem de `db` e `redis` via `depends_on`
- [ ] Health checks configurados para novos serviços
- [ ] Volumes montados corretamente (se necessário)
- [ ] Variáveis de ambiente consistentes entre serviços

### Testes

- [ ] Novos testes seguem padrão `test_<feature>.py`
- [ ] Testes de integração marcados com `@pytest.mark.integration`
- [ ] Testes não dependem de ordem de execução
- [ ] Testes não dependem de estado externo (Redis, SMTP)
- [ ] Mocks usados para serviços externos
- [ ] Cobertura não caiu abaixo de 85%

---

## 11. Perguntas Abertas para o Implementador

> Responda estas perguntas antes do deploy em produção:

### Infraestrutura

1. **Redis compartilhado ou dedicado?** O Redis do cache (`REDIS_URL`) e o do Celery (`CELERY_BROKER_URL`) devem ser instâncias separadas em produção para isolamento? Recomendação: separar usando databases diferentes (`/0` para cache, `/1` para Celery).

2. **Monitoramento de Celery**: Flower será exposto publicamente? Se sim, configurar `FLOWER_BASIC_AUTH` e/ou colocar atrás de VPN/proxy com autenticação.

3. **Scaling de workers**: Quantos workers/concurrency para o volume esperado de e-mails? Default atual: 2 (`--concurrency=2`).

### E-mail

4. **Domínio verificado no MailerSend**: O domínio de envio (`@agrohub.unirv.edu.br` ou similar) já foi verificado no painel do MailerSend? Sem verificação, e-mails irão para spam.

5. **E-mail remetente**: Qual será o `DEFAULT_FROM_EMAIL`? Exemplo: `AgroHub <noreply@agrohub.unirv.edu.br>`.

6. **Templates de e-mail**: Os e-mails atuais usam texto simples. Migrar para templates HTML do MailerSend? Isso requer trabalho adicional.

### Segurança

7. **Webhook secret do Anymail**: Gerar um `ANYMAIL_WEBHOOK_SECRET` forte e configurar no painel do MailerSend para validação de webhooks de tracking/inbound.

8. **Silk em staging**: Haverá um ambiente de staging separado onde Silk pode ficar ativo permanentemente para profiling?

### Dados

9. **Periodic tasks pré-definidas**: Existem tarefas periódicas que devem ser criadas no `django_celery_beat` logo após o deploy? Exemplo: limpeza de sessões, relatórios diários, etc.

10. **Retenção de dados do Silk**: Se ativado, por quanto tempo manter os dados de profiling? Configurar um cron/task para limpeza periódica.

---

## 12. Troubleshooting

### Celery worker não inicia

```bash
# Verificar se Redis está acessível
redis-cli -u $CELERY_BROKER_URL ping

# Verificar se as migrações rodaram
python manage.py showmigrations django_celery_beat

# Iniciar em modo verbose
celery -A UniRV_Django worker --loglevel=debug
```

### Health check retorna erro

```bash
# Verificar cada backend individualmente
python manage.py shell -c "
from health_check.backends import BaseHealthCheckBackend
from health_check.db.backends import DatabaseBackend
db = DatabaseBackend()
db.run_check()
print(db.pretty_status())
"
```

### Autocomplete não carrega no admin

```bash
# Verificar se collectstatic incluiu os assets
python manage.py collectstatic --noinput
ls staticfiles/autocomplete_light/
ls staticfiles/admin/js/vendor/select2/

# Verificar URLs registradas
python manage.py show_urls | grep autocomplete
```

### E-mail não chega via MailerSend

```bash
# Testar conexão com API
python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Teste', 'Corpo do teste', None, ['seu-email@teste.com'])
"

# Verificar logs do Anymail
# Os erros de API aparecem como AnymailRequestsAPIError nos logs
```

### Silk não aparece

```bash
# Verificar se está ativado
python manage.py shell -c "
from django.conf import settings
print('silk' in settings.INSTALLED_APPS)
print(getattr(settings, 'ENABLE_SILK', False))
"
```

---

## Referências

- [Celery — Getting Started with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-celery.html)
- [django-environ — Docs](https://django-environ.readthedocs.io/)
- [django-health-check — GitHub](https://github.com/revsys/django-health-check)
- [django-autocomplete-light — Tutorial](https://django-autocomplete-light.readthedocs.io/)
- [django-silk — GitHub](https://github.com/jazzband/django-silk)
- [django-anymail — MailerSend](https://anymail.dev/en/stable/esps/mailersend/)
- [django-cleanup — GitHub](https://github.com/un1t/django-cleanup)
- [pytest-django — Docs](https://pytest-django.readthedocs.io/)
