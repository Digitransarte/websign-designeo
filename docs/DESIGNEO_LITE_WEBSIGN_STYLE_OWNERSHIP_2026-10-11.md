# WEB-02 · Designeo Lite / Websign Runtime — propriedade dos estilos v0.1

**Data:** 11/10/2026. **Estado:** candidato validado estaticamente, em PHP e **num clone WordPress real descartável**. **Não está ativado no wp-lab público nem aprovado visualmente.**

## Contexto

No `wp-lab.designeo.pt`, o plugin **Websign Runtime v0.1.0** está ativo e carrega `assets/websign.css` no frontend e nos recursos do editor. O tema candidato **Designeo Lite** já implementa a sua própria Dynamic Style Bridge para os mesmos blocos nativos Gutenberg. A auditoria do servidor identificou **22 classes `websign-*` presentes em ambos os runtimes**, incluindo botões, fundos, tipografia, espaçamento e larguras. Alguns valores diferem, como raio dos botões e tamanhos.

A versão anterior, [PR #8](https://github.com/Digitransarte/websign-designeo/pull/8), resolveu o conflito CSS de `padding-top:0!important` no primeiro bloco, mas não resolvia a dupla origem das regras do Runtime.

## Contrato

- **Se Twenty Twenty-Five ou outro tema estiver ativo:** o plugin Websign Runtime mantém as suas folhas de estilo e os casos Gutenberg antigos continuam a funcionar.
- **Se Designeo Lite estiver ativo:** a **Bridge do Lite** é a autoridade para as classes `websign-*`; não carregar em simultâneo `websign-runtime` CSS do plugin, sem desinstalar/desativar/modificar o plugin.
- **Frontend e Gutenberg editor** seguem a mesma regra. Não é necessária uma variante do SiteDocument nem um segundo renderer.
- Preservar o Lite minimalista, sem CSS remoto, `!important` adicional ou alterações a templates/Patterns/tokens que não sejam necessárias.

## Implementação

**Builder:** `scripts/build_lite_websign_style_ownership_v01.py`, sobre a PR #8. Gera ZIP **isolado, determinístico**, 16 ficheiros. Muda apenas:
- `functions.php`: acrescenta a função `designeo_lite_own_websign_styles()`, que executa `wp_dequeue_style( 'websign-runtime' )`; é chamada com prioridade 1000 nos hooks `wp_enqueue_scripts` e `enqueue_block_editor_assets`. A função é carregada **só se o próprio tema Lite estiver ativo**.
- `assets/css/global.css` e `assets/css/editor.css`: acrescenta apenas fallbacks mobile `@media(max-width:768px)` para as **três classes específicas** de `websign-columns-gap-*`, com `flex-direction: column` e `flex-basis: auto`. Compensam a perda do comportamento mobile do plugin Websign quando o Lite passa a ser responsável por estes blocos.
- Os outros **13 ficheiros** não foram alterados. Não houve alterações à implementação do plugin nem aos ZIPs originais.

O script recusa substituição de artefactos existentes, erro de conteúdo inesperado e `!important` novo. Continua a produzir um candidato: não ativa WordPress.

### ZIP isolado gerado no Hetzner

```text
/home/wp-lab/tmp/designeo-lite-builds-20261011/designeo-lite-style-owner-v0.1-preview.zip
```

SHA-256 do ZIP Linux: `9e43838ea96d6ae5332a321836ccdbf51faf5bc9ed94e6b09d1a95da55a760c7`, **16 ficheiros**; `unzip -t` PASS; PHP 8.4 lint PASS. O ZIP está numa pasta temporária privada do servidor, **não** no diretório público de temas.

## Testes automatizados

- `tests/test_lite_websign_style_ownership_v01.py`: **6 novos testes PASS** (mudanças apenas nas três entradas esperadas, preservação de hooks, CSS mobile/parse, build determinístico, proteção contra output no repositório, lint PHP + simulação de ordem `priority=10/1000` em frontend/editor).
- **Hetzner Linux:** `python -m unittest discover -s tests -p 'test_lite_*.py' -q` → `Ran 65 tests ... OK (skipped=7)`. O código local original `websign_vnext` não está completo nesta cópia de GitHub, daí a diferença de skip.
- **Windows NPC**, com `PYTHONPATH` para o módulo local original de Websign em `C:\projetos\websign-designeo` (sem o publicar): `Ran 65 tests ... OK (skipped=1)`. Não houve erros. O script e o tema originais permanecem isolados.

## Teste WordPress real — clone privado e descartável

Criado de novo a partir do **conjunto local de backup já comprovado** no WEB-04 (ficheiros completos + SQL).

- Diretório temporário privado `/home/wp-lab/tmp/designeo-lite-owner-proof.*`.
- MariaDB isolada `--skip-networking`, socket Unix próprio.
- Servidor PHP ligado **apenas a 127.0.0.1:18797**.
- `wp-config.php` da **cópia** substituído por configuração temporária antes de carregar PHP WordPress; cron/updates externos bloqueados.
- Na BD **clonada**, plugin Websign Runtime ativo e inicialmente tema Twenty Twenty-Five.
- **Baseline:** página inicial HTTP 200, HTML continha referência ao stylesheet do plugin `websign-runtime/assets/websign.css`, confirmando que plugin funcionava no clone.
- Descompactado ZIP novo **somente dentro do clone**, instalado no slug de tema `designeo-lite-lab-v01`; ativo **somente na BD clonada**.
- **Lite clone:** página inicial HTTP 200, HTML inclui `designeo-lite-global-css` e **não inclui** a stylesheet do plugin.
- **Editor:** execução da action `enqueue_block_editor_assets` dentro de WP carregado em PHP confirmou que o handle do plugin **não permanece enqueued** e que o Lite **regista `assets/css/editor.css`**. **Não** foi um teste visual ou de edição autenticada no navegador.
- Cleanup confirmado: **zero** diretórios temporários, sockets de teste e listeners na porta.
- WordPress público `wp-lab.designeo.pt`: **HTTP 200**, **Twenty Twenty-Five ativo**, plugin Websign Runtime CSS continua presente; pasta Lite ativa em produção **não** foi alterada.

**Resultado:** a regra de propriedade dos estilos foi provada na aplicação WordPress real, sem impactar o site existente. A forma final no editor e nos breakpoints ainda não foi aprovada.

## Gates antes de ativar no wp-lab

1. **QA visual de frontend e Gutenberg real:** páginas com Hero, Services, About, CTA, botões, imagem/alt, layout 320/375/768/1024/1440, contraste e foco; verificar a saída exata do renderer nativo Websign em vez de confiar apenas em seletores.
2. **Pré-visualização com tema Lite num staging que suporte navegador/editor** sem alterar o blog de casos Gutenberg. O clone CLI acima não substitui edição com login autenticado.
3. Testar versões/fontes/licenças, navegação, comportamento dos PHP patterns opcionais apenas com copy real aprovada, SEO e acessibilidade.
4. Resolver no WEB-04 a gestão de backups **pré-mudança** e atualizações autorizadas; o backup SQL da madrugada não satisfaz um snapshot coerente imediatamente antes de uma ativação real.
5. Só depois ativar e recolher aprovação visual; as PRs continuam **Draft**, sem merge.

**Não criar modelos setoriais WEB-03 antes do tema base ser provado no WordPress.**
