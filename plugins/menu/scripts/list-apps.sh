#!/usr/bin/env bash
# Enumerate installable desktop entries as TAB separated:
#   <desktop-id-without-.desktop>\t<Name>\t<GenericName-or-Comment>\t<Icon>
#
# The shell's own AppLibrary is not reachable from this plugin: shell.qml only
# injects it into a scoped plugin shell, and that injection resolves to null for
# a third-party menu clone, so the stock "apps" provider can never contribute
# rows here. Enumerating directly keeps the section working regardless.
set -uo pipefail

# A tab or newline inside a field would shift every later column, so they are
# flattened to spaces before the row is printed.
clean() { printf '%s' "$1" | tr '\t\n' '  '; }

emit() { # file
  local f="$1" id name generic icon hidden
  id=$(basename "$f" .desktop)
  [ -n "$id" ] || return 0
  # Hidden entries: NoDisplay and Hidden both mean "do not list".
  if grep -qiE '^[[:space:]]*(NoDisplay|Hidden)=[[:space:]]*true' "$f"; then return 0; fi
  # Skip entries with no Exec, and skip aliases/url handlers that are not apps.
  grep -qiE '^[[:space:]]*Exec=' "$f" || return 0
  name=$(sed -n 's/^[[:space:]]*Name[[:space:]]*=[[:space:]]*//p' "$f" | head -1)
  [ -n "$name" ] || return 0
  generic=$(sed -n 's/^[[:space:]]*GenericName[[:space:]]*=[[:space:]]*//p' "$f" | head -1)
  [ -n "$generic" ] || generic=$(sed -n 's/^[[:space:]]*Comment[[:space:]]*=[[:space:]]*//p' "$f" | head -1)
  # Icon is the themed name or absolute path the entry asks for. It may be
  # absent or empty, and a local[icon] form names a file next to the entry.
  icon=$(sed -n 's/^[[:space:]]*Icon[[:space:]]*=[[:space:]]*//p' "$f" | head -1)
  case "$icon" in
    \[*\]*) icon="" ;;
  esac
  printf '%s\t%s\t%s\t%s\n' "$id" "$(clean "$name")" "$(clean "$generic")" "$(clean "$icon")"
}

for dir in \
  "${XDG_DATA_HOME:-$HOME/.local/share}/applications" \
  /usr/local/share/applications \
  /usr/share/applications \
  "${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"/../applications
do
  [ -d "$dir" ] || continue
  while IFS= read -r f; do emit "$f"; done < <(find "$dir" -maxdepth 1 -name '*.desktop' 2>/dev/null | LC_ALL=C sort)
done | awk -F'\t' '!seen[$1]++' | LC_ALL=C sort -t$'\t' -k2,2f
