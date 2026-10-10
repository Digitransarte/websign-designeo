# WEB-02 · Designeo Lite Core + Pattern Library v0.1

**Data:** 2026-10-10  
**Estado:** arquitetura modular materializada em ZIPs de sandbox e testada estaticamente; **não instalada/validada em WordPress**.  
**Produto:** Designeo Lite = versão **mínima de um template de website**. Designeo Base = fundação técnica partilhada; modelos por atividade assentam no Lite. **Não** criar uma linha Elite.

## O que agora existe realmente

A partir do ZIP original imutável **Designeo Lite v2.0.1**, com fallback Gutenberg da PR #2 e normalização de tokens dos patterns da PR #3, o novo gerador `scripts/build_lite_core_library_v01.py` cria **duas peças independentes**:

| Saída | Conteúdo | Finalidade |
|---|---|---|
| **Lite Core** | Tema block WordPress candidato, 16 ficheiros. `theme.json`, estilos, PHP, `templates/index.html`, outros templates essenciais, header/footer, assets; **sem nenhum pattern editorial** | Base técnica única, apta a receber diferentes layouts/conteúdos **após QA WordPress** |
| **Lite Pattern Library** | ZIP **não instalável como tema WP**, 4 patterns (`hero`, `services`, `about`, `cta`) e `manifest.json` com compatibilidade, checksums SHA-256 e `publish_ready: false` | Biblioteca de componentes editoriais selecionáveis pelo Websign/DesignOS |

A biblioteca não inclui o pattern **Contacto** original: contém um formulário HTML demonstrativo `action="#"` sem tratamento de envios. A futura secção de contacto terá de integrar um formulário verdadeiro ou alternativa validada; não publicar o demo.

O Lite Core é uma **candidatura a tema mínimo** baseada em código existente, não uma redução final otimizada: ainda contém templates de single/search/404, CSS `!important`, fontes nomeadas que recorrem a fallback e licença que precisa de revisão. O seu escopo definitivo depende de verificação de manutenção/acessibilidade/design e de WordPress real.

## Testes executados

- Código versionado na branch desta PR e executado numa cópia Windows isolada em `C:\projetos\Websign-Lite-Audit-20261010\core_library_preview`, sem alterar o Websign original.
- **20/20 testes unitários PASS** (8 novos de separação/composição + 12 preexistentes de fallback, mapeamento e preflight).
- Testam ZIPs íntegros, separação 16+4, manifesto, seleção de patterns, rejeição de patterns desconhecidos/duplicados/modificados, recusa de sobrescrever ficheiros e **reprodutibilidade byte-a-byte** entre compilações independentes.
- O preflight do **Core** não encontrou botões/imagens placeholders, mas continua com `release_ready=false` e `wordpress_runtime_tested=false`. A biblioteca e os modelos recompostos **mantêm placeholders** e exigem trabalho editorial antes de publicação.

## Artefactos reais no Windows, não publicados

Localizados em `C:\projetos\Websign-Lite-Audit-20261010\candidate_v201`:

| Ficheiro ZIP | SHA-256 | Entrada |
|---|---|---|
| `designeo-lite-core-v0.1-preview.zip` | `f12e5fcf036c474843ebaa8f452777ee242111743f0c5f1b14ea9170dc18d350` | Core, 16 ficheiros |
| `designeo-lite-pattern-library-v0.1-preview.zip` | `2e908b44c87f6462f80862fb9d512f1d7ea057e698ed4a45cf5a6fca85fb6442` | Biblioteca, 4 patterns + manifesto |
| `designeo-lite-composed-intro-v0.1-preview.zip` | `007983d411c12f586af0e6fe646c76f6bb5b866936ee094f879d39e540cd5b59` | Core + Hero + CTA; 18 ficheiros |
| `designeo-lite-composed-services-v0.1-preview.zip` | `09257bff7fd261da1c84e163b31d53728e6e965bb865ad42c1d2aff34d1b986f` | Core + Hero + Serviços + Sobre + CTA; 20 ficheiros |

São **pré-visualizações de montagem**, não websites de clientes nem setores validados. Nenhum foi instalado no servidor ou alojado.

## Como reproduzir

Usar um checkout da branch com os ZIPs originais `Templates/designeo-lite-v1.1.zip` e `Templates/designeo-lite-v2.0.1.zip`, e um destino **fora do repositório**:

```bash
python -m scripts.build_lite_core_library_v01 \
  --core /tmp/designeo-lite-core.zip \
  --library /tmp/designeo-lite-patterns.zip

python -m scripts.compose_lite_preview_v01 \
  --core /tmp/designeo-lite-core.zip \
  --library /tmp/designeo-lite-patterns.zip \
  --pattern hero --pattern cta \
  --output /tmp/designeo-lite-demo.zip
```

O manifesto apenas transporta **nomes de patterns, hashes, compatibilidade e avisos**; não imagens, conteúdo de clientes ou direitos de terceiros. Os ZIPs são determinísticos. O gerador utiliza o mesmo pipeline de normalização provado anteriormente e **recusa temas modificados**, componentes não reconhecidos ou output já existente.

## Desenho de integração futuro

```text
WRL (observações e evidência)
          ↓
DesignOS (estratégia, critérios, decisões visuais)
          ↓
SiteDocument (conteúdo, tokens, seleção de secções)
          ↓
Designeo Lite Core + Pattern Library  ← biblioteca comum
          ↓
Websign gera uma composição Gutenberg
          ↓
Preflight editorial, imagens, links, licença, QA
          ↓
Staging WordPress / Editor do Site / revisão humana
          ↓
Alojamento/manutenção Designeo após aprovação
```

**Esta integração com SiteDocument ainda não foi implementada.** O CLI prova seleção e montagem de ficheiros, **não** parametrização do conteúdo dentro de cada pattern, nem entrega, criação de páginas, instalação WordPress, disponibilização dos themes ou aplicação do design system ao cliente. Sem prova de WordPress runtime, não chamar “tema operacional aprovado”.

## Próximos gates

1. Revisão técnica desta PR; o Core será o mesmo para diferentes modelos, mas o conjunto mínimo de arquivos precisa de decisão após QA.
2. Definir uma pequena interface `SiteDocument → Lite pattern selection` que apenas seleciona patterns já conhecidos, sem texto/imagens de clientes no GitHub e sem copiar designs externos.
3. No WordPress wp-lab **por via normal e autorizada** (inspeção anterior bloqueada), verificar isolamento, backups e rollback, instalar tema com diretório que não colida com o instalado, Editor do Site, inserção de patterns, navegação, scripts, media, mobile e acessibilidade.
4. Rever fontes/licenças e 47 `!important` existentes no CSS; integrar conteúdo editorial real e QA de publicação.
5. Só depois começar modelos **Designeo Lite** por setor e medição de reutilização, sem cada setor criar um tema diferente.

**Produção preservada:** nenhuma instalação WP, CloudPanel, alteração de sites, ativação de tema ou modificação dos ZIPs originais foi efetuada.
