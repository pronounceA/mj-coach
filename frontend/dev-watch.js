const fs = require('fs');
const path = require('path');

const SRC_ROOT = '/app-host';
const DST_ROOT = '/app';
const SIGNAL = '/tmp/reload_signal';
const IGNORE = new Set(['node_modules', '.next', '.git', '.turbo']);

function walk(dir, files) {
  files = files || [];
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
  catch { return files; }
  for (const e of entries) {
    if (IGNORE.has(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, files);
    else files.push(p);
  }
  return files;
}

const mtimes = new Map();
walk(SRC_ROOT).forEach(function(f) {
  try { mtimes.set(f, fs.statSync(f).mtimeMs); } catch {}
});

try { fs.writeFileSync(SIGNAL, '0'); } catch {}

process.stdout.write('[dev-watch] polling started\n');

let debounceTimer = null;

function signalReload() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(function() {
    try {
      fs.writeFileSync(SIGNAL, String(Date.now()));
      process.stdout.write('[dev-watch] reload signal sent\n');
    } catch {}
    debounceTimer = null;
  }, 100);
}

setInterval(function() {
  walk(SRC_ROOT).forEach(function(f) {
    try {
      const mtime = fs.statSync(f).mtimeMs;
      if (mtimes.get(f) !== mtime) {
        mtimes.set(f, mtime);

        const relPath = path.relative(SRC_ROOT, f);
        const dstPath = path.join(DST_ROOT, relPath);

        fs.mkdirSync(path.dirname(dstPath), { recursive: true });
        fs.writeFileSync(dstPath, fs.readFileSync(f));

        process.stdout.write('[dev-watch] synced: ' + relPath + '\n');
        signalReload();
      }
    } catch {}
  });
}, 500);
