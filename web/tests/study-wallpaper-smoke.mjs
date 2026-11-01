import {createRequire} from 'node:module';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const root = join(process.cwd(), 'web/.runtime/study-wallpaper');
await mkdir(root, {recursive: true});
const base = process.env.TREECOURT_URL || 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const context = await browser.newContext({viewport: {width: 1440, height: 900}});
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push('console: ' + m.text()); });
try {
  await page.goto(base + '/wallpaper', {waitUntil: 'domcontentloaded'});
  await page.waitForFunction(() => document.querySelector('#focus-stage')?.dataset.ready === 'true', null, {timeout: 30000});
  await page.waitForTimeout(1200);
  await page.screenshot({path: join(root, 'focus-idle.png')});
  const initial = await page.locator('#fc-time').textContent();
  await page.locator('#fc-start').click();
  await page.waitForTimeout(2200);
  const running = await page.locator('#fc-time').textContent();
  const line = await page.locator('#fc-line').textContent();
  await page.screenshot({path: join(root, 'focus-running.png')});
  await page.locator('#fc-end').click();
  await page.waitForTimeout(600);
  const stats = await page.locator('#fc-stats').textContent();
  const canvas = await page.locator('#focus-stage video').count();
  console.log(JSON.stringify({initial, running, line, stats, canvas, errors}, null, 2));
  if (initial !== '25:00') throw new Error('初始计时不是 25:00: ' + initial);
  if (running === initial) throw new Error('开始后计时没有走动');
  if (canvas < 1) throw new Error('陪学动画未挂载');
  if (errors.length) throw new Error('errors: ' + errors.join(' | '));
  console.log('FOCUS_COMPANION_OK ' + root);
} finally {
  await context.close(); await browser.close();
}
