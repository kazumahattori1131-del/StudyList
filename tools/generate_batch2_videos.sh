#!/bin/bash
# 新規6本（第2弾）の動画生成スクリプト（再実行可・生成済みはスキップ）

set -euo pipefail

REPO="/home/user/StudyList"
LOG="${REPO}/tools/generate_batch2_videos.log"
OUTPUT="${REPO}/problems/youtube_redesign/output"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です'}"

STEMS=(
    math1-4_quadratic_complete
    math1-5_absolute_inequality
    math2-6_logarithm_concept
    math2-7_trig_unit_circle
    mathB-6_hypothesis_test
    mathC-4_conic_sections
)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== 動画生成開始（第2弾） ==="
cd "$REPO"

GENERATED=0
for stem in "${STEMS[@]}"; do
    html="problems/youtube_redesign/${stem}.html"
    mp4="${OUTPUT}/${stem}.mp4"

    if [ ! -f "$html" ]; then
        log "スキップ（HTMLなし）: $stem"
        continue
    fi
    if [ -f "$mp4" ]; then
        log "スキップ（生成済み）: $stem"
        continue
    fi

    log "生成開始: $stem"
    if GEMINI_API_KEY="$KEY" PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
        python3 tools/slide_to_video.py \
        --file "$html" \
        >> "$LOG" 2>&1; then
        log "生成成功: $stem"
        GENERATED=$((GENERATED + 1))
    else
        log "生成失敗: $stem（スキップして続行）"
    fi
done

log "生成完了: ${GENERATED}本"

if [ "$GENERATED" -gt 0 ]; then
    log "コミット・プッシュ中..."
    git checkout claude/math-problem-analysis-Hngj1
    for stem in "${STEMS[@]}"; do
        mp4="${OUTPUT}/${stem}.mp4"
        [ -f "$mp4" ] && git add -f "$mp4"
    done
    git commit -m "chore: 新規6本（第2弾）の動画を生成・追加

https://claude.ai/code/session_01AEJUFz7TMqmGFXqNWKccKA" || true
    git push -u origin claude/math-problem-analysis-Hngj1
    log "プッシュ完了"
fi

log "=== 全工程終了 ==="
