# WEB-02 · Designeo Lite Dynamic Style Bridge v0.1

**Data:** 2026-10-10  
**Estado:** candidato ZIP isolado gerado e validado estaticamente; **sem renderização verificada dentro de WordPress, sem aprovação visual, sem publicação**.  
**Objetivo:** aproveitar o renderizador Gutenberg e os slots do Websign sem criar um segundo motor de edição, e alinhar os seus estilos com o `theme.json` do **Designeo Lite Core**.

## Ponto de partida confirmado

O Websign VNext, disponível no workspace Windows, já inclui:
- `websign_vnext.validation.validate_site_document`;
- `websign_vnext.renderers.gutenberg.render_site_document`, que gera blocos nativos e classes `websign-...`;
- `websign_vnext.tokens.TOKEN_ENUMS` com **24 combinações semânticas**: espaçamentos, fundos, larguras/alinhamentos, gaps, hierarquia de títulos, papel de parágrafos e tipos de botão;
- `websign_vnext/runtime/websign.css`, um runtime genérico próprio. Este runtime **não foi copiado integralmente** para o Designeo Lite.

O Lite Core v0.1 já carrega:
- `assets/css/global.css` no frontend via `wp_enqueue_style()` em `functions.php`;
- `assets/css/editor.css` através do suporte `editor-styles` e `add_editor_style()`.

Esta foi a oportunidade de integração: **um adaptador pequeno de CSS semântico**, com classes do Websign mas valores associados aos *design tokens* Lite, na mesma infraestrutura do tema, sem nova API, JS ou renderer.

## O que foi implementado

`Templates/lite-runtime-overlay/assets/css/websign-lite-bridge.css` define as 24 classes reconhecidas pelo Websign, incluindo:
- `websign-section-spacing-none/compact/normal/spacious`;
- `websign-section-background-surface/muted/inverse`;
- `websign-container-width-narrow/content/wide` e alignment left/center;
- `websign-columns-gap-compact/normal/spacious`;
- `websign-heading-role-display/section/subsection`;
- `websign-paragraph-role-body/lead/muted`;
- `websign-button-style-primary/secondary/outline`.

Os fundos e a tipografia utilizam `--wp--preset--color-*` e `--wp--preset--font-size-*` existentes no `theme.json` da v2.0.1. O layout combina presets de espaçamento com os limites de largura do tema. A overlay inclui regras responsivas para 768px/480px, foco visível nos botões e estado de botão principal em fundo inverso. **Não acrescenta `!important`, fontes remotas, imports ou URLs externos.**

O builder `scripts/build_lite_dynamic_core_v01.py` lê o Core gerado a partir dos ZIPs originais e cria uma nova cópia, acrescentando a mesma overlay aos **dois CSS já carregados**. Preserva os restantes 14 ficheiros sem alterações, incluindo `functions.php`, `theme.json`, header/footer, templates Gutenberg e JS existente.

O builder recusa ficheiro de saída pré-existente, valida classes reconhecidas, sintaxe básica de braces e referências de presets à paleta real. **Não comprova em navegador** especificidade, cascata, métricas visuais, reconhecimento de blocos ou estilos de outros plugins.

## Prova executada no Windows NPC

Sandbox `C:\projetos\Websign-Lite-Audit-20261010\dynamic_style_preview`, com código exato da branch e `websign_vnext` nativo importado do workspace Windows (apenas leitura):

- **52/52 testes PASS**, código de saída 0. Incluem 7 novos testes da overlay e os 45 anteriores de slots/Gutenberg/Core/seleção.
- **24/24 classes Websign** previstas nos `TOKEN_ENUMS` são cobertas pelos seletores da overlay; não são permitidas classes extra desconhecidas.
- Todas as referências a presets de cor, fonte e espaçamento existem no `theme.json` Lite (erros obrigam bloqueio).
- Os dois ficheiros CSS originais recebem o mesmo bloco claramente delimitado; **os restantes 14 ficheiros permanecem byte a byte idênticos**; `functions.php` não foi alterado.
- O artefacto é reprodutível byte a byte em duas compilações isoladas.
- O preflight estrutural não encontra botões/imagens placeholders no Core, mas mantém `release_ready: false`. Os patterns opcionais continuam a exigir edição.

### Artefacto produzido

`C:\projetos\Websign-Lite-Audit-20261010\candidate_v201\designeo-lite-dynamic-core-v0.1-preview.zip`

SHA-256: `a904bad667e75d17c671a085bd5abfcec9e8ba301ef44b86357e2652ecd1a35c`.

Contém **16 ficheiros**, tal como o Core anterior, com apenas `assets/css/editor.css` e `assets/css/global.css` ajustados. É **um candidato de sandbox, não um tema final de produção**. Não foi carregado no GitHub como ZIP nem instalado em WordPress.

## Delimitação técnica importante

Há **três camadas distintas**:

1. **SiteDocument → Lite Component Slots** (PR #6): valida, preserva copy/links/media ou bloqueia estrutura com perda.
2. **Websign VNext Gutenberg renderer** (já existente no Windows): produz HTML de blocos editáveis, e classes semânticas `websign-...`.
3. **Lite Dynamic Style Bridge** (esta PR): faz essas classes resolverem para tokens de design do Lite no CSS de frontend e do editor.

Isto permite uma hipótese testável de Gutenberg com conteúdo original + estilo Lite. **Ainda não é equivalência visual com os antigos patterns PHP**, nem os transforma em templates dinâmicos. Não usa os patterns estáticos para interpolar conteúdo; preserva a biblioteca apenas como referência/editorial. Também não resolve automaticamente o caso Hero+imagem, bloqueado pela capacidade atual, nem os fluxos de formulário de contacto.

O CSS global da v2.0.1 já contém regras `!important` anteriores; esta overlay **não acrescenta novas**, mas a sua compatibilidade e a especificidade precisam de verificação em WordPress. As fontes nomeadas da v2.0.1 não estão empacotadas, e a licença `Proprietary` exige revisão jurídica/comercial antes de distribuição.

## Gates para aprovação

1. **QA de sintaxe CSS via parser independente**, adicional à validação simples atual, e revisão das regras globais que podem sobrepor a bridge.
2. Teste de dois documentos controlados: um com Hero sem imagem + CTA, outro com Serviços/Sobre; comparar saída Gutenberg no frontend e editor em desktop/mobile, foco/contraste, media e tipografia, com screenshots de staging autorizadas.
3. Confirmar instalação em `wp-lab` **somente por canal permitido**: isolamento, backups/restore e ausência de colisão do slug `designeo-lite-base`. A consulta WP-CLI anterior foi bloqueada por segurança, sem contorno.
4. Corrigir lacunas do catálogo (Hero com imagem, componentes multi-coluna diversos, contacto funcional) antes de modelos setoriais.
5. Rever com o Design Agent os tokens e a escala visual final do **Designeo Lite mínimo**, mantendo o website editável em Gutenberg e o alojamento/maintenance separado.

**Não realizado:** deploy, merge das PRs #2–#7, visual QA, WordPress runtime, alteração de sites/servidor ou modificação dos ZIPs originais; os resultados permanecem em rascunho.

**Sequência das PRs:** #2 fallback → #3 normalização/release preflight → #4 Lite Core + Library → #5 SiteDocument seleção → #6 slots + renderer nativo → **esta PR: style bridge v0.1**.
