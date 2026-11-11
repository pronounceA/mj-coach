const fs = require('fs');
const path = require('path');

const SRC = '/app-host';
const DST = '/app';
const IGNORE = new Set(['node_modules', '.next', '.git', '.turbo']);

function copyDir(srcDir, dstDir) {
  let entries;
  try { entries = fs.readdirSync(srcDir, { withFileTypes: true }); }
  catch { return; }
  fs.mkdirSync(dstDir, { recursive: true });
  for (const e of entries) {
    if (IGNORE.has(e.name)) continue;
    const s = path.join(srcDir, e.name);
    const d = path.join(dstDir, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else try { fs.copyFileSync(s, d); } catch {}
  }
}

process.stdout.write('[dev-init] copying source files...\n');
copyDir(SRC, DST);
process.stdout.write('[dev-init] done\n');
