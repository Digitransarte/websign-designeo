# WEB-01 · Designeo Lite — pré-verificação de entrega e definição do mínimo

**Data:** 2026-10-10 · **Fonte:** candidato `designeo-lite-v2.0.1-token-aligned-preview.zip` gerado e lido em isolamento no Windows NPC.  
**Estado:** tokens resolvidos e fallback Gutenberg presente, mas **pré-verificação de entrega falhou** por conteúdo demonstrativo. Sem alteração do ZIP original, sem acesso a sites e sem execução WordPress.

## Resultado observado

Executou-se `scripts/preflight_lite_v201_candidate.py` sobre o candidato experimental já gerado (SHA256 `49f1188f124129f895b1b5adbf66194da3ffaa1091e6e28497fc9476f628ba3f`):

| Verificação | Resultado |
|---|---|
| ZIP e `theme.json` | Integridade/estrutura previamente verificadas |
| Fallback `templates/index.html` | Presente; **não validado em WordPress** |
| Patterns incluídos | 4 (`Hero`, `Serviços`, `Sobre`, `CTA`); `Contacto` demonstrativo excluído |
| Referências a tokens não existentes | **0** (auditoria anterior) |
| Botões sem URL | **4** — `Hero` 2, `Sobre` 1, `CTA` 1 |
| Imagem sem `src` | **1** — `Sobre` |
| Formulários placeholder incluídos | **0** — o `Contacto` original com `action="#"` foi excluído |
| Declarações `!important` em CSS | **47** — precisam de revisão/simplificação visual |
| Fontes nomeadas declaradas | `display`, `body`, `mono`; não são incluídas em ficheiros `woff/ttf` nem existe carregamento explícito comprovado |
| Licença no `style.css` | `Proprietary`; revisão de redistribuição/licenças necessária |
| Testes unitários da branch isolada | **12/12 PASS**, exit code 0 |
| Estado de entrega | **BLOQUEADO** |
| WordPress wp-lab / Editor do Site | **NÃO TESTADO** — anterior inspeção remota bloqueada por segurança |

Os botões sem destino e a imagem vazia são aceitáveis como **marcadores de conteúdo que o editor vai preencher**, mas **não podem permanecer como elementos ativos num website entregue a um cliente**. O preflight é propositalmente conservador: bloqueia a categoria “pronto a entregar”, **não** proíbe utilizar patterns em sandbox de design.

## Definição funcional mínima (proposta para WEB-02)

Separar três camadas, sem criar outro motor:
- **Lite Core** = tema base instalável e editável em Gutenberg: tokens, `theme.json`, templates obrigatórios e página, header/footer, acessibilidade e padrões de fallback. Não inclui branding de cliente, CTA com link inventado, mídia vazia ou contacto demonstrativo.
- **Lite Pattern Library** = padrões originais opcionais, inseríveis e ajustáveis: Hero, Serviços, Sobre, CTA e futuramente um módulo de Contacto **com integração de envio real**. Podem ter conteúdo exemplar em sandbox, mas o processo editorial deve exigir a substituição de URLs, textos e media antes de publicar.
- **Lite Models por área** = estrutura editorial, secções, cores/tipografia e módulos selecionados por setor, sempre por cima do mesmo Core. Não criar temas independentes para cada setor.

A separação é uma **proposta de implementação**, sujeita a ajuste pelo utilizador, e não pretende transformar o Lite numa versão Elite nem introduzir uma nova aplicação de construção.

## Contrato de release sem atalhos

```text
ZIP original v2.0.1 (imutável)
    ↓
Fallback index.html + normalização de tokens (candidato, PRs #2 e #3)
    ↓
Preflight automatizado (BLOQUEIA elementos incompletos)
    ↓
Definição mínima Lite Core + Library
    ↓
WordPress wp-lab com isolamento, backup e rollback verificados
    ↓
Reconhecimento de block theme / editor Gutenberg / QA de patterns
    ↓
Preenchimento de links, media e contacto real + fonts/licenças
    ↓
Aprovação humana e release só depois da evidência
```

**Importante:** o preflight nunca marca `release_ready=true` apenas por testes estáticos; exige confirmação externa de runtime WordPress, visual, conteúdo e operação. `--fail-on-placeholder` termina com código não-zero quando existem elementos demonstrativos.

## Próximas tarefas técnicas

1. Construir um **Core mínimo isolado** que permita personalizar os patterns sem transportar conteúdo placeholder para o website publicado. O Design Agent decide o sistema visual; o Websign aplica; nenhum tema existente é alterado sem aprovação.
2. Rever CSS com `!important` (47 ocorrências no candidato) para distinguir overrides legítimos de correções frágeis; não remover automaticamente.
3. Definir carregamento/uso real de fontes com licenças apropriadas e fallback consistente; evitar assumir que os nomes em `theme.json` fazem download automático.
4. Resolver o acesso **normal e autorizado** ao wp-lab sem contornar o bloqueio anterior. Só aí realizar teste de reconhecimento, Gutenberg editor, media, mobile, acessibilidade e rollback.
5. Testar duas personalizações visuais originais numa base **Lite estável** antes de lançar modelos setoriais; medir esforço real.

**Não realizado:** instalação WP, ativação, deploy, captura de URLs reais, geração de nova identidade, ligação a formulários, alteração do ZIP original.
