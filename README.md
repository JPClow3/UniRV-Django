# UniRV Django - AgroHub

Sistema de gerenciamento de editais de fomento para o AgroHub UniRV.

## 🚀 Setup Rápido

### 1. Clone o repositório
```bash
git clone <repository-url>
cd UniRV-Django
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv .venv
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
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edite o arquivo `.env` e configure:
- `SECRET_KEY`: Gere uma nova chave secreta (veja instruções abaixo)
- `DJANGO_DEBUG`: Mantenha `True` apenas em desenvolvimento
- `ALLOWED_HOSTS`: Configure os domínios permitidos em produção

#### Gerando uma SECRET_KEY segura:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Execute as migrações
```bash
python manage.py migrate
```

### 6. (Opcional) Popular o banco com dados de exemplo
```bash
python manage.py seed_editais

### 7. (Opcional) Atualizar status dos editais automaticamente

O sistema inclui um management command para atualizar automaticamente o status dos editais baseado nas datas:

```bash
python manage.py update_edital_status
```

**Opções:**
- `--dry-run`: Executa sem fazer alterações (apenas mostra o que seria alterado)
- `--verbose`: Mostra informações detalhadas sobre cada edital atualizado

**Configuração para execução automática (cron/task scheduler):**

Para executar diariamente, adicione ao crontab (Linux) ou Task Scheduler (Windows):

```bash
# Linux (crontab -e)
0 0 * * * cd /path/to/UniRV-Django && /path/to/venv/bin/python manage.py update_edital_status

# Windows Task Scheduler
# Criar tarefa agendada para executar diariamente:
# python manage.py update_edital_status
```
```

### 7. Crie um superusuário
```bash
python manage.py createsuperuser
```

### 9. Inicie o servidor
```bash
python manage.py runserver
```

Acesse: http://127.0.0.1:8000/

## 🔒 Segurança

### Melhorias de Segurança Implementadas

✅ **SECRET_KEY em variável de ambiente**
- Nunca commit a `SECRET_KEY` no código
- Use `.env` para desenvolvimento local
- Configure variáveis de ambiente no servidor de produção

✅ **ALLOWED_HOSTS configurado corretamente**
- Em desenvolvimento: `localhost`, `127.0.0.1`, `[::1]`
- Em produção: especifique seus domínios no `.env`

✅ **Arquivo .env no .gitignore**
- Garante que credenciais não sejam commitadas

✅ **Dependências completas**
- Todas as bibliotecas necessárias estão no `requirements.txt`
- Inclui `bleach==6.1.0` para sanitização de HTML

### Checklist de Segurança para Produção

Antes de fazer deploy em produção, certifique-se de:

- [ ] `DEBUG=False` no ambiente de produção
- [ ] `SECRET_KEY` única e segura configurada
- [ ] `ALLOWED_HOSTS` configurado com seus domínios
- [ ] HTTPS habilitado
- [ ] Database backup configurado
- [ ] Logs de aplicação monitorados
- [ ] Atualizar dependências regularmente: `pip list --outdated`

## 📦 Dependências

- **Django 5.2.7**: Framework web
- **WhiteNoise 6.7.0**: Servir arquivos estáticos
- **Requests 2.32.3**: HTTP client
- **BeautifulSoup4 4.12.3**: Web scraping
- **Markdown2 2.5.1**: Renderização de Markdown
- **Bleach 6.1.0**: Sanitização de HTML
- **Gunicorn 23.0.0**: WSGI server (produção)
- **Uvicorn 0.34.0**: ASGI server

## 🧪 Testes

Execute os testes:
```bash
python manage.py test editais
```

**Cobertura de Testes:**
- 28 testes implementados cobrindo:
  - CRUD de editais (7 testes)
  - Busca e filtros (6 testes)
  - Detalhes e redirecionamento (4 testes)
  - Modelos (slug, validação, status) (5 testes)
  - Formulários (6 testes)
  - Management commands (testes em `editais/tests/test_management_commands.py`)

**Verificar cobertura (requer `coverage`):**
```bash
pip install coverage
coverage run manage.py test editais
coverage report
```

## 📁 Estrutura do Projeto

```
UniRV-Django/
├── editais/              # App principal de editais
│   ├── management/
│   │   └── commands/
│   │       └── seed_editais.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── tests.py
├── UniRV_Django/         # Configurações do projeto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/            # Templates HTML
├── static/               # Arquivos estáticos (CSS, JS, imagens)
├── requirements.txt      # Dependências do projeto
├── .env.example          # Exemplo de variáveis de ambiente
├── .gitignore           # Arquivos ignorados pelo Git
└── manage.py            # Utilitário de gerenciamento Django
```

## 🚀 Deploy

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

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

[Adicionar licença aqui]

## 👥 Autores

UniRV - Universidade de Rio Verde

