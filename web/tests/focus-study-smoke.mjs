import {createRequire} from 'node:module';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const root = join(process.cwd(), 'web/.runtime/focus-study'); await mkdir(root, {recursive: true});
const base = process.env.TREECOURT_URL || 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push('console: ' + m.text()); });
try {
  await page.goto(base + '/#focus', {waitUntil: 'domcontentloaded'});
  await page.locator('#focus-note').waitFor({timeout: 20000});
  // 等自习室动画画布就绪
  await page.waitForFunction(() => document.querySelector('#quiet-room')?.dataset.ready === 'true', null, {timeout: 40000}).catch(() => {});
  const ready = await page.evaluate(() => document.querySelector('#quiet-room')?.dataset.ready || 'no');
  const canvas = await page.locator('#quiet-room video').count();
  // 测试便签持久化
  const note = '今天的目标：完成四级第一章；鼓励自己：慢一点也没关系。';
  await page.fill('#focus-note', note);
  await page.reload({waitUntil: 'domcontentloaded'});
  await page.locator('#focus-note').waitFor({timeout: 20000});
  const saved = await page.inputValue('#focus-note');
  await page.screenshot({path: join(root, 'focus-study.png'), fullPage: false});
  console.log(JSON.stringify({ready, canvas, notePersisted: saved === note, saved, errors}, null, 2));
  if (!saved.includes('四级第一章')) throw new Error('note not persisted');
  if (canvas < 1) throw new Error('no video in quiet-room');
  if (errors.length) throw new Error('errors: ' + errors.join(' | '));
  console.log('FOCUS_STUDY_SMOKE_OK ' + root);
} finally {
  await context.close(); await browser.close();
}
