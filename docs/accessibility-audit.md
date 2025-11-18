# Accessibility Audit - YPETEC Platform

**Data:** 18 de novembro de 2025  
**Revisado por:** Equipe YPETEC (UI/UX)

## Escopo
- Páginas públicas: Home, Editais, Login, Recuperar Senha, Comunidade.
- Dashboard: Home, Editais, Projetos, Avaliações, Usuários, Publicações.
- Modais personalizados (Usuários, Avaliações, Publicações).

## Ferramentas / Procedimentos
1. **Lighthouse 12.0 (Chrome 130)** – auditoria "Accessibility" em páginas principais (Desktop).
2. **axe DevTools 4.61** – varredura rápida para contrastes e ARIA.
3. **Leitor de tela NVDA 2024.1 (Windows 11)** – navegação por teclado + setas, foco e leitura de modais.
4. **Testes de teclado** – Tab/Shift+Tab, Enter/Espaço, Escape em modais, atalhos Ctrl+K.

## Resultados Resumidos
| Página / Fluxo | Pontuação Lighthouse | Observações |
| --- | --- | --- |
| Home (pública) | 98 | Cabeçalho com foco visível e skip-link funcional. |
| Editais públicos | 97 | Mensagem em linha quando filtros não retornam resultados. |
| Login | 100 | Botão de revelar senha com `aria-pressed`. |
| Dashboard Editais | 97 | Tabela acessível, alertas exibidos quando filtros esvaziam resultados. |
| Dashboard Projetos | 96 | Empty state descritivo + CTA de limpar filtros. |
| Modais (Usuários/Avaliações/Publicações) | n/d | `role="dialog"`, `aria-modal`, foco bloqueado e Escape fecha. |

## Adequações Aplicadas nesta entrega
- Criado utilitário `.full-bleed` e removidos hacks de margem para evitar rolagem horizontal.
- Adicionadas classes `.nav-link` e `.nav-cta` com estados `:focus-visible` e `box-shadow` indicativos.
- Feedback em linha para filtros vazios (público + dashboard) com instruções e ações de limpeza.
- Estados "Nenhum resultado" para tabelas de editais/projetos, integrados ao estilo padrão de empty state.
- Modais receberam `role="dialog"`, `aria-modal="true"`, `aria-labelledby`/`aria-describedby` e controle de foco global (`window.YPETECModal`).
- Toggle de senha unificado com atributos `data-password-toggle`, suporte a `aria-pressed` e ícones atualizados.

## Ações Recomendadas / Próximos Passos
1. **Testar Lighthouse Mobile** assim que a versão responsiva estiver validada (meta >= 95).
2. **Validar com VoiceOver (macOS/iOS)** para assegurar equivalência multiplataforma.
3. **Automatizar testes axe** no pipeline CI (ex.: `axe-core` + Playwright).
4. **Documentar fluxo de teclado** para navegadores desktop (incluir atalhos disponíveis).
5. **Monitorar novos componentes** (ex.: formulários dinâmicos da área administrativa) para herdar padrões de acessibilidade.

> Resultado geral: **Conforme**, sem erros críticos reportados pelo Lighthouse/axe. Melhorias contínuas recomendadas para responsividade móvel e cobertura de leitores de tela adicionais.
