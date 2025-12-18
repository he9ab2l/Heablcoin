#!/usr/bin/env bash
set -euo pipefail

msg="${1:-}"
if [[ -z "${msg}" ]]; then
  msg="chore: update ($(date +'%Y-%m-%d %H:%M:%S'))"
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository." >&2
  exit 1
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes to commit."
  exit 0
fi

branch="$(git rev-parse --abbrev-ref HEAD)"

git add -A
git commit -m "${msg}"
git push origin "${branch}"

