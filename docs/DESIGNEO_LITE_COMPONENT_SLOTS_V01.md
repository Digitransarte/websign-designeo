# WEB-02 · Lite Component Schema v0.1 — slots de conteúdo e pré-visualização Gutenberg

**Data:** 2026-10-10  
**Estado:** contratos e extração de conteúdo testados em sandbox Windows; **não** substitui patterns PHP, **não** publica WordPress e **não** está aprovado visualmente.  
**Owner:** Websign / Designeo Lite, dependente do `websign_vnext` local ainda não versionado em GitHub.

## 1. Definição do contrato

Código canónico: [`scripts/lite_component_slots_v01.py`](../scripts/lite_component_slots_v01.py). Formato de retorno `designeo.lite.component-slots.v0.1`. O módulo requer o validador **nativo do Websign VNext**, não implementa uma segunda versão do seu modelo de páginas.

| Componente Lite | Slots de conteúdo aceites | Restrições de composição |
|---|---|---|
| **Hero** | `headline`, `description`, `actions[{label,url}]` | H1 + 1 parágrafo + 1–2 botões. **Sem imagem** com o padrão Hero atual |
| **Serviços** | `items[{title,description}]` | 2–3 colunas; cada uma com H2/H3 e 1 parágrafo |
| **Sobre** | `headline`, `description`, `image{src,alt}`, `actions[]`, `image_position` | 2 colunas, uma com texto + CTA opcional, a outra com imagem; ordem da imagem preservada |
| **CTA** | `headline`, `description?`, `action{label,url}` | H2/H3 + 0–1 parágrafo + exatamente 1 botão, sem media |

Isto define **o que um componente deve saber receber**. Não implica que o ficheiro PHP legado contenha atualmente variáveis/sl​​ots ou que qualquer composição WordPress já consiga reproduzir essa geometria. O código contém `legacy_php_pattern_has_dynamic_slots: false` para todas as quatro tipologias.

A deteção estrutural e seleção de patterns existe na [PR #5](https://github.com/Digitransarte/websign-designeo/pull/5). A nova camada percorre a mesma secção do SiteDocument e extrai **dados reais** dos nós, preservando texto, labels, URLs, `src` e `alt` na estrutura **privada** retornada por `bind_lite_component_slots()`.

## 2. Regras sem perda de informação

- A secção só é vinculada se **todos os nós de conteúdo** se encaixarem nas capacidades declaradas: não truncar 3 botões para 2, não omitir uma imagem ou texto extra, não fabricar CTA/contacto.
- Bloquear `javascript:`, `data:`, `http:`, URLs sem destino, `//` e URLs com credenciais ou controlos. São admitidos caminhos locais (`/contacto/`, `/assets/foo.jpg`) e `https://` com hostname.
- Rejeitar IDs de nós repetidos, formas ambíguas e layouts com folhas não consumidas. Erros não devem incluir texto ou URL do cliente.
- Um Hero com imagem **bloqueia** com motivo `hero_requires_media_capability`, em vez de descartar a imagem. O caso `case007` já testado demonstra este comportamento.
- Se algumas secções forem incompatíveis, o plano lista `blocked_sections` e **não declara** `all_sections_bound: true`. A saída inclui `publish_ready: false`.

**Privacidade:** diferente da proposta anterior de seleção, a resposta de slots **CONTÉM TEXTO, IMAGENS E LINKS REAIS** do SiteDocument. Deve existir apenas em armazenamento/workspace privado autorizado, nunca em logs públicos, fixtures GitHub, PRs ou serviços externos sem consentimento e política apropriada. Os testes utilizam apenas valores fictícios.

## 3. Renderização: reutilizar Websign VNext

O módulo `scripts/render_lite_gutenberg_preview_v01.py` introduz um *gate* simples:

1. Executa o binding de todos os componentes contra o validador nativo.
2. Se **qualquer** secção estiver bloqueada, **não renderiza nenhuma página**, devolve apenas referências/razões sem conteúdo privado.
3. Se todas forem compatíveis, usa **o mesmo SiteDocument validado** e chama `websign_vnext.renderers.gutenberg.render_site_document`, o renderizador nativo já existente, para gerar blocos Gutenberg editáveis. Não constrói uma segunda implementação da serialização de blocos.

**Limite essencial:** o renderer nativo emite Gutenberg com classes `websign-...` e depende do **Websign design runtime/CSS**. Isto **não** significa que o Lite Core já carregue esse runtime, nem que preserve a linguagem visual dos quatro patterns PHP. Os patterns PHP antigos **não foram interpolados** ou substituídos nesta etapa.

O resultado é uma prova **offline de integridade do conteúdo no markup Gutenberg**, não uma prova de edição/representação visual dentro do WP Site Editor.

## 4. Testes executados — Windows NPC

Pasta isolada `C:\projetos\Websign-Lite-Audit-20261010\component_slots_preview`, usando os módulos reais `websign_vnext.validation` e `websign_vnext.renderers.gutenberg` do workspace Windows original, **sem modificar o original**.

**45/45 testes unitários PASS** (exit 0), com 13 novos nesta etapa:
- 10 testes de slots/segurança/conteúdo (Hero, Serviços, Sobre, CTA; valores conservados; URLs maliciosas ou vazias; secções em excesso; imagem incompatível; IDs repetidos);
- 3 testes do renderizador Gutenberg nativo: markup com títulos/URLs/imagem fictícios, bloqueio total do preview se Hero requer media não suportada, ausência de renderer;
- 32 testes herdados de seleção e Core/Library anteriores, incluindo testes com validador nativo real.

Foi emitido markup com blocos Gutenberg no ambiente de teste, preservando strings sintéticas de título, copy, link e imagem. **O markup privado não foi enviado ao GitHub** nem publicado.

## 5. Gate para o próximo desenvolvimento

**Lite Dynamic Components (não implementado nesta PR):**
- Fixar o contrato semântico e visual por componente, com slots reais dentro de layouts **originais** de Gutenberg, sem texto placeholder, CSS duplicado nem cloning de referências.
- Converter os slots validados para padrões/blocos nativos com conteúdo e classnames coerentes com o **Designeo Base / Lite Core**, ou adotar/adaptar o runtime Websign de forma explícita; **não** assumir que patterns PHP legados são compatíveis sem alterar o código.
- O Hero com imagem exige componente próprio ou variante de capacidade (em vez de omissão silenciosa).
- Testar que o output preserva texto/URLs/media, tem um HTML válido e continua editável depois de guardar/reabrir no WordPress; verificar responsive, teclado, contraste e estilos, sem font/license drift.
- Resolver acesso normal/seguro ao wp-lab com snapshot/rollback verificados. A inspeção WordPress remota anterior foi bloqueada por segurança e não será contornada.
- Antes de modelos por setor, comprovar **um Lite mínimo funcional** no WordPress e medir esforço de personalização.

Todas as PRs deste percurso (#2 a #6) são técnicas e em rascunho. Nenhum theme de cliente, ficheiro original Websign/WRL, WordPress, servidor ou ambiente de produção foi alterado.
