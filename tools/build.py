"""Public Design Archive by armula / 빌드 스크립트

data/catalog.json (사진 목록, 유형, 캡션, 사업, 참고 자료)을 읽어
  1) Google Drive 원본 사진을 웹용으로 줄여 img/w (큰 사진), img/t (썸네일)에 저장하고
  2) 화면이 읽는 data/archive.js 를 다시 씁니다.

이미 만들어진 웹용 사진은 건너뛰므로, 원본이 없는 컴퓨터에서도 캡션만 고쳐서 다시 빌드할 수 있습니다.

사용법
  python tools/build.py            # 새 사진만 변환 + archive.js 생성
  python tools/build.py --force    # 모든 사진 다시 변환
  PDA_SOURCE="/경로/공공디자인 사례 연구" python tools/build.py   # 원본 폴더 직접 지정
"""
import glob
import io
import json
import os
import sys
import unicodedata
import zipfile

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL, THUMB = 1600, 720
FOLDER = '공공디자인 사례 연구'


def find_source():
    env = os.environ.get('PDA_SOURCE')
    if env:
        return env
    cands = []
    if sys.platform == 'win32':
        for d in 'GHIJKLMNOPQRSTUVWXYZDEF':
            cands += [f'{d}:/내 드라이브/{FOLDER}', f'{d}:/My Drive/{FOLDER}']
    home = os.path.expanduser('~')
    for drive in ('내 드라이브', 'My Drive'):
        for name in (FOLDER, unicodedata.normalize('NFD', FOLDER)):
            cands += glob.glob(f'{home}/Library/CloudStorage/GoogleDrive-*/{drive}/{name}')
            cands += glob.glob(f'{home}/Library/CloudStorage/GoogleDrive-*/{unicodedata.normalize("NFD", drive)}/{name}')
    cands += [f'{home}/Google Drive/{FOLDER}', f'{home}/Google Drive/My Drive/{FOLDER}']
    for c in cands:
        if os.path.isdir(c):
            return c
    return None


def resolve(src_root, rel):
    """맥(NFD)과 윈도우(NFC)의 한글 파일명 차이를 흡수해 실제 경로를 찾습니다."""
    for form in ('NFC', 'NFD'):
        p = os.path.join(src_root, unicodedata.normalize(form, rel))
        if os.path.exists(p):
            return p
    cur = src_root
    for part in rel.split('/'):
        if not os.path.isdir(cur):
            return None
        hit = [n for n in os.listdir(cur) if unicodedata.normalize('NFC', n) == unicodedata.normalize('NFC', part)]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur


def open_source(src_root, src):
    if '::' in src:  # zip 안의 파일: "폴더/파일.zip::안쪽이름.jpg"
        zp, name = src.split('::', 1)
        path = resolve(src_root, zp)
        if not path:
            return None
        z = zipfile.ZipFile(path)
        for zi in z.infolist():
            n = zi.filename
            try:
                n = n.encode('cp437').decode('cp949')
            except Exception:
                pass
            if unicodedata.normalize('NFC', n) == unicodedata.normalize('NFC', name):
                return Image.open(io.BytesIO(z.read(zi)))
        return None
    path = resolve(src_root, src) if src_root else None
    if not path and os.path.isabs(src) and os.path.exists(src):
        path = src
    return Image.open(path) if path else None


def save(im, out, size, q):
    im = im.copy()
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(out, 'JPEG', quality=q, optimize=True, progressive=True)


def main():
    force = '--force' in sys.argv
    cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
    src_root = find_source()
    print('원본 폴더:', src_root or '(찾지 못함 / 기존 웹용 사진만 사용)')
    os.makedirs(os.path.join(ROOT, 'img', 'w'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'img', 't'), exist_ok=True)

    jobs = [(p['id'], p['src']) for p in cat['photos'] if p.get('type') != 'exclude']
    for pj in cat['projects']:
        jobs += [(m['id'], m['src']) for m in pj['images']]

    sizes, made, missing = {}, 0, []
    for pid, src in jobs:
        fw = os.path.join(ROOT, 'img', 'w', pid + '.jpg')
        ft = os.path.join(ROOT, 'img', 't', pid + '.jpg')
        have = os.path.exists(fw) and os.path.exists(ft)
        if force or not have:
            im = None
            if not src.startswith('extracted:'):  # PDF, 영상에서 뽑은 사진은 원본 파일이 없습니다
                try:
                    im = open_source(src_root, src)
                except Exception as e:
                    print('  읽기 오류', src, e)
            if im is not None:
                im = ImageOps.exif_transpose(im).convert('RGB')
                save(im, fw, FULL, 80)
                save(im, ft, THUMB, 74)
                made += 1
            elif not have:
                missing.append(src)
                continue
        with Image.open(fw) as im:
            sizes[pid] = im.size

    types = []
    for t in cat['types']:
        ps = [p for p in cat['photos'] if p.get('type') == t['key'] and p['id'] in sizes]
        ps.sort(key=lambda p: (p.get('order', 50), p['id']))
        types.append({**{k: t[k] for k in ('key', 'ko', 'en', 'copy', 'desc')},
                      'photos': [[p['id'], *sizes[p['id']], p.get('caption', '')] for p in ps]})
    types = [t for t in types if t['photos']]
    projects = []
    for pj in cat['projects']:
        imgs = [[m['id'], *sizes[m['id']]] for m in pj['images'] if m['id'] in sizes]
        projects.append({k: pj.get(k, '') for k in ('slug', 'title', 'title_en', 'client', 'place', 'year', 'award', 'copy', 'desc')} | {'images': imgs})
    data = {'span': cat.get('span', ''), 'strip': [i for i in cat.get('strip', []) if i in sizes],
            'types': types, 'projects': projects, 'refs': cat.get('refs', [])}
    with open(os.path.join(ROOT, 'data', 'archive.js'), 'w', encoding='utf-8') as f:
        f.write('/* tools/build.py 가 data/catalog.json 에서 자동 생성합니다. 직접 고치지 마세요. */\n')
        f.write('window.ARCHIVE = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'변환 {made}장 / 전체 {len(sizes)}장 / 유형 {len(types)}개 / 사업 {len(projects)}건')
    if missing:
        print(f'원본을 찾지 못한 사진 {len(missing)}장 (처음 10개):')
        for m in missing[:10]:
            print('  ', m)


if __name__ == '__main__':
    main()
