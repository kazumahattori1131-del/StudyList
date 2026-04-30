#!/bin/bash
# 明日 09:00 JST に math2-10 → math2-01 → math2-04 の順で動画生成
# CTR最適化アップデート適用済みバージョン（2026-04-29 作成）
# 使い方: GEMINI_API_KEY=xxx nohup bash tools/generate_apr30_ctr.sh &

REPO="/home/user/StudyList"
BRANCH="claude/optimize-video-ctr-YCGRC"
LOG="${REPO}/tools/generate_apr30_ctr.log"
KEY_FILE="${HOME}/.gemini_api_key"

log() {
  echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG"
}

# APIキー読み込み（環境変数優先、なければファイル）
KEY="${GEMINI_API_KEY:-}"
if [ -z "$KEY" ] && [ -f "$KEY_FILE" ]; then
  KEY="$(cat "$KEY_FILE")"
fi
if [ -z "$KEY" ]; then
  log "エラー: GEMINI_API_KEY 環境変数も ~/.gemini_api_key も見つかりません"
  log "起動方法: GEMINI_API_KEY=xxx nohup bash tools/generate_apr30_ctr.sh &"
  exit 1
fi

# 09:00 JST まで待機
TARGET_EPOCH=$(TZ=Asia/Tokyo date -d 'tomorrow 09:00:00' +%s)
NOW_EPOCH=$(date +%s)
WAIT_SEC=$((TARGET_EPOCH - NOW_EPOCH))

log "=== generate_apr30_ctr.sh 起動 ==="
log "待機開始: ${WAIT_SEC}秒後（明日 09:00 JST）に生成開始"
log "生成順序: math2-10 → math2-01 → math2-04"
sleep "$WAIT_SEC"
log "=== 待機完了。生成開始 ==="

cd "$REPO" || exit 1
git checkout "$BRANCH" 2>&1 | tee -a "$LOG"

# 生成対象（CTRアップデート適用済み・順番固定）
STEMS=(
  "math2-10_log_inequality"
  "math2-01_exponential_substitution"
  "math2-04_derivative_maxmin"
)

for stem in "${STEMS[@]}"; do
  html="${REPO}/problems/youtube_redesign/${stem}.html"
  log "--- 生成開始: ${stem} ---"
  GEMINI_API_KEY="$KEY" python3 "${REPO}/tools/slide_to_video.py" \
    --file "$html" 2>&1 | tee -a "$LOG"
  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    log "エラー: ${stem} — 中断します"
    exit 1
  fi
  log "--- 完了: ${stem} ---"
done

log "=== 全生成完了。コミット・プッシュ開始 ==="

git add \
  problems/youtube_redesign/math2-10_log_inequality_edit.md \
  problems/youtube_redesign/math2-01_exponential_substitution_edit.md \
  problems/youtube_redesign/math2-04_derivative_maxmin_edit.md \
  tools/api_usage_log.jsonl \
  tools/generate_apr30_ctr.log

git commit -m "rebuild: CTR最適化版 math2-10/1/4 を生成（APR30 09:00 JST）

生成順序: math2-10（対数不等式） → math2-01（指数方程式） → math2-04（微分最大最小）
3戦略アップデート適用: サムネイル連動・京大生視点・挨拶排除

https://claude.ai/code/session_01NDAV6KmttzK1jEoWGKDVBj"

git push -u origin "$BRANCH"

# main へマージ
git checkout main
git merge --ff-only "$BRANCH"
git push origin main
git checkout "$BRANCH"

log "=== コミット・プッシュ・maへのマージ完了 ==="
