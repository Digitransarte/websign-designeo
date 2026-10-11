/** WEB-02 root-cause browser regression gate.
 * Run: WEB02_URL=https://wp-lab.designeo.pt node tests/web02_render_contract.cjs
 * Requires playwright and a local Chrome/Chromium installation.
 * Read-only: does not submit forms, change WordPress or toggle plugins.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.WEB02_CHROME ? { executablePath: process.env.WEB02_CHROME } : {})
  });
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.goto(process.env.WEB02_URL || 'https://wp-lab.designeo.pt/', {
        waitUntil: 'networkidle', timeout: 30000
      });
      const result = await page.evaluate(() => {
        const hero = document.querySelector('.dl-hero');
        const button = hero?.querySelector('.wp-block-button__link');
        const header = document.querySelector('.dl-site-header');
        const nav = header?.querySelector('.wp-block-navigation');
        if (!hero || !button || !header || !nav) throw new Error('Missing structural elements');
        const b = getComputedStyle(button), n = nav.getBoundingClientRect(),
              h = header.getBoundingClientRect();
        const rgb = value => [...value.matchAll(/[\d.]+/g)].slice(0, 3).map(m => Number(m[0]));
        const luminance = values => values.map(v => {
          v /= 255;
          return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
        }).reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
        const a = luminance(rgb(b.color)), c = luminance(rgb(b.backgroundColor));
        const contrast = (Math.max(a,c) + .05) / (Math.min(a,c) + .05);
        return { contrast, buttonColor: b.color, buttonBackground: b.backgroundColor,
          headerHeight: h.height, navHeight: n.height,
          navBottom: n.bottom, headerBottom: h.bottom,
          navNames: nav.innerText.slice(0, 120) };
      });
      console.log(JSON.stringify({ viewport: width, ...result }));
      assert.ok(result.contrast >= 4.5,
        `Button text contrast below WCAG AA at ${width}px: ${result.contrast.toFixed(2)}`);
      if (width >= 1024) {
        assert.ok(result.navBottom <= result.headerBottom + 1,
          `Navigation overflows header at ${width}px`);
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(err => { console.error(err.message); process.exitCode = 1; });
