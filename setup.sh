#!/bin/bash
# setup.sh — 에이전트 자동 클론 및 업데이트
# 사용법: ./setup.sh          (전체 클론/업데이트)
#         ./setup.sh update    (업데이트만)
#         ./setup.sh status    (각 에이전트 상태 확인)
#         ./setup.sh link      (로컬 레포 심볼릭 링크 — 개발용)

GITHUB_USER="kipeum86"
AGENTS_DIR="agents"
LOCAL_BASE="$HOME/코딩 프로젝트"

# 법무법인 진주 소속 에이전트 8명 — 오케스트레이터가 실제로 호출하는 대상.
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
    for repo in "${REPOS[@]}"; do
      if [ -d "$AGENTS_DIR/$repo" ] || [ -L "$AGENTS_DIR/$repo" ]; then
        if [ -L "$AGENTS_DIR/$repo" ]; then
          echo "🔗 $repo (symlink → $(readlink "$AGENTS_DIR/$repo"))"
        else
          echo "📥 Updating $repo..."
          (cd "$AGENTS_DIR/$repo" && git pull --rebase)
        fi
      else
        echo "📦 Cloning $repo..."
        git clone "https://github.com/$GITHUB_USER/$repo" "$AGENTS_DIR/$repo"
      fi
    done
    echo "✅ All agents ready."
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
    for repo in "${REPOS[@]}"; do
      if [ -L "$AGENTS_DIR/$repo" ]; then
        echo "🔗 $repo (symlink → $(readlink "$AGENTS_DIR/$repo"))"
      elif [ -d "$AGENTS_DIR/$repo" ]; then
        BRANCH=$(cd "$AGENTS_DIR/$repo" && git branch --show-current)
        COMMIT=$(cd "$AGENTS_DIR/$repo" && git log -1 --format="%h %s" 2>/dev/null)
        echo "✅ $repo ($BRANCH): $COMMIT"
      else
        echo "❌ $repo: not cloned"
      fi
    done
    ;;
esac
