#!/bin/sh
# 맥에서 실행: 최신 내용 받기 -> 내 변경 올리기
# 사용: sh tools/sync.sh "메모(선택)"
cd "$(dirname "$0")/.." || exit 1
git pull --rebase --autostash || { echo "받기 실패: 충돌을 먼저 해결하세요"; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "${1:-update} / $(hostname | cut -d. -f1) / $(date '+%Y-%m-%d %H:%M')"
fi
git push && echo "동기화 완료"
