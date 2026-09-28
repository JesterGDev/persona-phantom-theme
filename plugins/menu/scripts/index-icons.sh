#!/usr/bin/env bash
# List app and device icon files, one absolute path per line, so the menu can
# resolve a desktop entry's Icon= name to a real file.
#
# Only the apps/ and devices/ subdirectories are indexed, matching AppLibrary:
# an unconstrained themed lookup can resolve an app name such as "zoom" to an
# action icon, and a huge unfiltered index is slow to enumerate on every menu
# open. SVGs are emitted before PNGs because the caller keeps the first hit per
# name, so a scalable icon wins over a raster one.
set -uo pipefail

dirs=("$HOME/.icons" "$HOME/.local/share/icons")
IFS=':' read -r -a data_dirs <<< "${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
for d in "${data_dirs[@]}"; do
  dirs+=("$d/icons")
done
unset IFS

for ext in svg png; do
  for base in "${dirs[@]}"; do
    [ -d "$base" ] || continue
    find "$base" \( -path "*/apps/*" -o -path "*/devices/*" \) -name "*.$ext" 2>/dev/null
  done
  find /usr/share/pixmaps -maxdepth 1 -name "*.$ext" 2>/dev/null
done
