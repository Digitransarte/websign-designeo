# Designeo Web Foundation · Plano de consolidação v0.1

**Estado:** estratégia/roadmap, **não** implementação nova ou autorização de deploy.  
**Dono:** Designeo · desenvolvimento web.  
**Objetivo:** primeiro construir a capacidade interna de **conceber, repetir, alojar e manter websites WordPress**; só depois transformar componentes comprovados em kits comerciais para Venture OS.

## Princípio de arquitetura

**Um sistema, várias saídas** — evitar um construtor isolado para cada setor e evitar recriar o que já funciona.

```text
Designeo OS Core              (projetos, tarefas, decisões, histórico)
  └── DesignOS / Design Agent  (briefing, estratégia, identidade, design system)
         └── Websign / Designeo Site Studio / Web System
               ├── Designeo Base          (tokens, patterns, headers/footers, QA)
               ├── Site Models            (variações por setor)
               ├── SiteDocument canónico  (conteúdo, layouts, tokens, versões)
               └── Publicação             (Gutenberg prioritário; Elementor suportado)
                         └── Hetzner / CloudPanel / WordPress
                               (site provisioning, isolamento, SSL, staging,
                                backups/restore, updates, monitoring, maintenance)

Venture OS → consulta os componentes prontos e mede reutilização, custo e procura.
Venture OS NÃO é o owner dos templates nem da infraestrutura de hosting.
```

## Research — reutilizar Website Research Lab (WRL)

**Aplicação existente, agora localizada e inspecionada no Windows (NPC) em 2026-10-10.** Local conhecido: `C:\\projetos\\WebsiteResearchLab-MVP-0.1\\WebsiteResearchLab` (Windows local; não foi encontrado repositório WRL entre os GitHub acessíveis). A documentação no workspace atual identifica a **v0.5.0** (inclui pesquisas temáticas e comparação factual multiwebsite); 110 testes tinham sido reportados historicamente, **não reexecutados nesta auditoria**. FastAPI/SQLite/Jinja/Playwright, capturas desktop/mobile, extração de HTML/DOM/CSS e metadados, análise de estrutura visual/layouts/componentes/SEO/acessibilidade e crawler multipágina controlado (limites típicos 25 páginas/profundidade 2). Não assumir que estes testes passaram recentemente, nem que a integração Websign existe.

**Auditoria de código confirmada:** [WRL Windows v0.5.0 — inventário e riscos](WRL_LOCAL_WINDOWS_AUDIT_2026-10-10.md). O Git local está em `master` com último commit de julho em v0.2, mas a maior parte do código posterior e a própria base SQLite estão **por commitar**; preservar o estado do disco primeiro. `research_summary.py` já calcula agregados `corpus`, `technologies`, `architecture`, `offer`, `conversion`, `quality` e distingue cobertura factual. Não foi comprovada exportação estruturada para outras aplicações. A implementação inicial será um adapter read-only, depois de backup e testes isolados.

**Papel canónico:** observador/instrumento de investigação **local, determinístico**. Manter o WRL como aplicação autónoma. Não duplicar Playwright, crawler, base de dados ou UI de pesquisa dentro de Websign/DesignOS. O WRL não deve gerar clones de websites; a sua saída deve ser **evidência e padrões abstratos**, sujeitos a revisão humana.

Fluxo pretendido:

```text
Sites e referências selecionados
   → Website Research Lab (captura e análise, URL/fonte/data)
   → Evidence / Findings JSON exportável (sem media protegidos)
   → Padrões: navegação, layout, secções, CTA, tipografia/cores observadas,
      componentes, responsividade e acessibilidade
   → DesignOS / Design Agent: interpretação + decisões criativas originais
   → Designeo Base: componentes e tokens próprios
   → Websign/SiteDocument: modelo web e renderer Elementor/Gutenberg
   → QA técnico e visual → WordPress sandbox / hosting quando aprovado
```

**Fronteira de integração inicial:** WRL → exportação JSON versionada para pesquisa/design. O DesignOS interpreta; o Websign produz. Não mexer no motor interno do WRL nem criar integração bidirecional/automatizada antes de conhecer o formato atual das exportações. Definir campos mínimos: `source_url`, `captured_at`, `page_type`, `observations`, `evidence_refs`, `confidence`, `sections`, `patterns`, `assets_rights_status`, `analysis_version`; validar com dados reais e contrato canónico antes de fixar schema.

**WEB-01 acrescenta:** recuperar workspace Windows local, versão/commit, comandos de arranque e testes; inspecionar output de site single-page e de crawl multipágina, verificar como grava evidência e se suporta exportação; mapear o que é observação factual vs interpretação; avaliar limites legais, privacidade, robots/rate limits e direitos de screenshots/assets; só depois especificar um adapter mínimo consumido pelo DesignOS. Não enviar corpus/HTML privado ao GitHub.

## O que já existe e deve ser auditado antes de escrever novo código

**Fontes verificadas:** `Digitransarte/websign-designeo` tem `gutenberg.py` com builders de blocos e secções, `app.py`, dados multi-cliente, testes HTML de baseline e `Templates/designeo-lite-v1.1.zip`, `v2.0.zip`, `v2.0.1.zip`. `Digitransarte/design-os` é o owner do fluxo de design e brand workflow. `Digitransarte/designeo-studio` tem templates de **entregáveis de serviços**, distintos de templates de websites. Não os confundir.

