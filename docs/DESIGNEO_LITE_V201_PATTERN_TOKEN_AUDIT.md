# WEB-01 · Designeo Lite v2.0.1 — normalização de tokens de patterns

**Estado:** candidato ZIP local isolado, nove testes unitários em verde. **NÃO validado num WordPress real, NÃO aprovado visualmente, NÃO pronto para clientes.**

## Porque é necessária esta etapa

A auditoria aos cinco patterns da v2.0.1 confirmou que eram **iguais aos da v1.1**, mas `theme.json` foi redesenhado na v2. O resultado são referências inexistentes a cores (ex. `fundo`, `texto-suave`, `borda`), fontes (`medio`, `grande`) e espaçamentos (`7`, `9`). O ZIP 2.0.1 também não contém `templates/index.html`.

Há mais um risco funcional: `patterns/contact.php` contém literalmente `<form action="#" method="post">`, sem integração comprovada para receber/envio de mensagens. **Não deverá ser apresentado como formulário operacional.**

## Estratégia adotada

Este candidato é gerado programaticamente, **sem editar os ZIPs do histórico**:

1. Lê apenas `Templates/designeo-lite-v1.1.zip` e `Templates/designeo-lite-v2.0.1.zip` para obter dicionários de tokens e conteúdos. A v2.0.1 é protegida por SHA-256 esperado.
2. Substitui referências WP reais (`var:preset|...`, `var(--wp--preset--...)`, atributos de blocks e classes `has-...`) por tokens v2 existentes, com mapeamento explícito.
3. Usa a correção isolada do `templates/index.html` definida na [PR #2](https://github.com/Digitransarte/websign-designeo/pull/2).
4. **Exclui o pattern Contacto demonstrativo do ZIP experimental**: o sistema não deve prometer um formulário que não envia.
5. Valida referências dos quatro patterns, estruturas de comentários Gutenberg, integridade do ZIP e igualdade byte a byte dos ficheiros preservados. Recusa sobrescrever ZIPs existentes.

## Mapeamento de compatibilidade

| Tipo | Exemplos v1.1 → v2.0.1 |
|---|---|
| Cores | `fundo → surface`, `fundo-suave → surface-alt`, `fundo-escuro → surface-inverse`, `texto-suave → on-surface-muted`, `borda → border` |
| Fonte | `medio → lg`, `grande → xl`; os `2xl/3xl/4xl` antigos mudam de nome para `3xl/4xl/5xl` respetivamente para manter aproximadamente o tamanho |
| Espaçamento | `7 → 8` (64px), `8 → 12` (96px), `9 → 16` (128px); os restantes seguem os valores físicos antigos sempre que possível |

**Exceção conhecida:** o espaçamento antigo `2` tinha 12px e a escala v2 não possui 12px. A opção provisória é `2` (16px); requer QA visual. Em geral, preservar tamanho aproximado **não significa que seja esta a composição final do Designeo Lite**. A limpeza de regras globais `!important` do CSS não foi realizada.

## Resultado observado — Windows NPC

Criado ZIP apenas no workspace de auditoria:

`C:\projetos\Websign-Lite-Audit-20261010\candidate_v201\designeo-lite-v2.0.1-token-aligned-preview.zip`

**SHA-256:** `49f1188f124129f895b1b5adbf66194da3ffaa1091e6e28497fc9476f628ba3f`.

| Verificação | Resultado |
|---|---|
| 20 ficheiros no ZIP de origem | Confirmado |
| 15 ficheiros byte a byte idênticos | Confirmado |
| 4 patterns corrigidos: Hero, Serviços, Sobre, CTA | Confirmado |
| 1 pattern demonstrativo excluído: Contacto | Confirmado |
| 1 novo `templates/index.html` | Confirmado |
| Ficheiros finais | 20 |
| Referências a tokens indefinidos nos 4 patterns incluídos | **0** |
| Testes executados | **9/9 PASS** (`4` da PR #2 + `5` novos), exit code 0 |
| WordPress instalado / editor Site Editor testado | **Não** |
| PHP lint / render real / screenshot / QA mobile | **Não** |
| Formulário de contacto funcional | **Não incluído** |
| Produção, hosting ou temas WordPress alterados | **Não** |

## Sequência de PRs (sem merge)

- [PR #2](https://github.com/Digitransarte/websign-designeo/pull/2): fallback `templates/index.html`, isolado, mas não suficiente por si só.
- **Esta branch:** `feature/designeo-lite-token-compat-v201`, proposta incremental sobre a PR #2; normalização dos quatro patterns, exclusão do formulário demonstrativo e testes.

Nenhuma destas PRs deve ser integrada como release final sem revisão. O ZIP candidato está **só no Windows**, fora do repositório GitHub.

## Próximo gate: WordPress staging seguro

Não contornar a restrição que bloqueou a anterior consulta de wp-lab via Remote Desktop. Quando o acesso normal permitido estiver disponível, confirmar que é realmente ambiente de testes, fazer backup/restore e inventário de temas, evitar conflito da pasta `designeo-lite-base`, testar reconhecimento full-site-editing, editor de patterns, templates, front/back, mobile, contraste/foco e compatibilidade do Websign.

Somente depois decidir que tokens, blocos e patterns devem permanecer no **Designeo Lite mínimo**. O formulário de contacto real será uma integração validada mais tarde, não um HTML sem backend.
