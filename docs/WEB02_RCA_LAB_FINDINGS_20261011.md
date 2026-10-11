# WEB-02 RCA — 2026-10-11 lab evidence and source-of-truth gate

Scope: live lab only, explicitly authorised. No client production site.

## Recorded changes in wp-lab

Active theme: `designeo-lite-lab-v01` v2.0.1 at `wp-lab.designeo.pt`.
A paired local SQL + theme-file backup was created before edits at a private server path and is recorded in Designeo OS.

1. `assets/css/global.css`: the generic text-link rule `.entry-content a` was changed to `.entry-content a:not(.wp-block-button__link)`, preventing content links from overriding the button foreground set by theme.json.
2. `parts/header.html` and `parts/footer.html`: implicit `core/navigation` content was replaced with explicit `core/navigation-link` children targeting `/` and `/#servicos`. This prevents automatic `core/page-list` injection from old lab pages.

These are **lab edits**; they are not yet part of the generated Core ZIP or base theme distribution.

## Measured effects

Chrome Playwright read-only browser inspection at 1440px and 390px:
- Before: hero primary button color/background both rgb(26,26,24).
- After: button foreground rgb(255,255,255), background rgb(26,26,24).
- Before: desktop navigation measured 204px tall inside a 64px header.
- After: desktop navigation 21px tall inside the same 64px header.
- Mobile navigation after: 40px tall; controls remain within header.
- HTTP 200 after change.

Websign runtime stylesheet toggle did not change the button defect, so it was **not** the source of that specific problem.

## Release gate

The source build currently composes deterministic ZIPs from immutable legacy ZIP inputs and a set of overlays. Manual changes in the lab therefore risk being lost on regeneration.

Before deploying a generated theme over the lab changes:
- Introduce canonical, version-controlled theme source or a reviewed deterministic source overlay with structural assertions.
- Ensure the build tests reproduce these exact scoped-link and explicit-navigation contracts.
- Run `tests/web02_render_contract.cjs` against lab and staging, including genuine browser editor validation.
- Avoid hardcoding a customer's two-link lab navigation into the reusable theme: use an explicit per-site navigation contract generated from SiteDocument/site configuration.
- Keep the existing lab backup / rollback documentation.

No claim is made that the pipeline generates this final result automatically yet.
