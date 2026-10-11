#!/bin/sh
# 맥 처음 설정 (한 번만, 다시 실행해도 안전): 터미널에서
#   curl -fsSL https://raw.githubusercontent.com/armula92/public-design-archive/main/tools/setup-mac.sh | sh
set -e
command -v git >/dev/null || { echo "git이 없습니다. 'xcode-select --install' 후 다시 실행하세요."; exit 1; }
mkdir -p "$HOME/github"
cd "$HOME/github"
if [ -d public-design-archive/.git ]; then
  cd public-design-archive && git pull --rebase
else
  git clone https://github.com/armula92/public-design-archive.git
  cd public-design-archive
fi
git config core.precomposeunicode true
git config core.quotepath false
git config pull.rebase true

# 사진 변환 도구 (Pillow) 와 아이폰 HEIC 사진 지원 (pillow-heif)
pipi() { python3 -m pip install --user --quiet "$@" 2>/dev/null || python3 -m pip install --user --quiet --break-system-packages "$@"; }
python3 -c "import PIL" 2>/dev/null || pipi Pillow
python3 -c "import pillow_heif" 2>/dev/null || pipi pillow-heif || echo "pillow-heif 설치 실패: HEIC 사진만 처리되지 않습니다"

# Claude Code 스킬: "새 사진 올려 줘" 또는 /new-photos
mkdir -p "$HOME/.claude/skills/new-photos"
cp tools/claude-skill/new-photos/SKILL.md "$HOME/.claude/skills/new-photos/SKILL.md"

echo ""
echo "준비 완료: $HOME/github/public-design-archive"
echo "VS Code로 열기: code $HOME/github/public-design-archive"
echo "새 사진: Drive '공공디자인 사례 연구/_새 사진' 에 넣고 Claude Code에서 '새 사진 올려 줘'"
