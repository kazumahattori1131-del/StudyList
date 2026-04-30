#!/bin/bash
# mathB-04 動画再生成スクリプト（クォータリセット後に実行）
set -e

LOG="/home/user/StudyList/tools/regenerate_mathB4.log"
REPO="/home/user/StudyList"
KEY="${GEMINI_API_KEY:?'GEMINI_API_KEY が未設定です。export GEMINI_API_KEY=your_key を実行してください'}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] スリープ開始（73800秒 = 約20.5時間）" | tee -a "$LOG"
sleep 73800

echo "[$(date '+%Y-%m-%d %H:%M:%S')] スリープ終了。クォータ確認中..." | tee -a "$LOG"

# クォータ確認（最大3回リトライ）
for attempt in 1 2 3; do
    STATUS=$(python3 -c "
import os
from google import genai
from google.genai import types as genai_types
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
try:
    resp = client.models.generate_content(
        model='gemini-2.5-flash-preview-tts',
        contents='テスト。これはクォータ確認です。',
        config=genai_types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=genai_types.SpeechConfig(
                voice_config=genai_types.VoiceConfig(
                    prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(voice_name='Leda')
                )
            )
        )
    )
    print('OK')
except Exception as e:
    print('NG:' + str(e)[:100])
" 2>&1)

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] クォータ確認 attempt $attempt: $STATUS" | tee -a "$LOG"

    if echo "$STATUS" | grep -q "^OK"; then
        break
    elif [ "$attempt" -lt 3 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] まだリセットされていません。3600秒後に再確認..." | tee -a "$LOG"
        sleep 3600
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] クォータ確認失敗。中断します。" | tee -a "$LOG"
        exit 1
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 動画生成開始..." | tee -a "$LOG"
cd "$REPO"
GEMINI_API_KEY="$KEY" PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
    python3 tools/slide_to_video.py \
    --file problems/youtube_redesign/mathB-04_sum_arithmetic_geometric.html \
    >> "$LOG" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 動画生成成功。コミット・プッシュ中..." | tee -a "$LOG"
    git checkout claude/math-problem-analysis-Hngj1
    git add -f problems/youtube_redesign/output/mathB-04_sum_arithmetic_geometric.mp4
    git commit -m "chore: mathB-04 動画を修正内容で再生成（クォータリセット後）

https://claude.ai/code/session_01AEJUFz7TMqmGFXqNWKccKA"
    git push -u origin claude/math-problem-analysis-Hngj1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完了！" | tee -a "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 動画生成失敗。ログを確認してください: $LOG" | tee -a "$LOG"
    exit 1
fi
