#!/usr/bin/env bash
# Install the haus skills into agent skill locations, so they work beyond OpenCode.
# Symlinks by default (single source of truth: this repo). Use --copy if your agent
# does not follow symlinks. Idempotent: reruns replace old links.
#
# Usage:
#   ./skills/install.sh                # all personal locations (opencode, claude, agents)
#   ./skills/install.sh opencode       # ~/.config/opencode/skills
#   ./skills/install.sh claude         # ~/.claude/skills
#   ./skills/install.sh agents         # ~/.agents/skills (cross-agent convention)
#   ./skills/install.sh --copy ...     # copy files instead of symlinking
#   ./skills/install.sh --dry-run ...  # show what would happen
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COPY=0
DRY=0
TARGETS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) COPY=1 ;;
    --dry-run) DRY=1 ;;
    opencode|claude|agents) TARGETS+=("$1") ;;
    all) TARGETS=(opencode claude agents) ;;
    *) echo "unknown option: $1 (expected: opencode, claude, agents, all, --copy, --dry-run)" >&2; exit 1 ;;
  esac
  shift
done
[ ${#TARGETS[@]} -gt 0 ] || TARGETS=(opencode claude agents)

place() {  # place <target-dir> <skill-name>
  local dir="$1" name="$2" dest="$1/$2"
  mkdir -p "$dir"
  if [ "$COPY" = 1 ]; then
    rm -rf "$dest"
    cp -R "$SRC/$name" "$dest"
  else
    rm -rf "$dest"
    ln -s "$SRC/$name" "$dest"
  fi
  echo "installed $name -> $dest"
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    opencode) DIR="$HOME/.config/opencode/skills" ;;
    claude)   DIR="$HOME/.claude/skills" ;;
    agents)   DIR="$HOME/.agents/skills" ;;
  esac
  for name in haus-setup haus-update; do
    if [ "$DRY" = 1 ]; then
      echo "would install $name -> $DIR/$name"
    else
      place "$DIR" "$name"
    fi
  done
done

[ "$DRY" = 1 ] || echo "done. restart your agent client to pick them up."
