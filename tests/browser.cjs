// Optional browser QA: npm install --no-save playwright, then node tests/browser.cjs.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '..');
  const base = process.env.ATLAS_BASE_URL || pathToFileURL(path.join(root, 'docs/')).href;
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.ATLAS_CHROME_PATH ? { executablePath: process.env.ATLAS_CHROME_PATH } : {}),
  });
  const errors = [];
  try {
    await fs.mkdir(path.join(root, 'screenshots'), { recursive: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    const go = relative => page.goto(new URL(relative, base).href);
    await go('index.html');
    const total = await page.locator('[data-entry]').count();
    assert(total >= 6);
    await page.screenshot({ path: path.join(root, 'screenshots/home-desktop.png'), fullPage: true });
    await page.locator('.filter[data-category="writing"]').click();
    assert.equal(await page.locator('[data-entry]:visible').count(), 2);
    await page.locator('#search').fill('Lead');
    assert.equal(await page.locator('[data-entry]:visible').count(), 1);
    await page.locator('#search').fill('xyz-no-result');
    assert(await page.locator('#empty').isVisible());
    await page.locator('#reset-search').click();
    assert.equal(await page.locator('[data-entry]:visible').count(), total);
    assert(await page.locator('#search').evaluate(element => element === document.activeElement));
    await go('entries/preselection.html');
    assert(await page.locator('[data-panel="before"]').isVisible());
    assert(!(await page.locator('[data-panel="after"]').isVisible()));
    const after = page.locator('[data-view="after"]');
    await after.focus();
    await page.keyboard.press('Enter');
    assert.equal(await after.getAttribute('aria-pressed'), 'true');
    assert(await page.locator('[data-panel="after"]').isVisible());
    await page.screenshot({ path: path.join(root, 'screenshots/entry-desktop.png'), fullPage: true });
    for (const width of [360, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const route of ['index.html', 'entries/preselection.html', 'guide.html']) {
        await go(route);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `Overflow at ${width}: ${route}`);
      }
    }
    await page.screenshot({ path: path.join(root, 'screenshots/guide-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 360, height: 800 });
    await go('index.html');
    await page.screenshot({ path: path.join(root, 'screenshots/home-mobile.png'), fullPage: true });
    const noJS = await browser.newContext({ javaScriptEnabled: false });
    const staticPage = await noJS.newPage();
    await staticPage.goto(new URL('entries/preselection.html', base).href);
    assert(await staticPage.locator('[data-panel="before"]').isVisible());
    assert(await staticPage.locator('[data-panel="after"]').isVisible());
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ result: 'passed', entries: total, widths: [360, 768, 1440], checks: ['filter + search', 'empty + reset', 'keyboard comparison', 'no-JS reading', 'layout overflow', 'page errors'] }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
