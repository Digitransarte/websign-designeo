# Designeo Lite v2.0.1 — fallback FSE (candidato isolado)

**Estado:** candidato técnico em revisão; **não instalado no WordPress, não aprovado para produção**.  
**Prioridade:** WEB-01 → WEB-02 (Designeo Lite = template mínimo; Designeo Base = fundação técnica).  
**Escopo desta alteração:** corrigir apenas a ausência do template obrigatório de fallback em block themes WordPress. Não remodelar os modelos setoriais, CSS nem padrões nesta fase.

## Fonte e prova

O ZIP original `Templates/designeo-lite-v2.0.1.zip` contém 20 ficheiros e tem SHA-256:

`f171f8ed81a3bdd6c993c83dee5b9aa93d25c1a4a2974d6ddb5ebd69bdde95cd`

A v2.0.1 contém `theme.json` v3, header/footer, patterns `hero`, `services`, `about`, `cta`, `contact`, e templates `front-page`, `page`, `page-no-title`, `single`, `search` e `404`. **Não tem `templates/index.html`**, que é requisito do WordPress para o reconhecimento como block theme. Ter `index.php` e `theme.json` não substitui o fallback de blocos.

A correção é um único ficheiro `Templates/lite-v201-overlay/templates/index.html`, que usa apenas blocos core: header, main, Query Loop que herda a consulta corrente, post-title/excerpt, no-results, paginação e footer.

Os **20 ficheiros do ZIP original permanecem byte-a-byte iguais**. O ZIP candidato tem 21 ficheiros.

## Como gerar uma cópia segura

```bash
python scripts/build_lite_v201_fse_candidate.py --output /tmp/designeo-lite-v201-fse-test.zip
```

Este exemplo Unix é apenas ilustrativo; em Windows indicar uma pasta de trabalho isolada. O script valida hash do ZIP de origem, integridade ZIP, JSON do tema, comentários de blocos equilibrados, presença de padrões essenciais e compara os bytes de cada ficheiro. **Não substitui ficheiros existentes, não altera a pasta do Websign nem toca em WordPress.**

O candidato já foi gerado e verificado no computador Windows NPC (fora do projeto):  
`C:\projetos\Websign-Lite-Audit-20261010\candidate_v201\designeo-lite-v2.0.1-index-fallback-candidate.zip`  
SHA-256: `bbf0ed4b095e10ab5904ad7997460b910edd6baba95998a7387d8f6adeb5fffe`

O código de builder da branch foi testado numa segunda cópia isolada em `C:\projetos\Websign-Lite-Audit-20261010\repo_preview` usando o ZIP original copiado. **4/4 testes unittest passaram** (código de saída 0) e não modificaram o original.

## O que ainda NÃO ficou validado

- O WordPress reconhecer o ZIP como block theme real em execução e disponibilizar o editor do site.
- A renderização do `index.html` e a fallback hierarchy, tipografia, navegação, responsividade, acessibilidade e editor Gutenberg.
- Sintaxe PHP em runtime, compatibilidade com versões atuais WordPress/PHP, plugins, licenças e o `theme.json` aplicado pelo motor.
- Comportamento do CSS `!important`, performance e contraste; escopo do futuro template **mínimo** Lite.

Foi identificado no servidor o WP lab em `/home/wp-lab/htdocs/wp-lab.designeo.pt/wp-config.php`, mas o comando de inspeção via Remote Desktop Commander **foi impedido por uma restrição de segurança**. Não foi tentado contornar essa restrição e não ocorreu instalação ou alteração no *wp-lab*.

## Gate WP-LAB — apenas depois de acesso normal e aprovação

1. Confirmar que wp-lab é mesmo **staging isolado**, recuperar estado atual e preparar snapshot de ficheiros/BD com plano de restauro.
2. Instalar a cópia **não ativa** num slot de teste seguro. Antes, resolver o risco de a pasta interna `designeo-lite-base` coincidir com um tema já instalado; **não sobrescrever um tema ativo**.
3. Validar reconhecimento como block theme e acesso ao Editor do Site; abrir `index`, `page` e `front-page`; testar loops de arquivo, vazio, pesquisa e paginação.
4. Inserir os cinco patterns no editor; verificar CSS, links/foco, navegação móvel, tipografia e layouts em desktop/tablet/mobile.
5. Executar QA visual e estrutural e restauro/rollback; só depois aprovar Lite vNext e decidir o que deve ser retirado para cumprir a definição de **template mínimo**.
6. **Não migrar, ativar nem publicar em sites de clientes** antes de resultados e autorização específica.

Fontes WordPress: https://developer.wordpress.org/themes/core-concepts/theme-structure/ ; https://developer.wordpress.org/themes/templates/templates/

**Conclusão:** o defeito estrutural conhecido tem uma correção isolada validada estaticamente; ainda não existe certificado de compatibilidade WordPress em execução.
