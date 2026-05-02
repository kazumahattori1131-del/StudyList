#!/bin/bash
# mathB-03 動画生成 自動再開スクリプト
# 使い方: GEMINI_API_KEY=xxx bash tools/resume_mathB03.sh

REPO="/home/user/StudyList"
MP4="${REPO}/problems/youtube_redesign/output/mathB-03_recurrence_char.mp4"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です'}"
WAIT=1800  # 30分待機してから再開

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== mathB-03 自動再開スクリプト 待機開始（${WAIT}秒） ==="
sleep "$WAIT"

if [ -f "$MP4" ] && [ "$(stat -c%s "$MP4" 2>/dev/null || stat -f%z "$MP4")" -gt 1000000 ]; then
  log "MP4 既に完成済み（$(du -h "$MP4" | cut -f1)）。コミット・プッシュのみ実行。"
else
  log "MP4 未完成。動画生成を再開します..."
  cd "$REPO" && GOOGLE_API_KEY="$KEY" PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
    python3 tools/slide_to_video.py \
    --file problems/youtube_redesign/mathB-03_recurrence_char.html
fi

log "=== コミット・プッシュ ==="
cd "$REPO"
git add -f problems/youtube_redesign/output/mathB-03_recurrence_char.mp4 2>/dev/null
git add problems/youtube_redesign/mathB-03_recurrence_char_edit.md 2>/dev/null
git diff --staged --quiet || git commit -m "mathB-03 動画生成完了（自動再開）

https://claude.ai/code/session_01NDAV6KmttzK1jEoWGKDVBj"
git push -u origin main
git push origin main:claude/optimize-video-ctr-YCGRC
log "=== 完了 ==="
