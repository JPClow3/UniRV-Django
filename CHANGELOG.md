# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-02-12

### Changed
- Updated .gitignore environment file pattern for better clarity
- Renamed .env.docker to .env.docker.example to prevent accidental commits
- Updated .dockerignore to include README.md in container
- Enhanced pytest.ini with testpaths and strict configuration
- Added Python files to .gitattributes for consistent line endings
- Improved cookie domain validation in settings.py
- Expanded conftest.py with additional test fixtures
- Added rationale comments to requirements.txt for version constraints
- Reorganized testing documentation to docs/testing/ subdirectory

### Fixed
- Fixed .env file tracking confusion in version control
- Improved documentation organization and consistency

## [1.0.0] - 2025-01-15

### Added

#### Core Features
- Sistema completo de gerenciamento de editais de fomento
- Dashboard administrativo com estatísticas e gerenciamento
- Sistema de busca avançada com full-text search (PostgreSQL)
- Sistema de autenticação e autorização
- Gerenciamento de startups/projetos aprovados
- Histórico de alterações com django-simple-history

#### Models
- **Edital**: Modelo principal para editais de fomento
  - Campos de conteúdo (análise, objetivo, etapas, recursos)
  - Sistema de status (draft, programado, aberto, fechado)
  - Slug único para URLs amigáveis
  - Validação de datas
  - Sanitização HTML para segurança
- **EditalValor**: Valores financeiros com suporte a múltiplas moedas
- **Cronograma**: Cronograma de atividades do edital
- **Startup**: Modelo para startups incubadas
  - Categorias (AgTech, BioTech, IoT, EdTech)
  - Status de incubação (pré-incubação, incubação, graduada, suspensa)
  - Upload de logos
- **Tag**: Sistema de tags para categorização flexível

#### Database Features
- Índices otimizados para performance
- Full-text search com PostgreSQL
- Trigram indexes para busca fuzzy
- Constraints de validação no banco de dados
- Unique constraints em slugs e valores

#### Frontend
- Interface moderna com Tailwind CSS v4
- Design responsivo (mobile, tablet, desktop)
- Animações suaves e loading states
- JavaScript vanilla (sem frameworks)
- Minificação de assets (CSS/JS)

#### Security
- Proteção XSS (sanitização HTML com bleach)
- Proteção CSRF
- Rate limiting
- Headers de segurança (HSTS, X-Frame-Options, etc.)
- Validação de uploads de arquivos
- Sessões seguras (HttpOnly, Secure, SameSite)

#### Performance
- Cache de páginas e consultas (Redis/LocMemCache)
- Otimização de queries (select_related, prefetch_related)
- Minificação de CSS/JS
- Connection pooling (PostgreSQL)
- Índices otimizados no banco de dados

#### Infrastructure
- Docker multi-stage build
- Docker Compose configuration
- Nginx reverse proxy setup
- Gunicorn WSGI server configuration
- CI/CD com GitHub Actions
- Lighthouse CI para auditorias de performance

#### Documentation
- README.md completo
- Documentação de testes
- Revisão do banco de dados
- Revisão de migrações
- Documentação de arquitetura

### Changed

- Modelo Project renomeado para Startup (migration 0028)
- Tabela `editais_project` renomeada para `editais_startup` (migration 0022)
- Logo field mudado de ImageField para FileField para suportar SVG (migration 0023)
- Sistema de histórico: EditalHistory removido, substituído por django-simple-history (migration 0021)
- Campos de texto opcionais agora permitem null (migration 0016)

### Fixed

- **CRITICAL**: Conflito de related_name no modelo Startup (migration 0024)
  - `proponente.related_name` alterado de 'startups' para 'startups_owned'
- Validação de datas no modelo Edital
- Validação de arquivos no modelo Startup
- Constraints de unicidade em EditalValor (migration 0025)
- Validação de datas no Cronograma (migration 0026)
- Check constraints para validação de datas (migration 0027)

### Security

- Sanitização HTML em todos os campos de conteúdo
- Validação de tamanho e tipo de arquivo em uploads
- Headers de segurança habilitados em produção
- Rate limiting em views críticas
- Proteção contra SQL injection (Django ORM)

## [Unreleased]

### Planned

- API REST para integração externa
- Sistema de notificações
- Exportação de dados (PDF, Excel)
- Dashboard de analytics avançado
- Sistema de comentários em editais

---

## Migration History Summary

### Initial Setup (0001-0004)
- Criação dos modelos base (Edital, EditalValor, Cronograma)
- Adição de campos de análise
- Sistema de favoritos (deprecated)
- Índices iniciais

### Slug System (0005-0006)
- Adição de slugs únicos
- Data migration para popular slugs existentes
- Expansão de status choices

### History System (0007-0008, 0021)
- Criação de EditalHistory (deprecated)
- Melhorias no sistema de histórico
- Substituição por django-simple-history

### Project/Startup Evolution (0010-0014, 0028-0029)
- Criação do modelo Project
- Transformação em Startup
- Adição de categorias e descrições
- Sistema de slugs e logos
- Renomeação final para Startup

### Database Optimizations (0018-0020)
- Habilitação da extensão pg_trgm
- Índices trigram para busca fuzzy
- Índice full-text search

### Data Integrity (0025-0027)
- Unique constraint em EditalValor
- Validação de datas no Cronograma
- Check constraints no banco

### Bug Fixes (0024)
- Correção do conflito de related_name

---

## Versioning

- **Major version** (1.x.x): Breaking changes
- **Minor version** (x.1.x): New features (backward compatible)
- **Patch version** (x.x.1): Bug fixes (backward compatible)

---

**Note**: This changelog is maintained manually. For detailed migration history, see `editais/migrations/`.
