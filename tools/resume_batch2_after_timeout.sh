#!/bin/bash
# タイムアウト時の自動再開スクリプト（5時間後に generate_batch2_videos.sh を実行）

REPO="/home/user/StudyList"
LOG="${REPO}/tools/generate_batch2_videos.log"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です'}"
WAIT=18000  # 5時間

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== 自動再開待機開始（${WAIT}秒 = 5時間） ==="
sleep "$WAIT"

log "=== 待機終了。動画生成を再開します ==="
GEMINI_API_KEY="$KEY" bash "${REPO}/tools/generate_batch2_videos.sh"
