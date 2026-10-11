# WEB-02 · WordPress wp-lab — instalação inativa do Designeo Lite

**Data:** 11 de outubro de 2026  
**Ambiente:** `wp-lab.designeo.pt` (Hetzner / CloudPanel).  
**Estado:** cópia candidata **instalada apenas em ficheiros como tema INATIVO**; WordPress atual e as páginas Gutenberg existentes mantidos. Não é um lançamento, não houve ativação nem alterações intencionais à base de dados.

## 1. Proteção e backups

- Existe arquivo diário da base de dados para 11/10/2026; é um `.sql.gz` de ~30 KB. **`gzip -t` PASS**, estrutura SQL reconhecida (12 instruções `CREATE TABLE`). **Não** foi feita importação de teste, portanto **restauro da base de dados ainda não está comprovado**.
- Antes de instalar, foi produzido backup **integral dos ficheiros da instalação WordPress**, incluindo `wp-config.php`, temas/plugins e uploads, comprimido com acesso privado (permissões 0600). Foram arquivadas **4 282 entradas**, ~40,6 MB, gzip verificado.
- SHA-256 do backup de ficheiros: `e001a2c9498f4aee3308e929a4871fb821802bde24fada9aac01ebb3e4fe0834`.
- **Teste de extração para pasta temporária PASS**. Comparações byte a byte (`cmp`) de amostras representativas: `wp-config.php`, `index.php`, `websign-runtime.php`, `twentytwentyfive/style.css`. A pasta temporária foi apagada.
- **Importante:** backups guardados no mesmo servidor, não constituem backup externo/offsite. Não há teste de restauro completo do SQL em instância isolada; evitar qualquer ação que altere a BD antes de resolver essa limitação.
- Os arquivos contêm configuração e dados privados; **não foram enviados ao GitHub** e as credenciais de `wp-config.php` não foram lidas/publicadas.

## 2. Reprodução do candidato no Linux

A partir da branch da [PR #8](https://github.com/Digitransarte/websign-designeo/pull/8), foi feito checkout via GitHub no workspace temporário privado do servidor. Foram instalados `tinycss2==1.5.1` e `cssselect2==0.10.1` **num venv privado**, sem alteração ao Python global.

`scripts.audit_lite_css_cascade_v01` produziu um ZIP candidato com 16 ficheiros. O ZIP completo teve SHA-256 Linux `b034e62afa2928e882b8540d70a0d67321c68b1e71fe233dfd6fd773744c02d6`, distinto do SHA-256 do ZIP produzido no Windows (`900943689e7dcdd577b4c86df2cdcd78e1d588cba63f0c043123a5ece8f5b8c7`).

**Foi comparado o SHA-256 de cada uma das 16 entradas dos dois ZIPs: 16/16 bytes idênticos.** A diferença é de empacotamento, não do conteúdo dos ficheiros. Ambos passaram a verificação ZIP.

Antes da instalação foram verificados `theme.json` versão 3, `templates/index.html`, `php -l` para `functions.php` e `index.php` (PHP 8.4.24, sem erros), e ausência de colisão de pasta existente.

## 3. Instalação de ficheiros, sem ativar

Foi criado um diretório de tema **exclusivo** no wp-lab:

```text
wp-content/themes/designeo-lite-lab-v01
```

Os 16 ficheiros foram copiados de uma área temporária por uma operação com staging e rename atómico, sem substituir diretórios de temas existentes. Dono `wp-lab:wp-lab`, diretórios 0755 e ficheiros 0644.

**Não houve**:
- alteração do tema ativo ou das opções WordPress;
- alteração do plugin Websign Runtime;
- substituição de Twenty Twenty-Five/Four/Three;
- importação de base de dados ou criação de páginas;
- merge das PRs;
- alteração a outros sites CloudPanel.

### Smoke test HTTP pós-instalação

| Verificação | Resultado |
|---|---|
| Homepage `https://wp-lab.designeo.pt/` | HTTP **200** |
| `.../themes/designeo-lite-lab-v01/style.css` | HTTP **200** |
| `.../themes/designeo-lite-lab-v01/assets/css/editor.css` | HTTP **200** |
| Marcas de theme da página inicial | **Twenty Twenty-Five** (permanece ativo) |
| Links dos casos Gutenberg existentes | Permanecem referenciados no homepage |
| CSS Lite Dynamic Bridge e correção de cascata | Presentes e servidos por HTTP |
| `templates/index.html` | Presente no diretório do tema |
| WordPress reconhece tema pelo Site Editor | **Ainda não testado** |
| Tema Lite ativado | **Não** |

## 4. Novo bloqueio identificado: duplicação de estilos com plugin ativo

O frontend atual mostra a folha de estilos do **plugin Websign Runtime v0.1.0** carregada. O plugin tem CSS para as classes `websign-...`; o Lite candidato introduz CSS próprio para classes coincidentes.

Comparação estática: **22 classes `websign-*` partilhadas** entre o plugin e a Dynamic Style Bridge Lite. Coincidem em botões, titles, fundos, spacing, larguras e colunas. O plugin ainda contém regras responsivas e `!important` próprias.

**Sem testar no Gutenberg/site ativado, não há garantia de precedência CSS, tipografia ou proporções.** Não desativar o plugin no wp-lab: as páginas anteriores de investigação dependem dele.

### Solução recomendada para próximo gate

Implementar uma política de *style ownership* em **staging** que impeça carregar dois runtimes para as mesmas classes quando o Lite estiver ativo, mantendo o Websign Runtime para os temas existentes. Qualquer alteração ao plugin tem de ser testada e reversível, depois de resolver o teste de restauro da base de dados se implicar ativação/mudanças de opções.

Alternativamente, validar o Lite num WordPress completamente isolado, sem afetar as páginas Case existentes.

## 5. Gates que faltam

1. **Acesso autenticado e autorizado** para inspecionar o reconhecimento de tema no WP admin/Site Editor; ferramenta WP-CLI havia bloqueado uma consulta, e essa restrição não foi contornada.
2. Testar uma recuperação SQL num ambiente descartável, sem operar na BD do wp-lab.
3. Resolver a sobreposição dos **22 seletores CSS** entre plugin Runtime e Lite (frontend + editor).
4. Testar importação, edição/guardar, frontend, responsive, contraste, nav e restauração/rollback no WordPress.
5. Só então considerar ativar no wp-lab, publicar casos Lite e avançar para modelos setoriais.

**Conclusão:** a construção, a transferência via repositório e a instalação do tema INATIVO no servidor estão comprovadas. A ativação/edição Gutenberg em execução ainda depende de validação e controlo dos riscos acima.
