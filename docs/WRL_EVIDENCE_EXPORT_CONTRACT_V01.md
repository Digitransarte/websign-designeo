# WRL → DesignOS · EvidencePackage v0.1 (proposta testável)

**Owner do research:** Website Research Lab no computador Windows.  
**Consumidores futuros:** DesignOS/Design Agent → Designeo Base/Websign.  
**Implementação:** `integrations/wrl/evidence_export.py` (pure Python, standard library).  
**Estado:** PR de integração para revisão; **não está ligada à interface original WRL, não publica conteúdos, não modifica SQLite, não executa IA**.

## O que foi verificado antes deste contrato

- Workspace WRL v0.5.0 encontrado em `C:\projetos\WebsiteResearchLab-MVP-0.1\WebsiteResearchLab`.
- O Git local está substancialmente desatualizado face ao código do workspace; há modificações não commitadas e novos módulos de análise. A base real não deve ser publicada.
- Um backup privado do workspace completo, incluindo `.git`, HTML/screenshots e **snapshot consistente SQLite**, foi criado no Windows em `C:\projetos\WRL-Safe-Backups\WRL_2026-10-10_snapshot_01` (**921 ficheiros, 98 601 044 bytes; SQLite PRAGMA quick_check = ok**). Exclui `.venv` regenerável e caches.
- Uma cópia separada para validação, sem a BD real, passou **152/152 testes originais do WRL**. Com o protótipo de exportação introduzido apenas nessa cópia, **172/172 testes passaram**, incluindo 20 novos testes de contrato e privacidade. Nenhuma captura externa foi realizada nesta validação.

Isto demonstra integridade da suite e lógica de exportação em teste. **Não prova** que a integração DesignOS esteja implementada, nem que o WRL tenha sido empacotado/deployado como produto.

## Interface Python

```python
from integrations.wrl.evidence_export import export_research_summary

package = export_research_summary(
    summary,                     # output de research_summary.build_research_summary(websites)
    research_id=3,               # identificador local WRL, não ID público
    exported_at="2026-10-10T15:00:00+01:00",
    source_schema_version="0.2.2",
)
```

A função **não abre ficheiros, não comunica com o WRL, não lê screenshots ou HTML e não faz crawling**. Tem de receber os agregados já gerados pelo WRL. Uma eventual rota `GET /researches/{id}/export` é **futura** e não está implementada.

## Conteúdo do pacote (formato)

```json
{
  "export_version": "wrl_evidence.v0.1",
  "source": {
    "application": "Website Research Lab",
    "source_schema_version": "0.2.2",
    "research_ref": "WRL-RESEARCH-000003",
    "exported_at": "2026-10-10T15:00:00+01:00"
  },
  "corpus": {
    "website_count": 2,
    "references": [
      {"ref": "WRL-WEB-000007", "domain": "example.org", "capture_timestamp": null}
    ],
    "coverage": {
      "arquitetura_informacao": {
        "analyzed": 1,
        "partial": 1,
        "not_analyzed": 0,
        "total": 2
      }
    }
  },
  "observations": {
    "page_types": [],
    "conversion_features": [],
    "quality_indicators": [],
    "technologies": []
  },
  "interpretation": null,
  "limitations": [
    "Incomplete/partial WRL coverage is not observed absence"
  ],
  "action_authorized": false
}
```

*Exemplo ilustrativo: na exportação real as seis áreas de cobertura são obrigatórias e os exemplos de fontes têm de corresponder ao total do corpus.*

Os indicadores de `page_types`, `conversion_features` e `quality_indicators` usam `feature`, `present`, `absent`, `partial_unknown`, `not_analyzed` e `evidence_refs` com IDs locais pseudónimos. As tecnologias são filtradas para nomes reconhecidos, sem texto livre.

## Segurança e semântica

**Não exporta:** nomes atribuídos a websites, textos copiados de páginas, HTML, CSS bruto, scripts, imagens, contactos, emails, telefones, notas de pesquisa ou respostas LLM. Não inclui ratings ou pontuações geradas. As fontes usam apenas domínios validados, sem caminhos, query strings, tokens ou credenciais. URLs completas e timestamps de captura não estão disponíveis no agregado consultado e **não são inventados** (`capture_timestamp: null`).

**Evidência ≠ interpretação:** se uma área é `partial`, a ausência de uma feature permanece `partial_unknown` em vez de se transformar num falso `absent`. O DesignOS fará a interpretação criativa e deverá citar fontes/evidências, sem clonagem de layouts ou ativos de terceiros. Pacotes têm `action_authorized: false`.

**Falha fechada:** o exportador rejeita corpus inconsistente, contadores inválidos, status sem cobertura, tipos arbitrários e referências a websites inexistentes. Limite atual de 250 entradas na exportação (não altera os limites de crawling do WRL). Este contrato só deve consumir agregados provenientes de pesquisas públicas/autorizadas; não aplicar a conteúdos privados sem revisão de privacidade.

## Próximos gates

1. Rever a PR e testar o contrato isoladamente; não publicar o repositório WRL bruto.
2. Fazer revisão de privacidade de dois pacotes sintéticos antes de utilizar dados reais.
3. Com autorização, integrar uma rota read-only no WRL **depois de preservar e versionar o código local**, sem alterar a DB e sem ligar IA por defeito.
4. Validar a receção do JSON no DesignOS em ambiente de testes e transformar as observações em padrões **originais** Designeo.
5. Só depois integrar no sistema de templates por setor e no motor Gutenberg/Elementor.

**Nota:** a cópia de segurança referida é local ao computador Windows; deve existir cópia externa encriptada para tolerância a falhas do disco, antes de migrações ou limpeza do workspace.
