# WEB-01 · Website Research Lab — auditoria local Windows (10/10/2026)

**Origem auditada:** dispositivo Windows `NPC`, `C:\projetos\WebsiteResearchLab-MVP-0.1\WebsiteResearchLab`  
**Método:** leitura do código, ficheiros e `git status` via Desktop Commander. Sem alterações, testes, captura de websites ou migração de dados.  
**Estado:** funcionalidades **presentes em código**, não certificadas por testes executados nesta auditoria.

## 1. A descoberta principal

O cabeçalho do `README.md` identifica a versão **Website Research Lab MVP 0.5.0**, não apenas 0.3.2.1. A versão 0.5.0 agrega pesquisas temáticas e comparação factual **entre websites já capturados**, sem LLM e sem realizar novamente crawling.

Há uma ressalva crítica: o Git local está na branch `master`, último commit visível `4bb0047868542b961e13998527a07e69df3fba71` (2026-07-25, `feat: automatic website capture and review flow v0.2`). `git status` mostra muitas alterações e ficheiros `app/services/*`/tests/templates ainda não adicionados ao Git, além de `data/website-research.db` modificada. Portanto, **0.5.0 é o estado do workspace atual, não uma release Git confirmada nem um backup versionado**. Não limpar, resetar, sincronizar ou publicar sem preservação separada de código E dados.

## 2. Inventário confirmado pela leitura do código

| Área | Evidência inspeccionada | Estado da auditoria |
|---|---|---|
| Captura desktop/mobile | `README.md`, `app/services/capture.py`, rota `/websites/analyze` em `app/main.py` | Implementação presente; não executada agora |
| HTML/CSS/DOM e análise factual | `app/services/extraction.py`, `analysis_schema.py`, `technical_analysis.py`, `visual_analysis.py` | Implementação presente; esquema `analysis_data 0.2.2` |
| Deteção stack (WP/Elementor/etc.) | `technology_detection.py` e README | Implementação presente; heurística |
| SEO, acessibilidade, CTA e visual | `seo_analysis.py`, `accessibility_analysis.py`, `interaction_classification.py`, `visual_analysis.py` | Implementações presentes |
| Crawl multipágina interno | `crawler.py`, README | Limites default descritos: 25 páginas / profundidade 2 |
| Interpretação estratégica opcional | `strategic_analysis.py`, `ollama_provider.py`, rota de execução explícita | Código separado dos factos; contexto limitado, grounding por evidência e saída JSON; não testado runtime |
| Pesquisas temáticas multiwebsite v0.5.0 | `research_summary.py`, `researches.html`, `research_detail.html`, rotas `/researches` em `app/main.py`, `test_researches.py` | Presente em código: CRUD e comparação agregada |
| Base de dados | `app/database.py` e `data/website-research.db` | SQLite, tabelas `websites`, `researches`, `research_websites`; BD contém dados locais a preservar |
| Testes | `tests/test_*.py`, 17 ficheiros visíveis | Testes existentes, **não executados** nesta auditoria |
| Saída exportável para outras apps | Pesquisa visual por `app/main.py` e diretório `data/exports` | **Nenhuma API JSON/exportação estruturada confirmada**; diretório exports vazio na leitura |
| Segurança operacional | `url_security.py` e README | Proteções SSRF/crawl controlado descritas; auditar efetividade antes de exposição externa |

**Nota de design:** `research_summary.build_research_summary(websites)` retorna no código um `dict` com `corpus`, `technologies`, `architecture`, `offer`, `conversion`, `quality`, distinguindo `present`, `absent`, `partial_unknown`, `not_analyzed`. Não transforma lacunas de recolha em ausência comprovada. É um excelente contrato-fonte para construir modelos por atividade, com supervisão humana.

## 3. Decisão técnica de integração

**Manter o WRL no Windows como produto independente e dono dos dados de pesquisa. Não reconstruir um crawler em Websign.**

```text
Website(s) selecionados → WRL (evidência, cobertura, fontes, snapshots)
    → EvidencePackage JSON (exportação a desenhar, read-only)
    → DesignOS / Design Agent (interpretar, questionar, decidir)
    → Designeo Base (tokens + componentes próprios)
    → Websign (SiteDocument → Gutenberg e/ou Elementor)
    → QA / hosting / manutenção sob procedimento aprovado
```

**Contrato mínimo de exportação (proposta, ainda não implementada):**
`export_version`, `research_id` (ou `website_id`), `exported_at`, `source_refs` com URL/data, `schema_version` factual de origem, `coverage`, `facts`, `aggregate`, `evidence_refs`, `limitations`, `redaction_policy`.
Mapear inicialmente os grupos já existentes `corpus`, `technologies`, `architecture`, `offer`, `conversion`, `quality`. A exportação deve preservar contagens de cobertura e incerteza.

**Não exportar:** HTML integral, screenshots, scripts, cookies, tokens, capturas privadas, formulários, dados pessoais, base SQLite ou identidade de websites não autorizados. O consumidor pode consultar referências locais do WRL mediante acesso autorizado em vez de copiar ativos de terceiros. Exportar somente observações abstratas necessárias ao estudo; aplicar política de retenção/privacidade.

## 4. Próximos gates para WEB-01

1. **Preservação primeiro:** cópia local separada do projeto e da base de dados (com aplicação fechada ou snapshot consistente), incluindo ficheiros ainda não commitados, `data/html` e `data/screenshots`, protegendo dados e credenciais. Não copiar automaticamente para repositório público. Confirmar que a cópia é legível antes de qualquer operação Git invasiva.
2. **Teste seguro depois:** executar testes num workspace de teste ou snapshot isolado, com DB temporária; evitar tocar em `data/website-research.db`. Validar especialmente `test_researches.py`, extração, crawl/SSRF e geração dos agregados. Confirmar versão de dependências e corrigir eventual divergência entre `requirements.txt` e o ambiente real **sem mudar o original até testar**.
3. **Exportação pequena:** construir num ramo isolado um serializer puro `dict -> EvidencePackage v0.1` que não reexecuta crawl, não chama Ollama e não muta SQLite. Fixtures sintéticas e testes de privacidade.
4. **Consumo mínimo:** passar um único pacote de prova para DesignOS como input de leitura e avaliar se consegue sustentar o mapa de componentes sem copiar um site externo.
5. **Só então WEB-02:** usar a informação no Designeo Base (tokens/patterns), continuando Websign como responsável por Gutenberg/Elementor.

**Bloqueios:** não criar um novo UI de research, scraper, agente de pesquisa ou serviço Docker antes destes gates. Nenhuma operação no site de cliente, em produção WordPress ou no hosting está autorizada por esta auditoria.
