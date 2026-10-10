# WEB-01 · Auditoria comparativa Designeo Lite v1.1 / v2.0 / v2.0.1

**Data:** 2026-10-10  
**Estado:** inspeção estática concluída; **nenhuma versão certificada como block theme WordPress pronto para instalar/publicar**.  
**Definição aprovada:** Designeo Lite = **versão mínima de um template de website**, não uma família Elite. Designeo Base = fundação técnica (tokens, design system, componentes). Setores = variantes do Lite.

## Fonte verificada

Acesso read-only a `C:\projetos\websign-designeo\Templates` no computador Windows `NPC`; ZIPs auditados em memória por Python `zipfile`, com `testzip()` íntegro e `theme.json` decodificado como JSON. Foi confirmado que cada ZIP local **é idêntico ao ficheiro do repositório GitHub `main`**, comparando `git hash-object` e o blob SHA do GitHub:

| Arquivo | Tamanho ZIP | SHA blob GitHub + Windows | Ficheiros |
|---|---:|---|---:|
| `designeo-lite-v1.1.zip` | 21 301 B | `5f12a13dca20e220166e3d9b4a53413179d051f3` | 19 |
| `designeo-lite-v2.0.zip` | 24 716 B | `da2ae245a0ece11bb760a4ff7dac24c07c62f031` | 20 |
| `designeo-lite-v2.0.1.zip` | 25 086 B | `e84232230c0423f4743ddee191d8e6e001f4a707` | 20 |

A pasta Windows tem alterações locais não commitadas fora dos ZIPs e outros projetos/artefactos Websign em `websign_vnext`, `bhconv`, `design_compiler`; não se executou `reset`, `checkout`, `pull`, atualização de theme ou ligação ao wp-lab.

## Componentes já existentes

Cada ZIP contém:
- `theme.json` versão de schema WordPress **3**, válido em JSON;
- `style.css`, `functions.php` e `index.php`;
- seis templates HTML: `front-page`, `page`, `page-no-title`, `single`, `search`, `404`;
- `parts/header.html` e `parts/footer.html`;
- cinco patterns PHP **com conteúdo igual nas três versões**: `hero`, `services`, `about`, `cta`, `contact`;
- CSS global/editor; versões v2.x acrescentam `assets/js/header.js`.

A v1.1 utiliza 8 cores, 2 famílias tipográficas, 9 tamanhos de fonte e 9 espaçamentos. A v2.0/2.0.1 tem **11 cores semânticas**, 3 famílias, 11 tamanhos e 11 espaçamentos. Estas contagens não significam que todas sejam necessárias ao template **mínimo**; separar o essencial do opcional em WEB-02.

## Resultado da comparação v2.0 → v2.0.1

O patch preserva **16 dos 20 ficheiros byte-a-byte** e altera somente:
1. `style.css`: versão 2.0.0 → 2.0.1;
2. `theme.json`: sete novas declarações `typography.fontStyle = normal` nos títulos H1–H6 e `core/post-title`; restantes valores escalares/arrays do JSON permanecem iguais;
3. `templates/page.html`: reduz padding vertical (10/12 → 8/10), ajusta margem inferior do título (8 → 5), `margin-top:0` e impede itálico no título da página;
4. `assets/css/global.css`: acrescenta regras para títulos sem itálico, links herdarem a cor em vez de azul default, espaçamento título/conteúdo e remoção de margens duplas em grupos.

**Alerta de flexibilidade:** o patch usa seletores globais com `!important` para forçar títulos não-itálicos; também força herança de cor para links. São correções de uma apresentação específica que podem dificultar variantes setoriais do Lite. Na fundação mínima é preferível parametrizar estes estados por tokens/variantes e medir contrastes e estados de foco.

## Bloqueio prioritário: template fallback obrigatório ausente

**As três versões contêm `index.php`, mas nenhuma contém `templates/index.html`**. O WordPress diferencia um block theme de um classic theme pela existência de um `index.html` dentro de `/templates` (ou `/block-templates` legado); esse é o template fallback obrigatório para edição completa do site.

**Documentação oficial:**
- https://developer.wordpress.org/themes/core-concepts/theme-structure/
- https://developer.wordpress.org/themes/templates/templates/
- https://developer.wordpress.org/block-editor/how-to-guides/themes/

Logo, um `theme.json` válido e alguns templates HTML **não bastam para declarar a versão pronta como tema FSE**. Pode haver suporte ao editor de blocos num tema clássico, mas o funcionamento como *block theme* precisa de correção e de prova real no WordPress.

**Critério técnico para desbloquear WEB-02:** num **ramo/cópia isolada**, adicionar `templates/index.html` com fallback adequado a páginas/arquivo e blocos core; passar análise estática/validação de templates; instalar num WordPress **sandbox**, confirmar que o WordPress reconhece o tema como *block theme* com editor do site, abrir templates/patterns, verificar frontend/mobile/acessibilidade, importação e edição; **nenhum deploy para clientes** sem aprovação e rollback.

Outros pontos de QA: `style.css` informa `Tested up to: 6.7`, não é evidência de compatibilidade com WordPress atual; verificar fonts/licenças, contraste/foco, comportamento mobile JS, seleção de templates, patterns, SVG/imagens, ausência de links/paths absolutos, compatibilidade com publicação Websign. O ZIP v2.x usa a pasta interna `designeo-lite-base` e o v1.1 `designeo-lite`; migrar um tema instalado entre slugs pode alterar as referências de template e estado. Não substituir temas de sites existentes automaticamente.

## Decisão recomendada

**Candidata técnica:** v2.0.1, por consolidar as alterações de v2.0 sem mudar os cinco patterns; **não declarada base aprovada**. Não regressar automaticamente à v1.1 só por ter menos tokens. Primeiro resolver o fallback obrigatório e comparar o resultado em sandbox.

**Versão mínima Designeo Lite vNext:** definir um núcleo pequeno e neutro — `style.css`, `theme.json`, `templates/index.html`, `templates/page.html`, header/footer, tokens mínimos e apenas os patterns fundamentais necessários ao website de apresentação. Patterns adicionais podem permanecer como biblioteca opcional; não exigir logo serviços/sobre/contacto no mesmo template. **Este é um escopo proposto, não uma decisão de conteúdo final tomada pelo utilizador.**

**Os modelos por setor não devem criar novos themes independentes:** variam secções, conteúdo editorial de exemplo, tokens e componentes sob a mesma base; preservar a independência entre DesignOS (interpretação), Websign (renderização/publicação) e infraestrutura WordPress (alojamento/manutenção).

## Próximo teste de baixo risco

1. Criar cópia isolada da v2.0.1 fora da pasta original; confirmar hash e integridade; introduzir `templates/index.html` mínimo e documentar porquê.
2. Validar os templates e os ficheiros com testes estáticos, sem mexer no Git local com alterações.
3. Instalar a cópia no **wp-lab**, só depois de confirmar credenciais/isolamento e aprovação, e fazer checklist de block theme + visual QA.
4. Transformar correções comprovadas na nova referência Designeo Lite, mantendo histórico dos ZIPs v1.1/2.0/2.0.1 como fontes.
5. WEB-03 então começa variantes por setor baseadas no Lite corrigido.

**Nenhuma alteração aos ZIPs originais, sites WordPress, servidor, credenciais ou produção foi feita nesta auditoria.**
