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

## 5. Validação executada e preservação local — atualização de 10/10/2026

Depois da auditoria inicial, **o backup e os testes foram realizados** no dispositivo Windows `NPC`:

- Snapshot privado `C:\projetos\WRL-Safe-Backups\WRL_2026-10-10_snapshot_01`, com `921` ficheiros e `98 601 044` bytes. Preserva `.git`, código tracked/untracked, testes, frontend, HTML e screenshots; exclui `.venv` regenerável, caches e `*.pyc`.
- `data/website-research.db` foi preservada por **SQLite backup API** (origem aberta em leitura). O arquivo destino passou `PRAGMA quick_check = ok`, com **5 registos websites, 1 pesquisa temática, 5 vínculos pesquisa→website**.
- Manifesto privado `manifest.json` contém hashes SHA-256 dos ficheiros e metadados para comparação. Não publicar nem sincronizar este snapshot bruto com GitHub.
- A cópia de validação `C:\projetos\WRL-Safe-Backups\WRL_validation_2026-10-10_01` foi derivada do snapshot, **sem a base real**; suite original `152 passed` (exit 0, 2,29 s).
- Nessa mesma cópia, protótipo `evidence_export.py` e 20 testes novos → **172 passed** (exit 0, 2,15 s).
- Código exportador puro em PR Draft [Websign #1](https://github.com/Digitransarte/websign-designeo/pull/1), com esquema [EvidencePackage v0.1](../../blob/feature/wrl-evidence-package-v01-20261010/docs/WRL_EVIDENCE_EXPORT_CONTRACT_V01.md). Os **8 testes unitários independentes da PR passaram** num segundo workspace isolado (exit 0).
- Nenhuma captura de sites, execução de LLM, mudança do WRL original, deploy, commit de código confidencial ou migração de dados.

**Limites em aberto:** a cópia está no mesmo computador Windows (não substitui backup externo encriptado); a PR ainda não integra WRL/DesignOS em tempo de execução. Próximo gate: revisão do contrato, aprovação para integração e teste de intercâmbio JSON sintético antes de qualquer uso com pesquisas reais.
