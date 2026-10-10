# WEB-02 · SiteDocument → seleção de patterns Designeo Lite v0.1

**Data:** 2026-10-10 · **Estado:** integração **local e read-only** testada; sem import/publicação WordPress, sem revisão visual e sem transferência automática de conteúdo.

## Resultado concreto

Foi acrescentado um adaptador `scripts/plan_lite_patterns_from_site_document_v01.py` que recebe:
- `SiteDocument` **v0.1** de Websign, com `schema_version: websign.site.v0.1`;
- manifesto da **Lite Pattern Library v0.1** (4 componentes Hero, Serviços, Sobre e CTA, `publish_ready:false`);
- o **validador nativo do Websign VNext** como callable obrigatório. **Não inclui outra cópia do Websign VNext no GitHub.**

A saída é um `designeo.lite.selection.v0.1`: um plano por página e secção, sem transcrever textos, títulos, nomes de clientes, destinos de links nem caminhos de imagens. Usa referências ordinais `page-01/section-01` e dá origem a uma **sugestão de pattern**, com motivo e eventuais alertas; se a estrutura for ambígua ou não encaixar, fica para decisão humana.

A seleção usa **apenas estrutura**: H1 + descrição + botão na primeira secção sugere Hero; cabeçalhos secundários repetidos + parágrafos sugerem Serviços; imagem + H2/H3 + texto sugerem Sobre; uma secção tardia curta com H2/H3 + botão sugere CTA. Os padrões são hipóteses de composição, **não** reprodução visual da estrutura. Exemplo: o Hero atual da biblioteca **não tem slot de imagem**. Nesse caso o plano emite `hero_pattern_has_no_image_slot`.

O CLI `scripts/compose_lite_site_document_preview_v01.py` requer o `websign_vnext.validation.validate_site_document` real. **Se esse módulo não estiver disponível, recusa operar** em vez de inventar um validador compatível. O CLI pode produzir apenas o plano (`--output` omitido) ou um ZIP de **authoring preview**: Lite Core + a união dos patterns sugeridos. Este ZIP **não insere** conteúdo nos templates nem cria páginas; apenas torna os patterns disponíveis para trabalho editorial posterior.

## Prova realizada no Windows NPC

Acesso ao módulo `websign_vnext` **existente apenas no workspace Windows** `C:\projetos\websign-designeo`; esse módulo não se encontra versionado nas branches GitHub desta PR, por isso a dependência operacional permanece local.

1. Testes sobre a cópia isolada `C:\projetos\Websign-Lite-Audit-20261010\site_document_preview` (não sobre a pasta original): **32/32 PASS**, exit code 0. Incluem 10 novos testes de seleção/privacidade/ambiguidade/erros, 2 testes de integração nativa **executados e não saltados** e 20 anteriores de Core/Library/tokens/preflight.
2. SiteDocument **sintético com duas páginas** passou no validador nativo. Selecionou `hero`, `cta`, `services`, `about`, sem transferir textos/URLs/imagens de origem. Produziu um ZIP de preview de 20 ficheiros reutilizando a mesma biblioteca e Core.
3. Documento de referência real do projeto `fixtures/vnext/case007/expected_site_document.json` passou no validador nativo. Selecionou `hero` e detetou o conflito `hero_pattern_has_no_image_slot`.
4. CLI offline testado explicitamente com `case007`, devolveu código 0 e criou `designeo-lite-case007-site-document-preview.zip` com **17 ficheiros** (16 Core + Hero), SHA-256 `3b290090ab2e0fe5bd209eb3d184aebb9902415d341759382ded4127b92a56af`.
5. Nada foi modificado na pasta original do Websign, nos ZIPs v1.1/v2.0/v2.0.1, no WordPress, no DesignOS, no WRL nem no alojamento.

## Exemplo do resultado — sem conteúdo do cliente

```json
{
  "plan_schema": "designeo.lite.selection.v0.1",
  "site_document_schema": "websign.site.v0.1",
  "page_count": 1,
  "pattern_selection": ["hero"],
  "pages": [
    {
      "page_ref": "page-01",
      "sections": [{
        "section_ref": "page-01/section-01",
        "suggested_pattern": "hero",
        "rule": "first_section_with_h1_paragraph_and_button",
        "review_warnings": [
          "source_content_not_transferred",
          "hero_pattern_has_no_image_slot"
        ],
        "status": "proposal_not_inserted"
      }]
    }
  ],
  "requires_human_review": true,
  "patterns_inserted_into_wordpress_pages": false,
  "publish_ready": false
}
```

## O que falta para passar de sugestão a website

**Trabalho não implementado:**
- Decidir como mapear `SiteDocument` para **componentes com slots reais**: headline, descrição, CTA/URL, imagem e alinhamentos, mantendo edição Gutenberg. Os patterns atuais são templates PHP estáticos com placeholders e não recebem automaticamente conteúdo do SiteDocument.
- Criar um **catálogo de componentes com contrato de capacidades** (ex.: Hero sem imagem vs Hero com imagem, Services grid, Sobre texto+imagem) e validação de compatibilidade. Não escolher um pattern apenas pela aparência de uma secção.
- Aplicar a composição ao conteúdo real da página através de um renderer, com testes de round-trip e confronto visual no editor Gutenberg, sem clonar layouts de referências.
- Resolver links e imagens placeholders, fontes/licenças, CSS global e formulário de contacto real; QA de responsividade/teclado.
- Verificar isolamento e backups e testar WordPress staging com acesso normal e autorizado; consulta WP-CLI anterior foi bloqueada por segurança e **não será contornada**.
- Integrar o Websign VNext no repositório GitHub de forma aprovada **sem publicar dados locais de clientes ou artefactos sensíveis**. O adaptador depende do contrato local atual; não declarar deploy multi-máquina antes da integração oficial.

O passo natural seguinte é o **contrato de slots dos patterns (Lite Component Schema)**. Só depois vale a pena desenvolver os modelos Lite por áreas de atividade. A escolha automática de um nome de pattern sem conteúdo/slots **não equivale** a um website gerado.

## Limites de aprovação

Este é um protótipo de **seleção e montagem offline**, não uma release. O campo `publish_ready` permanece falso, a revisão humana é obrigatória e os patterns incluídos conservam conteúdo de exemplo. Todas as PRs envolvidas são rascunhos empilhados, sem merge ou deploy.
