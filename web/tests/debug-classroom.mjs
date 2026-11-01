import {createRequire} from 'node:module';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const base = 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await (await browser.newContext({viewport: {width: 1440, height: 1000}})).newPage();
const logs = [];
page.on('console', m => logs.push(m.type() + ': ' + m.text()));
page.on('pageerror', e => logs.push('pageerror: ' + e.message));
await page.goto(base + '/#classroom', {waitUntil: 'networkidle'});
await page.waitForTimeout(2500);
const info = await page.evaluate(() => ({
  href: location.href,
  hash: location.hash,
  hasClassroom: !!document.querySelector('.classroom'),
  hasStage: !!document.querySelector('.class-stage'),
  sceneHost: !!document.querySelector('.scene-host'),
  canvas: document.querySelectorAll('canvas').length,
  contentText: (document.querySelector('#content')?.innerText || '').slice(0, 300),
  modalOpen: document.querySelector('#modal')?.open,
  status: document.querySelector('.stage-status')?.textContent,
}));
console.log(JSON.stringify(info, null, 2));
console.log('LOGS', JSON.stringify(logs.slice(-15), null, 2));
await browser.close();
