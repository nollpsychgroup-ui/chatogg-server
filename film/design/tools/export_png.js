// Export every design SVG to a ~1280px-wide PNG in film/design/png/.  node film/design/tools/export_png.js
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const D = path.resolve(__dirname, '..');
const files = ['sheets/lineup', 'sheets/noor', 'sheets/kai', 'sheets/bea', 'sheets/walter',
  'expressions/noor-expressions', 'expressions/walter-expressions', 'expressions/bea-expressions',
  'expressions/kai-expressions', 'props/props'];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  fs.mkdirSync(path.join(D, 'png'), { recursive: true });
  for (const f of files) {
    const svg = path.join(D, f + '.svg');
    const m = fs.readFileSync(svg, 'utf8').match(/viewBox="0 0 (\d+) (\d+)"/);
    const w = 1280, h = Math.round(w * m[2] / m[1]);
    await p.setViewportSize({ width: w, height: h });
    await p.goto('file://' + svg);
    await p.evaluate(([w, h]) => { const s = document.querySelector('svg'); s.setAttribute('width', w); s.setAttribute('height', h); document.body && (document.body.style.margin = 0); }, [w, h]);
    await p.screenshot({ path: path.join(D, 'png', path.basename(f) + '.png'), clip: { x: 0, y: 0, width: w, height: h } });
  }
  await b.close();
})();
