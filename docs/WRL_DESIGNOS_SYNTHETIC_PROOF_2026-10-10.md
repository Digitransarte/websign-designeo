# WEB-01 · Prova sintética WRL → DesignOS (10/10/2026)

**Estado:** contrato funcional validado em isolamento; ingestão no DesignOS persistente **não executada**.

## Resultado técnico

- O exportador `integrations/wrl/evidence_export.py` transforma `research_summary` em `wrl_evidence.v0.1`, sem ler SQLite nem capturas.
- O consumidor `integrations/wrl/designos_adapter.py` valida referências, grupos de factos, cobertura e contagens e converte o pacote numa estrutura de **Discovery** para o DesignOS.
- A saída de teste está versionada como [`WRL_DESIGNOS_SYNTHETIC_BRIEF_V01.json`](fixtures/WRL_DESIGNOS_SYNTHETIC_BRIEF_V01.json). Foi gerada **pelo código da PR**, não escrita manualmente.
- A cópia isolada no Windows `NPC` passou **20 testes unittest** (8 do exportador, 12 do consumidor), código de saída 0. A suite original do WRL tinha passado **152 testes** em cópia separada; o protótipo de exportação dentro dessa cópia tinha totalizado **172**. São execuções distintas, não somar contagens.
- A análise da fonte `Digitransarte/design-os/designos/schemas.py` confirma que `BriefingCreate` aceita `source: str`, `version >= 1` e `content: dict[str, Any]`, compatíveis **em formato** com esta proposta; `designos/routers/projects.py` fornece a rota para adicionar briefings. Isto **não é prova** de ingestão real.

## O que o DesignOS receberia

Um briefing rotulado:
- `briefing_kind = research_evidence_discovery`;
- `status = draft_research_only`;
- `synthetic_input = true`;
- `sector_hypothesis = Serviços de bem-estar (hipótese de estudo)`;
- duas fontes fictícias (`WRL-WEB-000007` e `WRL-WEB-000008`);
- observações factuais de páginas, conversão e qualidade;
- **quatro perguntas criativas originais** com referências rastreáveis;
- `design_hypotheses = []`, `approved_design_decisions = []`;
- `handoff.generation_allowed = false` e `commercial_actions_authorized = false`.

O exemplo mistura uma página de serviços detetada em 1/2 sites, ações de conversão parcialmente observadas, uma inconsistência H1 num dos casos e WordPress como tecnologia presente em ambos. **Tudo é fictício; não são métricas de mercado ou sites reais.**

A intenção é orientar um futuro Design Agent a **perguntar** como definir navegação, arquitetura de serviços, CTA e QA, nunca a copiar conteúdo/layout ou escolher decisões sem briefing do cliente.

## Gate de integração

A tentativa de criar e preencher um projeto sandbox no DesignOS através do conector foi **bloqueada por verificações de segurança da ferramenta**. Não foi contornada por outra via. A listagem read-only posterior confirmou que não foi criado nenhum novo projeto DesignOS; apenas o projeto anterior `helena-martins` permanece listado.

Por isso, **não declarar** que WRL e DesignOS já estão integrados, que um agente executou o briefing, que o Core armazena os dois websites ou que existem novos modelos web.

## Próximos passos permitidos

1. Rever esta PR Draft com foco em privacidade, validação de contadores, proveniência e tipagem.
2. Resolver o acesso autorizado a sandbox DesignOS por via normal (sem contornar bloqueios de segurança); depois realizar uma ingestão limitada **só com JSON fictício**, explicitamente marcada como teste.
3. Preservar o backup local do WRL e preparar cópia externa encriptada antes de modificar o original.
4. Só depois desenhar um adapter oficial WRL `/researches/{id}/export` e fluxo DesignOS de referências, sem exportar base SQLite, HTML ou screenshots.
5. Integrar os achados em **Designeo Base** e modelos por setor como inspirações e restrições originais — não como templates copiados.

**Produção preservada:** nenhum site WordPress, instância de DesignOS, pesquisa WRL real ou código Windows original foi alterado.
