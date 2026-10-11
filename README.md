# Public Design Archive by armula / Ver 1.0

거리에서 모은 공공디자인의 장면을 유형별로 기록하는 아카이브입니다.
이현성 / 홍익대학교 공공디자인전공

- 사이트: https://armula92.github.io/public-design-archive/
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

## 사진 추가하기

1. Drive의 `공공디자인 사례 연구` 폴더에 사진을 넣습니다.
2. `data/catalog.json`의 `photos`에 항목을 추가합니다.

```json
{"id": "p0888", "src": "이미지/새 사진.jpg", "type": "walk", "caption": "짧은 설명"}
```

3. `python3 tools/build.py` 를 실행하고 올립니다.

`type` 값: `walk` 보행과 횡단, `bike` 자전거, `color` 안전색채, `cpted` 범죄예방, `furniture` 공공시설물, `sign` 사인과 정보, `inclusive` 배려와 유니버설, `nudge` 넛지와 행동유도, `play` 놀이와 활력, `street` 가로와 경관, `memory` 기록, `exclude` 숨김

## 디자인 원칙

Noto Sans KR 한 가족, 기본 자간, 박스형 카드 없음, 서수 번호 대신 정사각형 불릿, 중간점 대신 `,` 와 `/`, 통계는 한 줄에 흐린 `I`로 구분, 링크는 마우스를 올렸을 때만 오렌지(#ff6b1a).
