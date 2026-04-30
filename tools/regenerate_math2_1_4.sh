#!/bin/bash
# math2-01 と math2-04 のみ再生成（修正後）
REPO="/home/user/StudyList"
REDESIGN="${REPO}/problems/youtube_redesign"
LOG="${REPO}/tools/regenerate_math2_1_4.log"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です'}"

VIDEOS=(
  "math2-01_exponential_substitution"
  "math2-04_derivative_maxmin"
)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
log "=== math2-01 / math2-04 再生成 開始 ==="

for stem in "${VIDEOS[@]}"; do
  log "  生成開始: ${stem}"
  GEMINI_API_KEY="$KEY" python3 "${REPO}/tools/slide_to_video.py" \
    --file "${REDESIGN}/${stem}.html" 2>&1 | tee -a "$LOG"
  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    log "  エラー: ${stem}"
    exit 1
  fi
  log "  完了: ${stem}"
done

log "=== 再生成完了 ==="

cd "$REPO"
git add problems/youtube_redesign/output/math2-01_exponential_substitution.mp4 \
        problems/youtube_redesign/output/math2-04_derivative_maxmin.mp4 \
        problems/youtube_redesign/math2-01_exponential_substitution_edit.md \
        problems/youtube_redesign/math2-04_derivative_maxmin_edit.md
git commit -m "rebuild: math2-01/4 を修正後に再生成

https://claude.ai/code/session_01RKesr7AcWzRxVjkrQ8KsTr"
git push -u origin claude/timeout-recovery-prompt-MerMB
git checkout main
git merge --ff-only claude/timeout-recovery-prompt-MerMB
git push origin main
git checkout claude/timeout-recovery-prompt-MerMB
log "=== コミット・プッシュ・マージ完了 ==="
