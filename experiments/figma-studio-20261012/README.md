# Designeo Studio — Figma → Websign SiteDocument → WordPress (Pilot 01)

**Date:** 2026-10-12  
**Status:** Published *only* on privately IP-allowlisted WordPress staging. Pilot, not production design approval.

## Pointers

- **Figma desktop:** https://www.figma.com/design/lC0PI3RGoX8SNuF7aOutKS?node-id=2-2 (1440×3350)
- **Figma mobile:** https://www.figma.com/design/lC0PI3RGoX8SNuF7aOutKS?node-id=3-2 (390×4200)
- **Actual WordPress:** https://core-stage.designeo.pt/designeo-studio-figma/ (new page ID 14)
- Independent CloudPanel staging WordPress 7.1.3; active project child `designeo-corestage-atelier` and neutral Core parent `designeo-lite-core-v1 1.0.0-alpha.3`.

## What really ran

1. **Read Figma high-fidelity editable layers** from desktop node `2:2` with mobile counterpart `3:2`; identified text, positioning, colors and conceptual graphics. Nothing is a flattened screenshot copied into WordPress.
2. Manually interpreted those layouts as **seven semantic sections** in an actual `websign.site.v0.1` SiteDocument (the current schema). See `site-document.json`. Node source references are recorded in selected semantic content nodes.
3. Executed the existing local `websign_vnext.validation.validate_site_document` and `websign_vnext.renderers.gutenberg.render_site_document`. See `compiled-unmodified-gutenberg.html` available privately on the staging host; the compiled output was 100% Gutenberg core block markup (group/columns/column/paragraph/heading/buttons/button).
4. The current Websign schema only supports **two-column groups and a short closed token vocabulary**, not Figma's independent editorial shapes, three- or four-column grids, or art-direction intents. An explicitly isolated pilot adapter added only semantic CSS classes + anchor IDs to the seven section groups. The result `compiled-pilot-gutenberg.html` is also Gutenberg core blocks; it does not contain Custom HTML blocks.
5. The **presentation layer** is `pilot.css` in the dedicated *project child theme*, enqueued **only for WordPress page ID 14** via a minimal WordPress `functions.php`. The page also has its own FSE page template (no change to other templates). The neutral Lite Core is byte-untouched. The CSS reconstructs conceptual graphics from native editable text and CSS decorative elements, not imported site screenshots. Colors #141414/#F5411F/#F0EDE7 and Jost/Inter/Space Mono reflect the Figma exploration.
6. The page was created as a **draft** through WP-CLI, validated, then explicitly published on the private staging URL. The old stage homepage ID 6 was not replaced.

## Reproducibility and known gap

The local NPC workspace **C:\\projetos\\websign-designeo\\websign_vnext** contains renderer/validator code that had not yet been synced to the `Digitransarte/websign-designeo` remote main branch (verified by comparing source files). To avoid silently reconstructing a parallel pipeline, the pilot used a temporary copy of four **non-sensitive local modules** in the root-only, isolated work folder `/opt/designeo-lite-corestage-20261012/figma-pilot/local-compiler-copy/`. The original Windows workspace was not modified.

This GitHub branch preserves the input SiteDocument, exact adapter script, presentation stylesheet, semantic manifest and compiled Gutenberg output, but **does not pretend to supply the missing upstream renderer implementation**. Synchronizing/reviewing the original local compiler is a separate work item. The adapter script won't run in a clean checkout of remote main until the underlying `websign_vnext` package is committed/recovered.

The Figma-to-SiteDocument semantic interpretation was done manually by the agent: **automatic extraction, component identification and responsive intent inference do not exist yet as a proven automated service**. Do not market this as a one-click pixel-perfect Figma import.

## Automated runtime checks

- Actual page HTTPS 200 with certificate verification 0; external desktop accesses only from previously allowlisted IP.
- Figma pilot CSS loaded only on page ID 14; other staging pages do not enqueue that stylesheet.
- `wp parse_blocks` / serialize / parse roundtrip stable; 1 editable H1; 0 Custom HTML blocks.
- Playwright Chromium captures tested at **1440, 768, 390px**: status 200, no horizontal overflow, no JS page errors, loaded Jost/Inter/Space Mono, 1 H1, correct CSS/background, working internal anchor links.
- After detected mobile Gutenberg column flex wrapping, targeted `@media(max-width:720px)` fix removed the extra header row.
- **axe-core 4.10.3 WCAG 2.1 A/AA** after correction: **0 detected violations / 1 incomplete/manual-review finding / 8 applicable passes** in desktop and mobile. Brand bright orange remains for artwork; small text and buttons use higher-contrast shades, intentionally differing slightly from Figma.
- No authenticated Gutenberg editor save/reopen of **this actual page** has yet been performed by a human. WP-CLI semantic serialization passing does not guarantee a perfect editor WYSIWYG experience. The prior separate GenerateBlocks test in disposable CI remains available, but is not proof of this page.

## Deployment isolation and rollbacks

- Prechange root-only staging database export and project child theme style/theme.json backups reside under `/opt/designeo-lite-corestage-20261012/figma-pilot/prepublish/`.
- All new styling is confined to the project child and page ID 14. `theme.json` registers a custom page template; site-wide tokens/palette were not modified.
- The old WordPress homepage remains ID 6. The neutral parent remains `1.0.0-alpha.3`. The original `wp-lab` and `/lite-core-qa/` are unchanged.
- Rollback of the visual pilot is deletion/unpublishing of page ID14 after authorization plus restoring the exact saved child style/theme.json and removing project-only CSS/functions.php/template, after reviewing any intervening edits. **Do not overwrite the project child from an old backup without a conflict check.**

## Actual gaps to solve next (do not invent a new parallel framework)

1. Recover/review and version the **existing local Websign renderer**, currently absent remotely.
2. Extend versioned SiteDocument design semantics (3–4 responsive grid columns, typographic intents, branded visual modules, responsive ordering), with native Gutenberg patterns and child-theme token bindings.
3. Convert the present manually curated Figma node map into a repeatable design-to-SiteDocument adapter; compare screenshots desktop/mobile and generate diagnostic differences.
4. Human Gutenberg editor roundtrip on this exact page, keyboard/mobile manual review and deferred NVDA screen reader check.
5. Later: replace experimental pseudo-element graphic implementation with reusable **native Gutenberg patterns**; prefer a small documented design system instead of a growing page-specific stylesheet.
