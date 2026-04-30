#!/bin/bash
# 明日 9:00 JST にクォータリセット後、math2-01 / math2-04 を生成して main へマージ
REPO="/home/user/StudyList"
LOG="${REPO}/tools/resume_apr30.log"
KEY_FILE="${HOME}/.gemini_api_key"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST' --date='TZ="Asia/Tokyo"')] $*" | tee -a "$LOG"; }

# APIキー読み込み
if [ ! -f "$KEY_FILE" ]; then
  log "エラー: ~/.gemini_api_key が見つかりません"
  exit 1
fi
KEY="$(cat "$KEY_FILE")"

# 9:00 JST まで待機
TARGET_EPOCH=$(TZ=Asia/Tokyo date -d 'tomorrow 09:00:00' +%s)
NOW_EPOCH=$(date +%s)
WAIT_SEC=$((TARGET_EPOCH - NOW_EPOCH))

log "=== resume_apr30.sh 起動 ==="
log "待機開始: ${WAIT_SEC}秒後（明日 09:00 JST）に生成開始"
sleep "$WAIT_SEC"
log "=== 待機完了。生成開始 ==="

cd "$REPO" || exit 1

for stem in math2-01_exponential_substitution math2-04_derivative_maxmin; do
  html="${REPO}/problems/youtube_redesign/${stem}.html"
  log "  生成開始: ${stem}"
  GEMINI_API_KEY="$KEY" python3 "${REPO}/tools/slide_to_video.py" \
    --file "$html" 2>&1 | tee -a "$LOG"
  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    log "  エラー: ${stem} — 中断します"
    exit 1
  fi
  log "  完了: ${stem}"
done

log "=== 全生成完了。コミット・プッシュ開始 ==="

git add problems/youtube_redesign/math2-01_exponential_substitution_edit.md \
        problems/youtube_redesign/math2-04_derivative_maxmin_edit.md \
        tools/api_usage_log.jsonl \
        tools/resume_apr30.log
git commit -m "rebuild: math2-01/4 を修正後に再生成（APR30）

https://claude.ai/code/session_01RKesr7AcWzRxVjkrQ8KsTr"

git push -u origin claude/timeout-recovery-prompt-MerMB

# main へマージ
git checkout main
git merge --ff-only claude/timeout-recovery-prompt-MerMB
git push origin main
git checkout claude/timeout-recovery-prompt-MerMB

log "=== コミット・プッシュ・マージ完了 ==="
