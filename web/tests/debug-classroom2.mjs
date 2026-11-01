import {createRequire} from 'node:module';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const base = 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await (await browser.newContext({viewport: {width: 1440, height: 1000}})).newPage();
const reqs = [];
page.on('response', r => { if (r.url().includes('/api/')) reqs.push(r.status() + ' ' + r.url()); });
await page.goto(base + '/#classroom', {waitUntil: 'domcontentloaded'});
await page.waitForTimeout(6000);
const info = await page.evaluate(() => ({
  contentText: (document.querySelector('#content')?.innerText || '').slice(0, 400),
  modalText: (document.querySelector('#modal-body')?.innerText || '').slice(0, 400),
  modalOpen: document.querySelector('#modal')?.open,
  hasClassroom: !!document.querySelector('.classroom'),
  status: document.querySelector('#sync-status')?.textContent,
}));
console.log(JSON.stringify(info, null, 2));
console.log('API', JSON.stringify(reqs.slice(-10), null, 2));
await browser.close();
