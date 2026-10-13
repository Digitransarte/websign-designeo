# WEB-02 · SiteDocument → Lite selection v0.1

**Status:** implementation candidate; review/CI and WordPress runtime QA pending. Not a release.

This is the first deliberately narrow boundary between a Design Agent-authored structured document and the existing Designeo Lite Core/Pattern Library pipeline. It **selects allowlisted patterns**. It does **not** convert a visual design to Gutenberg, inject customer text/assets/tokens, modify the source theme, or publish a site.

## Input contract

```json
{
  "schema": "designeo.site-document.v0.1",
  "pages": [
    {
      "slug": "home",
      "sections": [
        {"pattern": "hero"},
        {"pattern": "services"},
        {"pattern": "cta"}
      ]
    }
  ]
}
```

Only one page named `home` is supported in this gate. Each section is an allowlisted `hero`, `services`, `about` or `cta`, without duplicates. Unknown keys are rejected rather than silently ignored. The existing composer's checksums, output overwrite protection and editorial preflight remain effective.

## Run (isolated preview only)

Create Core and Library using `scripts.build_lite_core_library_v01` from this branch, then:

```bash
python -m scripts.site_document_lite_v01 --document /tmp/site.json \
  --core /tmp/designeo-lite-core.zip \
  --library /tmp/designeo-lite-patterns.zip \
  --output /tmp/designeo-lite-preview.zip
python -m unittest tests.test_site_document_lite_v01
```

The output is a **theme composition preview**, not a Gutenberg page assembled from a design. `publish_ready=false` and `wordpress_runtime_tested=false` are explicit.

## Next implementation gate

1. Run tests and review this adapter against the existing Core/Library PR.
2. Define versioned content/token/asset semantics and safe mapping to Gutenberg block attributes and markup.
3. Validate Gutenberg block serialization round-trip and visual fidelity on a disposable WordPress clone, including responsive/editor checks.
4. Keep all production operations disabled until signed-off backup/restore, rollback, and staging QA.

No client content or credentials should be committed to Git.
