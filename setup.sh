#!/bin/bash
# setup.sh — 8명의 하위 에이전트를 항상 최신 main으로 동기화 (shallow clone)
# 사용법: ./setup.sh           (clone 또는 최신 main으로 fast-forward)
#         ./setup.sh update    (alias for default — 모든 에이전트 최신 main 동기화)
#         ./setup.sh link      (개발용: 로컬 레포를 심볼릭 링크로 연결)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

GITHUB_USER="lowtidebuild"
AGENTS_DIR="agents"
LOCAL_BASE="$HOME/코딩 프로젝트"
DEFAULT_BRANCH="main"

# Legal Agent Orchestrator가 호출하는 8명의 하위 에이전트.
# 각 에이전트는 자체 GitHub 리포의 main 브랜치를 따라가며, 항상 최신 버전이 반영됩니다.
REPOS=(
  "general-legal-research"
  "legal-writing-agent"
  "second-review-agent"
  "GDPR-expert"
  "PIPA-expert"
  "game-legal-research"
  "contract-review-agent"
  "legal-translation-agent"
)

mkdir -p "$AGENTS_DIR"

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
    git -C "$target" reset --hard "origin/$DEFAULT_BRANCH"
    echo "⬆️  $repo synced to latest $DEFAULT_BRANCH"
  elif [ -e "$target" ]; then
    echo "⚠️  $target exists but is not a git repo — skipping" >&2
    return 1
  else
    git clone --depth 1 --branch "$DEFAULT_BRANCH" --single-branch "$url" "$target"
    echo "📥 $repo cloned (shallow, $DEFAULT_BRANCH only)"
  fi
}

case "${1:-setup}" in
  setup|update)
    for repo in "${REPOS[@]}"; do
      sync_one "$repo"
    done
    echo "✅ All 8 subordinate agents are at latest $DEFAULT_BRANCH."
    ;;
  link)
    # 로컬 개발용: 기존 레포를 심볼릭 링크로 연결
    for repo in "${REPOS[@]}"; do
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
    echo "Usage: ./setup.sh [setup|update|link]" >&2
    exit 2
    ;;
esac
