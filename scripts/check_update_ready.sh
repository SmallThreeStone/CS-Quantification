#!/usr/bin/env bash
set -euo pipefail

REMOTE="origin"
BRANCH="feature/initial-mvp"
TARGET_COMMIT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --remote)
      REMOTE="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --target-commit)
      TARGET_COMMIT="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FAIL current directory is not a git work tree" >&2
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
LOCAL_HEAD="$(git rev-parse HEAD)"

echo "== update readiness =="
echo "branch=${CURRENT_BRANCH}"
echo "local_head=${LOCAL_HEAD}"
echo "remote=${REMOTE}"
echo "expected_branch=${BRANCH}"

if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  echo "FAIL current branch is ${CURRENT_BRANCH}, expected ${BRANCH}" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "FAIL git working tree is not clean" >&2
  git status --short >&2
  exit 1
fi

git fetch "$REMOTE" "$BRANCH"

REMOTE_HEAD="$(git rev-parse FETCH_HEAD)"
echo "remote_head=${REMOTE_HEAD}"

if [ -n "$TARGET_COMMIT" ]; then
  TARGET_FULL="$(git rev-parse "$TARGET_COMMIT")"
  echo "target_commit=${TARGET_FULL}"
  if [ "$REMOTE_HEAD" != "$TARGET_FULL" ]; then
    echo "FAIL remote ${REMOTE}/${BRANCH} does not match target commit" >&2
    exit 1
  fi
fi

if git merge-base --is-ancestor "$LOCAL_HEAD" "$REMOTE_HEAD"; then
  echo "OK local HEAD can fast-forward to remote"
else
  echo "FAIL local HEAD is not an ancestor of remote; resolve divergence before deploy" >&2
  exit 1
fi

echo "next=git pull --ff-only ${REMOTE} ${BRANCH}"
