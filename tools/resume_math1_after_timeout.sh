#!/bin/bash
# 数学I 動画生成 タイムアウト自動再開スクリプト
# バックグラウンドで起動しておく:
#   GEMINI_API_KEY=xxx bash tools/resume_math1_after_timeout.sh &

REPO="/home/user/StudyList"
LOG="${REPO}/tools/generate_math1_videos.log"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です'}"
WAIT=10800  # 3時間待機

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== 自動再開待機開始（${WAIT}秒 = 3時間） ==="
sleep "$WAIT"

log "=== 待機終了。未完了の動画生成を再開します ==="
GEMINI_API_KEY="$KEY" bash "${REPO}/tools/generate_math1_videos.sh"
