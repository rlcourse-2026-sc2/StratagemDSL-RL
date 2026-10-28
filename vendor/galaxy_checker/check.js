#!/usr/bin/env node
// StratagemDSL L5: type-check generated MapScript.galaxy with plaxtony.
//
//   node check.js [--data DIR] FILE.galaxy ...   -> JSON on stdout
//
// DIR holds TriggerLibs/{natives.galaxy, natives_missing.galaxy, NativeLib_h.galaxy,
// NativeLib.galaxy, GameData/*.galaxy} from https://github.com/Talv/sc2-data-trigger
// (mods/core.sc2mod/base.sc2data). tools/fetch_galaxy_checker.sh installs both.
'use strict';
const fs = require('fs');
const path = require('path');
const { Store, createTextDocumentFromFs } = require('plaxtony/lib/src/service/store');
const { TypeChecker } = require('plaxtony/lib/src/compiler/checker');

const args = process.argv.slice(2);
let data = process.env.STRAT_SC2_TRIGGER_DATA || path.join(__dirname, 'sc2data');
const di = args.indexOf('--data');
if (di >= 0) { data = args[di + 1]; args.splice(di, 2); }
const libs = path.join(data, 'TriggerLibs');
if (!fs.existsSync(path.join(libs, 'natives.galaxy'))) {
  console.error(`missing ${libs}/natives.galaxy; run tools/fetch_galaxy_checker.sh`);
  process.exit(2);
}
const store = new Store();
store.rootPath = data;
const libFiles = ['natives.galaxy', 'natives_missing.galaxy', 'NativeLib_h.galaxy', 'NativeLib.galaxy']
  .map(f => path.join(libs, f))
  .concat(fs.readdirSync(path.join(libs, 'GameData')).filter(f => f.endsWith('.galaxy')).sort()
    .map(f => path.join(libs, 'GameData', f)));
for (const f of libFiles) store.updateDocument(createTextDocumentFromFs(f));

const CATEGORY = { 1: 'error', 2: 'warning', 3: 'message', 4: 'hint' };
const out = [];
for (const target of args) {
  const doc = createTextDocumentFromFs(path.resolve(target));
  store.updateDocument(doc);
  const sf = store.documents.get(doc.uri);
  const checker = new TypeChecker(store);
  const diags = [...sf.parseDiagnostics, ...checker.checkSourceFile(sf, true)];
  out.push({
    file: target,
    diagnostics: diags.map(d => ({ line: d.line + 1, col: d.col + 1, severity: CATEGORY[d.category] || String(d.category),
      code: d.code, message: d.messageText })),
  });
  store.removeDocument(doc.uri);
}
process.stdout.write(JSON.stringify(out, null, 1) + '\n');
