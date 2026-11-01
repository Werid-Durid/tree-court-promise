import {createRequire} from 'node:module';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
const modules = process.env.TREECOURT_NODE_MODULES || join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require = createRequire(join(modules, 'package.json'));
const {chromium} = require('playwright');
const root = join(process.cwd(), 'web/.runtime/classroom-style'); await mkdir(root, {recursive: true});
const base = process.env.TREECOURT_URL || 'http://127.0.0.1:8765';
const browser = await chromium.launch({channel: 'msedge', headless: true});
const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push('console: ' + m.text()); });
try {
  await page.goto(base, {waitUntil: 'domcontentloaded'});
  await page.locator('#hero-start').waitFor({timeout: 30000});
  await page.locator('#hero-start').click();
  await page.locator('[data-enter]').first().waitFor({timeout: 20000});
  await page.locator('[data-enter]').first().click();
  await page.waitForFunction(() => document.querySelector('.scene-host')?.dataset.ready === 'true', null, {timeout: 90000}).catch(() => {});
  await page.waitForTimeout(1500);
  const state = await page.evaluate(() => {
    const host = document.querySelector('.scene-host');
    return {
      ready: host?.dataset.ready || 'no',
      animated: host?.dataset.animated || 'no',
      canvas: document.querySelectorAll('.scene-host canvas').length,
      hasClassroom: !!document.querySelector('.classroom'),
      status: document.querySelector('.stage-status')?.textContent,
    };
  });
  await page.screenshot({path: join(root, 'classroom-style.png')});
  console.log(JSON.stringify({...state, errors}, null, 2));
  if (state.ready !== 'true' || state.canvas < 1) throw new Error('classroom 3D not ready');
  if (errors.length) throw new Error('errors: ' + errors.join(' | '));
  console.log('CLASSROOM_STYLE_SMOKE_OK ' + root);
} finally {
  await context.close(); await browser.close();
}
