import {createRequire} from 'node:module';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const base = process.env.TREECOURT_URL || 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await (await browser.newContext({viewport: {width: 1440, height: 1000}})).newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push('console: ' + m.text()); });
try {
  await page.goto(base + '/static/walk-preview.html', {waitUntil: 'domcontentloaded'});
  await page.waitForFunction(() => document.querySelector('#stage')?.dataset.ready === 'true', null, {timeout: 60000}).catch(() => {});
  await page.waitForTimeout(1200);
  const info = await page.evaluate(() => ({
    ready: document.querySelector('#stage')?.dataset.ready || 'no',
    canvas: document.querySelectorAll('#stage canvas').length,
    status: document.querySelector('#status')?.textContent,
  }));
  console.log(JSON.stringify({...info, errors}, null, 2));
  if (info.ready !== 'true' || info.canvas < 1) throw new Error('walk preview not ready');
  if (errors.length) throw new Error('errors: ' + errors.join(' | '));
  console.log('WALK_PREVIEW_SMOKE_OK');
} finally {
  await browser.close();
}
