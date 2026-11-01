import {createRequire} from 'node:module';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const base = 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await (await browser.newContext({viewport: {width: 1440, height: 1000}})).newPage();
const bad = [];
page.on('response', r => { if (r.status() >= 400) bad.push(r.status() + ' ' + r.url()); });
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
await page.goto(base + '/static/walk-preview.html', {waitUntil: 'domcontentloaded'});
await page.waitForTimeout(8000);
const info = await page.evaluate(() => ({
  ready: document.querySelector('#stage')?.dataset.ready || 'no',
  canvas: document.querySelectorAll('#stage canvas').length,
  status: document.querySelector('#status')?.textContent,
}));
console.log(JSON.stringify({info, bad, errors}, null, 2));
await browser.close();
