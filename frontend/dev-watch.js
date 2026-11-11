const fs = require('fs');
const path = require('path');

const ROOT = '/app';
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
walk(ROOT).forEach(function(f) {
  try { mtimes.set(f, fs.statSync(f).mtimeMs); } catch (e) {}
});

process.stdout.write('[dev-watch] polling started\n');

setInterval(function() {
  walk(ROOT).forEach(function(f) {
    try {
      const mtime = fs.statSync(f).mtimeMs;
      if (mtimes.get(f) !== mtime) {
        const buf = fs.readFileSync(f);
        fs.writeFileSync(f, buf);
        // 書き戻し後の mtime を記録してループ防止
        mtimes.set(f, fs.statSync(f).mtimeMs);
        process.stdout.write('[dev-watch] changed: ' + f + '\n');
      }
    } catch (e) {}
  });
}, 500);