**Inventário a confirmar:** Websign/Site Studio, Designeo Lite, Designeo Elite, `bhconv` HTML→WordPress, Design System/Brand Kit (tokens, tipografia, componentes), contratos dos agentes, código de integração WordPress via Application Passwords, case studies/site Designeo (atualmente Elementor) e Casa Bhumi como caso futuro Gutenberg. Não afirmar que as conversões e pipelines já estão prontas para clientes sem testar.

**Hosting existente, observado sem alterações:** CloudPanel presente no servidor Hetzner; Nginx, MariaDB, PHP 8.2/8.3 em execução; WP-CLI 2.12.0 no PATH. **Isto não é prova** de hosting gerido para múltiplos clientes pronto. Auditoria operacional necessária antes de novos sites reais.

## Sequência de trabalho (prioridades)

### WEB-01 — Arqueologia e mapa de capacidades existentes
- Identificar repositórios, módulos, versões, contratos, dependências e o que é reutilizável.
- **WRL:** localizar o workspace Windows, auditar v0.3.2.1/crawler/extrator e amostras JSON; manter aplicação independente, com handoff estruturado apenas à camada de Research/DesignOS.
- Inventariar 1 WordPress sandbox, versões dos motores Elementor/Gutenberg e estado de publicação.
- Verificar “o que já corre”, “o que apenas compila”, “o que ainda falta”, em matriz com provas.
- **Done:** inventário concreto, sem soluções redundantes nem novos serviços.

### WEB-02 — Designeo Base (fundação única de templates)
- Consolidar tokens visuais, `theme.json`, tipografia, grid, espaçamentos, componentes repetíveis, templates e patterns Gutenberg.
- Definir `SiteDocument`/esquema canónico versionado: contents, sections, slots, visual tokens, responsive, assets, source provenance.
- Desenhar os adaptadores: Gutenberg para nova produção; Elementor para suporte/serviço e migrações, sem forçar reconstrução de sites Elementor que funcionam.
- Incorporar QA visual, responsivo, acessibilidade, update/diff e rollback.
- **Done:** um template-base neutro editável/importável num WP sandbox, publicado apenas como **rascunho interno**, com teste de round-trip e comparação/QA. Não precisa ser produto vendável.

### WEB-03 — Modelos por área
- Um modelo canónico + variações de páginas, módulos e linguagem por setor, **sem copiar projetos de clientes**.
- Primeiras hipóteses: **serviços profissionais** (neutro), **bem-estar/yoga** (referência funcional futura Casa Bhumi), **indústria/oficinas** (candidata serralharia).
- Separar componentes comuns do setor, conteúdos de exemplo e alterações de identidade visual.
- **Done:** pelo menos duas variações testadas no mesmo motor, com medição de reutilização e esforço humano.

### WEB-04 — WordPress Hosting & Maintenance no Hetzner
- Auditar CloudPanel e instalações existentes: versões WP/PHP/plugins/temas; contas, recursos, domínios, certificados TLS, isolamento por site, acesso WP-CLI.
- Desenvolver um procedimento standard para provisionamento de site, staging → revisão → produção, segurança e acessos, operações WP-CLI, updates de core/plugins/themes, monitorização de uptime/erros, backups **ficheiros + base de dados**, cópia fora do servidor, **restauro comprovado**, disaster recovery e rollback.
- Dar tratamento separado a sites em **Elementor** (licenças, versões, regressões visuais/compatibilidade) e **Gutenberg** (themes, patterns, styles, compatibilidade de blocos), com manutenção contratual e SLAs explicitados.
- Não abrir alojamento a clientes nem migrar sites de produção antes do teste isolado.
- **Done:** um WP sandbox gerido por procedimento escrito, com backup e restauro em ambiente de testes, atualização e rollback ensaiados, sem expor dados de clientes.

### WEB-05 — Casos reais e melhoria iterativa
- Teste do novo website **Designeo**, preservando a produção Elementor enquanto o projeto futuro Gutenberg evolui em paralelo.
- Depois, caso **Casa Bhumi** como aplicação real de modelos e conversão; apenas com aprovação e revisão de conteúdo/identidade.
- Medir esforço por página, retrabalho, custo de alojamento, suporte e atualizações, incidências e qualidade.
- **Done:** evidência de redução de esforço e operação contínua, sem funcionalidades prometidas antes de QA.

### VF-WP-01 — Venture OS: produto derivado, NÃO bloqueador da fundação
- Estudo G0 documentado. **Gate G1 (construção de Hero isolado) adiado** até WEB-01/WEB-02 demonstrar o que já existe e qual o melhor caso de teste.
- O Hero poderá ser um **caso de teste de WEB-02**, não uma linha de desenvolvimento paralela.
- Revenda de kit/marketplace exige evidência de reutilização, custos reais, licença/distribuição e análise de compradores; nenhum contacto, publicação ou gasto autorizado por este roadmap.

## Gates transversais

- Não criar um novo website builder/agent se o Websign existente puder ser recuperado; auditar antes de decidir.
- DesignOS decide **o quê**; Websign materializa em WordPress **como**; CloudPanel/infra mantém **onde e com que garantias**; Project Agent coordena; Venture OS só avalia oportunidades.
- Manter a produção existente estável, sem deploy oportunista na mesma VM.
- Credenciais e dados reais de sites WP, CloudPanel e WordPress não devem entrar em GitHub, fixtures ou documentação pública.
- Todas as mudanças com risco de produção exigem plano de backup, restauro testado, QA/rollback e aprovação separada.

**Primeira execução proposta:** WEB-01, inventariando concretamente Websign Designeo Lite/Elite, Gutenberg e publicação antes de construir um Hero ou template novo.
