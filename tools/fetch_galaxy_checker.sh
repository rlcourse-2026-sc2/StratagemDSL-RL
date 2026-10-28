#!/usr/bin/env bash
# Install the open-source Galaxy checker used by layer 5 (no galaxycc needed):
#   * plaxtony 1.10.5 (MIT, https://github.com/Talv/plaxtony) from npm
#   * the core TriggerLibs headers from https://github.com/Talv/sc2-data-trigger
# Needs node >= 16, npm and git. Result: vendor/galaxy_checker/{node_modules,sc2data}.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)/vendor/galaxy_checker"
cd "$here"
npm install --no-audit --no-fund --loglevel=error
if [ ! -f sc2data/TriggerLibs/natives.galaxy ]; then
  tmp="$(mktemp -d)"
  git clone --depth 1 --filter=blob:none --sparse https://github.com/Talv/sc2-data-trigger.git "$tmp/repo"
  git -C "$tmp/repo" sparse-checkout set mods/core.sc2mod/base.sc2data/TriggerLibs
  src="$tmp/repo/mods/core.sc2mod/base.sc2data/TriggerLibs"
  mkdir -p sc2data/TriggerLibs/GameData
  cp "$src"/natives.galaxy "$src"/natives_missing.galaxy "$src"/NativeLib_h.galaxy "$src"/NativeLib.galaxy sc2data/TriggerLibs/
  cp "$src"/GameData/*.galaxy sc2data/TriggerLibs/GameData/
  git -C "$tmp/repo" rev-parse HEAD > sc2data/REVISION
  rm -rf "$tmp"
fi
echo "galaxy checker ready: $here"
