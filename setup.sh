#!/bin/bash
# setup.sh — 에이전트 자동 클론 및 lock commit 동기화
# 사용법: ./setup.sh              (agents.lock 기준 클론/checkout)
#         ./setup.sh update       (agents.lock 기준 재동기화)
#         ./setup.sh update-lock  (현재 ref의 최신 commit으로 agents.lock 갱신)
#         ./setup.sh status       (lock 대비 각 에이전트 상태 확인)
#         ./setup.sh link         (로컬 레포 심볼릭 링크 — 개발용)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

GITHUB_USER="lowtidebuild"
AGENTS_DIR="agents"
LOCAL_BASE="$HOME/코딩 프로젝트"
LOCK_FILE="agents.lock"

# Legal Agent Orchestrator가 관리하는 에이전트 8명 — 오케스트레이터가 실제로 호출하는 대상.
# briefing 계열(game-legal-briefing, game-policy-briefing)은 독립 Python
# 앱이라 이 오케스트레이터가 호출하지 않으므로 클론 대상에서 제외.
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

case "${1:-setup}" in
  setup|update)
    python3 "$ROOT_DIR/scripts/agent-lock.py" sync \
      --lock "$ROOT_DIR/$LOCK_FILE" \
      --agents-dir "$ROOT_DIR/$AGENTS_DIR"
    echo "✅ All agents synced to $LOCK_FILE."
    ;;
  update-lock)
    python3 "$ROOT_DIR/scripts/agent-lock.py" update-lock \
      --lock "$ROOT_DIR/$LOCK_FILE" \
      --agents-dir "$ROOT_DIR/$AGENTS_DIR"
    echo "✅ $LOCK_FILE updated. Review and commit it intentionally."
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
  status)
    python3 "$ROOT_DIR/scripts/agent-lock.py" status \
      --lock "$ROOT_DIR/$LOCK_FILE" \
      --agents-dir "$ROOT_DIR/$AGENTS_DIR"
    ;;
  *)
    echo "Usage: ./setup.sh [setup|update|update-lock|status|link]" >&2
    exit 2
    ;;
esac
