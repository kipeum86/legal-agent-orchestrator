#!/bin/bash
# setup.sh — 4명의 하위 에이전트를 항상 최신 main으로 동기화 (shallow clone)
# 사용법: ./setup.sh                         (clone 또는 최신 main으로 fast-forward)
#         ./setup.sh update [agent-id ...]    (선택 에이전트만 최신 main 동기화)
#         ./setup.sh status [agent-id ...]    (선택 에이전트의 로컬 SHA vs 원격 main 비교)
#         ./setup.sh link [agent-id ...]      (개발용: 로컬 레포를 심볼릭 링크로 연결)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

GITHUB_USER="lowtidebuild"
AGENTS_DIR="agents"
LOCAL_BASE="$HOME/코딩 프로젝트"
DEFAULT_BRANCH="main"

# Legal Agent Orchestrator가 호출하는 4명의 하위 에이전트.
# 각 에이전트는 자체 GitHub 리포의 main 브랜치를 따라가며, 항상 최신 버전이 반영됩니다.
REPOS=(
  "legal-research-agent"
  "legal-writing-agent"
  "second-review-agent"
  "data-protection-agent"
)

usage() {
  echo "Usage: ./setup.sh [setup|update|status|link] [agent-id ...]" >&2
  echo "Known agent ids: ${REPOS[*]}" >&2
}

is_known_repo() {
  local candidate="$1"
  local repo
  for repo in "${REPOS[@]}"; do
    if [ "$candidate" = "$repo" ]; then
      return 0
    fi
  done
  return 1
}

select_targets() {
  TARGET_REPOS=()
  if [ "$#" -eq 0 ]; then
    TARGET_REPOS=("${REPOS[@]}")
    return
  fi

  local repo
  for repo in "$@"; do
    if ! is_known_repo "$repo"; then
      echo "Unknown agent id: $repo" >&2
      usage
      exit 2
    fi
    TARGET_REPOS+=("$repo")
  done
}

sync_complete_message() {
  if [ "${#TARGET_REPOS[@]}" -eq "${#REPOS[@]}" ]; then
    echo "✅ All 4 subordinate agents are at latest $DEFAULT_BRANCH."
  else
    echo "✅ Selected subordinate agents are at latest $DEFAULT_BRANCH: ${TARGET_REPOS[*]}"
  fi
}

sync_one() {
  local repo="$1"
  local target="$AGENTS_DIR/$repo"
  local url="https://github.com/$GITHUB_USER/$repo.git"

  if [ -L "$target" ]; then
    echo "🔗 $repo (symlink, skipped)"
    return
  fi

  if [ -d "$target/.git" ]; then
    git -C "$target" fetch --depth 1 origin "$DEFAULT_BRANCH"
    local local_sha
    local_sha=$(git -C "$target" rev-parse HEAD)
    local remote_sha
    remote_sha=$(git -C "$target" rev-parse "origin/$DEFAULT_BRANCH")
    local dirty
    dirty=$(git -C "$target" status --porcelain --untracked-files=no)

    if [ "$local_sha" = "$remote_sha" ] && [ -z "$dirty" ]; then
      echo "✅ $repo already at latest $DEFAULT_BRANCH"
    else
      git -C "$target" reset --hard "origin/$DEFAULT_BRANCH"
      echo "⬆️  $repo synced to latest $DEFAULT_BRANCH"
    fi
  elif [ -e "$target" ]; then
    echo "⚠️  $target exists but is not a git repo — skipping" >&2
    return 1
  else
    git clone --depth 1 --branch "$DEFAULT_BRANCH" --single-branch "$url" "$target"
    echo "📥 $repo cloned (shallow, $DEFAULT_BRANCH only)"
  fi
}

status_one() {
  local repo="$1"
  local target="$AGENTS_DIR/$repo"
  local url="https://github.com/$GITHUB_USER/$repo.git"

  if [ -L "$target" ]; then
    printf "%-26s %s\n" "$repo" "🔗 symlink (dev mode)"
    return
  fi
  if [ ! -d "$target/.git" ]; then
    printf "%-26s %s\n" "$repo" "⛔ not installed"
    return
  fi

  local local_sha
  local_sha=$(git -C "$target" rev-parse HEAD 2>/dev/null || echo "")
  local remote_sha
  remote_sha=$(git ls-remote "$url" "refs/heads/$DEFAULT_BRANCH" 2>/dev/null | awk '{print $1}')

  if [ -z "$remote_sha" ]; then
    printf "%-26s %s\n" "$repo" "❓ unreachable (local: ${local_sha:0:12})"
    return
  fi

  if [ "$local_sha" = "$remote_sha" ]; then
    printf "%-26s %s\n" "$repo" "✅ up to date (${local_sha:0:12})"
  else
    printf "%-26s %s\n" "$repo" "⚠️  behind  local: ${local_sha:0:12}  →  remote: ${remote_sha:0:12}"
  fi
}

COMMAND="${1:-setup}"
if [ "$#" -gt 0 ]; then
  shift
fi

case "$COMMAND" in
  setup|update)
    select_targets "$@"
    mkdir -p "$AGENTS_DIR"
    for repo in "${TARGET_REPOS[@]}"; do
      sync_one "$repo"
    done
    sync_complete_message
    ;;
  status)
    select_targets "$@"
    echo "📊 Subordinate agent status (local vs origin/$DEFAULT_BRANCH):"
    for repo in "${TARGET_REPOS[@]}"; do
      status_one "$repo"
    done
    ;;
  link)
    select_targets "$@"
    mkdir -p "$AGENTS_DIR"
    # 로컬 개발용: 기존 레포를 심볼릭 링크로 연결
    for repo in "${TARGET_REPOS[@]}"; do
      if [ -d "$LOCAL_BASE/$repo" ]; then
        if [ -e "$AGENTS_DIR/$repo" ]; then
          echo "⏭️  $repo already exists, skipping"
        else
          ln -s "$LOCAL_BASE/$repo" "$AGENTS_DIR/$repo"
          echo "🔗 Linked $repo → $LOCAL_BASE/$repo"
        fi
      else
        echo "⚠️  $repo not found at $LOCAL_BASE/$repo"
      fi
    done
    echo "✅ Done linking."
    ;;
  *)
    usage
    exit 2
    ;;
esac
