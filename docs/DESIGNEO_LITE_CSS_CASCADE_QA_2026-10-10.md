# WEB-02 · Auditoria de cascata CSS — Designeo Lite / Websign

**Data:** 2026-10-10  
**Estado:** correção **estática** validada numa cópia Windows isolada; não é validação em navegador, Gutenberg ou WordPress real.  
**Dependência:** PR #7 (Style Bridge) → esta PR incremental.

## Problema comprovado

O tema Designeo Lite v2.0.1 já continha no `assets/css/global.css` esta regra (criada antes dos componentes dinâmicos Websign):

```css
.dl-main > .wp-block-post-content > .wp-block-group:first-child,
.dl-main > .wp-block-group:first-child {
  padding-top: 0 !important;
}
```

Ela elimina o **padding superior** do primeiro `wp-block-group` em contextos `.dl-main`. O Websign Gutenberg VNext reutiliza precisamente `.wp-block-group` para uma secção, com classe semântica como `websign-section-spacing-spacious`. Por isso, quando a primeira secção dinâmica estiver nesse contexto, o `padding-top: 0 !important` tem precedência sobre o `padding-block` do novo Style Bridge, mesmo que este esteja mais abaixo no CSS.

Isto é um **conflito de seletores reproduzido estaticamente**, não observação de um website publicado com defeito.

## Correção isolada

A regra anterior foi restringida **apenas no novo candidato ZIP**, ficando equivalente a:

```css
.dl-main > .wp-block-post-content > .wp-block-group:first-child:not([class*="websign-section-spacing-"]),
.dl-main > .wp-block-group:first-child:not([class*="websign-section-spacing-"]) {
  padding-top: 0 !important;
}
```

- Os blocos nativos com `websign-section-spacing-*` deixam de ser afetados.
- Os blocos Lite tradicionais, sem essa classe, mantêm o comportamento antigo.
- **Não se introduz nenhuma regra `!important` nova**, nem se remove arbitrariamente CSS legacy.
- A alteração é feita por substituição específica, protegida contra diferenças inesperadas no CSS fonte.
- Nenhum dos ZIPs históricos nem `functions.php`, `theme.json` ou `editor.css` é modificado.

**Implementação:** `scripts/audit_lite_css_cascade_v01.py`, que compila a saída anterior da PR #7 e só altera esta regra em `assets/css/global.css`. O output fica fora do repositório e não pode sobrescrever um artefacto existente.

## Prova independente

A validação usa bibliotecas locais `tinycss2 1.5.1` e `cssselect2 0.10.1`, além das verificações de ZIP já existentes:

1. Lê as regras CSS com `tinycss2`, rejeita declarações vazias, erros de parser e chavetas mal equilibradas.
2. Compila seletores com `cssselect2` e testa a correspondência contra DOM sintético:
   - **Antes**: o seletor `padding-top:0!important` corresponde à primeira secção com `websign-section-spacing-spacious`.
   - **Depois**: deixa de corresponder a essa secção.
   - **Depois**: continua a corresponder à primeira secção Lite sem classe Websign.
3. Valida os CSS **frontend + editor**, sem mudar o conteúdo de `editor.css`.
4. Compara os ZIPs fonte e destino byte a byte, verificando que a correção afeta apenas `global.css`.
5. Confirma que o ZIP é determinístico em compilações independentes e que o builder recusa sobrescrever ficheiros.

A biblioteca cssselect2 não implementa o pseudo-elemento proprietário `::-webkit-details-marker` que existe no Lite; o validador permite **esse caso explicitamente**, mantendo a sua análise sintática via tinycss2 e testando os seletores relevantes com cssselect2. Não pressupor que um parser Python replica toda a cascata dos navegadores.

### Execução observada

- Sandbox: `C:\projetos\Websign-Lite-Audit-20261010\cascade_qa_preview`.
- **59/59 testes PASS**, exit code 0: 7 novos testes de CSS/cascata mais os 52 anteriores do percurso Lite.
- **43 ocorrências de `!important` no CSS frontend**, sem alteração de contagem. O editor mantém as suas próprias **4**; a soma do tema continua **47**. Este trabalho corrige um conflito pontual, não faz a revisão geral das 47 regras.
- Novo ZIP criado só no Windows:
  `C:\projetos\Websign-Lite-Audit-20261010\candidate_v201\designeo-lite-dynamic-cascade-safe-v0.1-preview.zip`
- SHA-256: `900943689e7dcdd577b4c86df2cdcd78e1d588cba63f0c043123a5ece8f5b8c7`.
- O candidato continua a ter **16 ficheiros**: **15 ficheiros exatamente iguais** ao ZIP da PR #7; apenas `global.css` é diferente.

## Os limites permanecem

Ainda não há prova de:
- WordPress reconhecer e editar o tema como block theme em execução, sem conflito de slug;
- estilos efetivos da cascata no Chrome/Firefox/WordPress/Gutenberg, especialmente herança e especificidade com outros plugins;
- aspeto, coerência visual, contraste, foco, responsividade, imagens/fontes e paridade com patterns PHP anteriores;
- utilização com Elementor, Contacto funcional ou pipeline de publicação para clientes.

O `wp-lab` existe mas a consulta remota WP-CLI anterior foi bloqueada por restrições de segurança; **não foi contornada**. Nenhum site, base de dados, CloudPanel, instalação de WP, original Windows ou ZIP histórico foi alterado. Todas as PRs continuam em rascunho.

## Decisão operacional sugerida

**Suspender novas abstrações e avançar para o gate visual/runtime:** antes de acrescentar mais componentes ou modelos por setor, validar a atual composição Core + Style Bridge dentro de um WordPress staging realmente isolado com backups e restauro testados, por acesso normal autorizado. Usar conteúdos fictícios e comparar frontend/editor em desktop/mobile, incluindo secção primeira com e sem `websign-section-spacing-*`.

Se o wp-lab permanecer inacessível, a solução correta é **registar a dependência de infraestrutura como bloqueio**, não declarar release nem inventar caminhos de contorno.
