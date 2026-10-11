#!/bin/sh
# 맥 처음 설정 (한 번만): 터미널에서
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
python3 -c "import PIL" 2>/dev/null || python3 -m pip install --user Pillow
echo ""
echo "준비 완료: $HOME/github/public-design-archive"
echo "VS Code로 열기: code $HOME/github/public-design-archive"
