# Public Design Archive by armula / Ver 1.0

거리에서 모은 공공디자인의 장면을 유형별로 기록하는 아카이브입니다.
이현성 / 홍익대학교 공공디자인전공

- 사이트: https://www.armula.com/public-design-archive/
- 원본 사진: Google Drive `내 드라이브/공공디자인 사례 연구` (저장소에는 웹용으로 줄인 사진만 들어 있습니다)

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 사이트 화면 |
| `assets/` | 스타일(`style.css`)과 화면 스크립트(`app.js`) |
| `data/catalog.json` | **고치는 곳.** 유형 설명, 사진별 유형과 캡션, 사업, 참고 자료 |
| `data/archive.js` | 빌드가 자동으로 만드는 파일 (직접 고치지 않음) |
| `img/w`, `img/t` | 웹용 큰 사진(1600px), 썸네일(720px) |
| `tools/build.py` | catalog.json → 사진 변환 + archive.js 생성 |
| `tools/inbox.py`, `tools/NEW_PHOTOS.md` | 새 사진 수신함 처리와 Claude 작업 순서 |
| `tools/claude-skill/` | Claude Code 스킬 "새 사진 올려 줘" (맥 설정 스크립트가 설치) |
| `tools/sync.sh`, `tools/sync.ps1` | 맥, 윈도우에서 받기와 올리기를 한 번에 |

## 맥과 노트북을 오가며 작업하기

두 컴퓨터 모두 저장소를 **Google Drive 밖**(`~/github/public-design-archive`)에 둡니다.
`.git` 폴더를 Drive 안에 두면 동기화 충돌로 저장소가 깨질 수 있기 때문입니다.
GitHub가 두 컴퓨터 사이의 중심 역할을 합니다.

### 처음 한 번

윈도우 노트북 (이미 설정됨)

```
C:\Users\ARMULA\github\public-design-archive
```

맥 (터미널에 한 줄)

```sh
curl -fsSL https://raw.githubusercontent.com/armula92/public-design-archive/main/tools/setup-mac.sh | sh
```

GitHub 로그인을 묻는다면 `brew install gh && gh auth login` 으로 한 번 로그인합니다.

### 매번 작업할 때

1. 시작 전: 받기
2. 작업: `data/catalog.json` 수정 → `python3 tools/build.py`
3. 끝나면: 올리기

받기와 올리기는 스크립트 하나로 합니다.

```sh
sh tools/sync.sh "캡션 수정"                                        # 맥
powershell -ExecutionPolicy Bypass -File tools\sync.ps1 "캡션 수정"   # 윈도우
```

올린 뒤 1~2분이면 사이트에 반영됩니다.

## 새 사진 올리기

1. 찍은 사진을 Google Drive `공공디자인 사례 연구/_새 사진` 폴더에 넣습니다.
   - 휴대폰: 갤러리에서 사진 선택 → 공유 → Drive → `_새 사진`
   - 맥, 노트북: 폴더에 끌어다 놓기
   - 메모(선택): 하위 폴더 이름(`_새 사진/안전색채/`)이나 파일명(`뉴욕 쓰레기통.jpg`)에 적어 두면 분류와 캡션에 반영됩니다.
2. Claude Code에서 **"새 사진 올려 줘"** 또는 `/new-photos`

나머지는 Claude가 합니다. 중복 확인 → 사진을 보고 유형과 캡션 결정 → 웹용 변환(위치정보 삭제) → 사이트 반영과 GitHub 올리기 → 처리한 사진은 `현장 사진/연-월` 폴더로 이동. 새 사진은 사이트의 **최근 추가**에 먼저 보입니다.
작업 순서는 `tools/NEW_PHOTOS.md`, 처리 스크립트는 `tools/inbox.py` 입니다.

캡션이나 유형을 고칠 때는 "p0890 캡션 고쳐 줘", "p0890 숨겨 줘"처럼 요청하면 됩니다.

### 직접 고치기

`data/catalog.json` 의 `photos` 항목을 고치고 `python3 tools/build.py` 를 실행한 뒤 올립니다.

`type` 값: `walk` 보행과 횡단, `bike` 자전거, `color` 안전색채, `cpted` 범죄예방, `furniture` 공공시설물, `sign` 사인과 정보, `inclusive` 배려와 유니버설, `nudge` 넛지와 행동유도, `play` 놀이와 활력, `street` 가로와 경관, `memory` 기록, `exclude` 숨김

## 디자인 원칙

Noto Sans KR 한 가족, 기본 자간, 박스형 카드 없음, 서수 번호 대신 정사각형 불릿, 중간점 대신 `,` 와 `/`, 통계는 한 줄에 흐린 `I`로 구분, 링크는 마우스를 올렸을 때만 오렌지(#ff6b1a).
