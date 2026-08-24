#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  github_state_branch.sh restore <database_path>
  github_state_branch.sh save <database_path>

Required environment variables:
  GITHUB_TOKEN
  GITHUB_REPOSITORY

Optional environment variables:
  STATE_BRANCH   Defaults to citation-radar-state
EOF
}

if [ "$#" -ne 2 ]; then
  usage >&2
  exit 2
fi

command_name="$1"
database_path="$2"
state_branch="${STATE_BRANCH:-citation-radar-state}"
database_name="$(basename "$database_path")"

if [ -z "${GITHUB_TOKEN:-}" ] || [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "GITHUB_TOKEN and GITHUB_REPOSITORY are required." >&2
  exit 2
fi

repo_url="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
state_dir="$(mktemp -d)"
trap 'rm -rf "$state_dir"' EXIT

git -C "$state_dir" init >/dev/null 2>&1
git -C "$state_dir" config user.name "github-actions[bot]"
git -C "$state_dir" config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git -C "$state_dir" remote add origin "$repo_url"

fetch_state_branch() {
  git -C "$state_dir" fetch --depth=1 origin "$state_branch" >/dev/null 2>&1
}

checkout_state_branch() {
  if fetch_state_branch; then
    git -C "$state_dir" checkout -B "$state_branch" FETCH_HEAD >/dev/null 2>&1
    return 0
  fi

  git -C "$state_dir" checkout --orphan "$state_branch" >/dev/null 2>&1
  git -C "$state_dir" rm -rf . >/dev/null 2>&1 || true
  return 1
}

write_state_readme() {
  cat >"$state_dir/README.md" <<'EOF'
# Citation Radar state

This branch stores the SQLite database used by the scheduled GitHub Actions workflow.
EOF
}

case "$command_name" in
  restore)
    if ! checkout_state_branch; then
      echo "State branch not found; starting with a fresh database."
      exit 1
    fi

    if [ ! -f "$state_dir/$database_name" ]; then
      echo "State branch exists but $database_name is missing."
      exit 1
    fi

    cp "$state_dir/$database_name" "$database_path"
    echo "Restored $database_name from $state_branch."
    ;;

  save)
    if [ ! -f "$database_path" ]; then
      echo "Database file not found: $database_path" >&2
      exit 2
    fi

    checkout_state_branch || true
    write_state_readme
    cp "$database_path" "$state_dir/$database_name"

    git -C "$state_dir" add README.md "$database_name"
    if git -C "$state_dir" diff --cached --quiet; then
      echo "No state changes to commit."
      exit 0
    fi

    git -C "$state_dir" commit -m "Update citation radar state [skip ci]" >/dev/null
    git -C "$state_dir" push origin "$state_branch" >/dev/null
    echo "Saved $database_name to $state_branch."
    ;;

  *)
    usage >&2
    exit 2
    ;;
esac
