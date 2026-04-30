#!/bin/bash
# 数学I 動画再生成スクリプト（タイムアウト自動再開対応）
# 使い方: GEMINI_API_KEY=xxx bash tools/generate_math1_videos.sh

REPO="/home/user/StudyList"
REDESIGN="${REPO}/problems/youtube_redesign"
LOG="${REPO}/tools/generate_math1_videos.log"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です'}"

VIDEOS=(
  "math1-01_quadratic_discriminant"
  "math1-02_quadratic_trap"
  "math1-03_quadratic_axis"
  "math1-04_quadratic_complete"
  "math1-05_absolute_inequality"
)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== 数学I 動画再生成 開始 ==="

for stem in "${VIDEOS[@]}"; do
  marker="${REPO}/tools/.done_${stem}"
  if [ -f "$marker" ]; then
    log "  SKIP: ${stem}（完了済み）"
    continue
  fi

  log "  生成開始: ${stem}"
  GEMINI_API_KEY="$KEY" python3 "${REPO}/tools/slide_to_video.py" \
    --file "${REDESIGN}/${stem}.html" 2>&1 | tee -a "$LOG"

  exit_code=${PIPESTATUS[0]}
  if [ "$exit_code" -eq 0 ]; then
    touch "$marker"
    log "  完了: ${stem}"
  else
    log "  エラー(exit=$exit_code): ${stem} → ログを確認してください"
    exit 1
  fi
done

log "=== 全動画生成完了 ==="

# 完了マーカーを削除
rm -f "${REPO}/tools/.done_math1-"*

# コミット・プッシュ
cd "$REPO"
git add problems/youtube_redesign/output/
git commit -m "rebuild: 数学I動画5本を _edit.md 修正後に再生成

https://claude.ai/code/session_01RKesr7AcWzRxVjkrQ8KsTr"
git push -u origin claude/timeout-recovery-prompt-MerMB

log "=== コミット・プッシュ完了 ==="
