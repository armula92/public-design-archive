"""Public Design Archive by armula / 새 사진 수신함 처리

Google Drive `공공디자인 사례 연구/_새 사진` 폴더에 올린 사진을 아카이브에 더합니다.
유형과 캡션은 Claude가 밀착 인화를 보고 정합니다. 전체 순서는 tools/NEW_PHOTOS.md 를 보세요.

  python tools/inbox.py scan    새 사진을 찾아 _work/inbox/ 에 밀착 인화와 pending.json 을 만듭니다.
  python tools/inbox.py apply   _work/inbox/decisions.json 을 반영합니다.
                                사진을 '현장 사진/연-월' 폴더로 옮기고 catalog.json 갱신 후 빌드합니다.
"""
import datetime
import hashlib
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402  같은 폴더의 build.py (HEIC 지원도 여기서 켭니다)

INBOX = '_새 사진'
DONE = '현장 사진'
DUPS = '현장 사진/_중복'
WORK = os.path.join(build.ROOT, '_work', 'inbox')
CATALOG = os.path.join(build.ROOT, 'data', 'catalog.json')
IMAGE_EXT = ('.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.jfif')
IGNORE = ('desktop.ini', 'thumbs.db', '.ds_store')
NEAR = 8  # 이 값 이하의 해시 거리면 이미 있는 사진과 같은 장면일 수 있습니다


def load_catalog():
    with open(CATALOG, encoding='utf-8') as f:
        return json.load(f)


def save_catalog(cat):
    with open(CATALOG, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def known_md5(cat):
    known = {}
    for p in cat['photos']:
        if p.get('md5'):
            known[p['md5']] = p['id']
    for pj in cat['projects']:
        for m in pj['images']:
            if m.get('md5'):
                known[m['md5']] = m['id']
    for h in cat.get('seen_md5', []):
        known.setdefault(h, '(이전 정리에서 제외한 사진)')
    return known


def next_id(cat):
    ids = [p['id'] for p in cat['photos']] + [m['id'] for pj in cat['projects'] for m in pj['images']]
    nums = [int(i[1:]) for i in ids if i.startswith('p') and i[1:].isdigit()]
    return max(nums, default=0) + 1


def taken_date(im, path):
    """촬영일(EXIF)이 없으면 파일 수정일을 씁니다."""
    try:
        ex = im.getexif()
        v = ex.get_ifd(0x8769).get(36867) or ex.get(306)
        if v:
            return datetime.datetime.strptime(str(v).strip()[:19], '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d')
    except Exception:
        pass
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def dhash(im):
    g = im.convert('L').resize((9, 8), Image.LANCZOS)
    px = g.load()
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | int(px[x, y] > px[x + 1, y])
    return bits


def existing_hashes():
    """이미 사이트에 있는 사진(img/t)의 해시. _work/dhash.json 에 저장해 두고 새 것만 계산합니다."""
    cache_path = os.path.join(build.ROOT, '_work', 'dhash.json')
    try:
        with open(cache_path, encoding='utf-8') as f:
            cache = json.load(f)
    except Exception:
        cache = {}
    tdir = os.path.join(build.ROOT, 'img', 't')
    out = {}
    for f in os.listdir(tdir):
        if f.endswith('.jpg'):
            pid = f[:-4]
            if pid not in cache:
                with Image.open(os.path.join(tdir, f)) as im:
                    cache[pid] = dhash(im)
            out[pid] = cache[pid]
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(out, f)
    return out


def label_font(size):
    for f in (r'C:\Windows\Fonts\malgunbd.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Helvetica.ttc', '/Library/Fonts/Arial.ttf'):
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def contact_sheets(items):
    T, COLS, ROWS = 400, 4, 4
    font = label_font(24)
    paths = []
    for k in range(0, len(items), COLS * ROWS):
        chunk = items[k:k + COLS * ROWS]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new('RGB', (COLS * T, rows * (T + 34)), 'white')
        d = ImageDraw.Draw(sheet)
        for j, it in enumerate(chunk):
            x, y = (j % COLS) * T, (j // COLS) * (T + 34)
            with Image.open(os.path.join(WORK, 'thumbs', it['id'] + '.jpg')) as im:
                im = im.copy()
            im.thumbnail((T - 6, T - 6))
            sheet.paste(im, (x + (T - im.width) // 2, y + 34 + (T - im.height) // 2))
            d.rectangle([x, y, x + T - 2, y + 32], fill='black')
            d.text((x + 8, y + 3), f"{it['id']}  {it['date']}", fill='yellow', font=font)
        p = os.path.join(WORK, 'sheet_%02d.jpg' % (k // (COLS * ROWS) + 1))
        sheet.save(p, quality=84)
        paths.append(p)
    return paths


def scan():
    src_root = build.find_source()
    if not src_root:
        sys.exit('Google Drive의 "공공디자인 사례 연구" 폴더를 찾지 못했습니다. PDA_SOURCE 환경변수로 경로를 지정하세요.')
    inbox = os.path.join(src_root, INBOX)
    os.makedirs(inbox, exist_ok=True)
    cat = load_catalog()
    known = known_md5(cat)
    nid = next_id(cat)
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(os.path.join(WORK, 'thumbs'))
    hashes = existing_hashes()

    items, dups, skipped, seen_now = [], [], [], {}
    for root, dirs, files in os.walk(inbox):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        for f in sorted(files):
            if f.lower() in IGNORE or f.startswith(('.', '~$')):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, src_root).replace(os.sep, '/')
            if not f.lower().endswith(IMAGE_EXT):
                skipped.append({'path': rel, 'why': '사진 파일이 아님 (동영상, 문서는 아직 지원하지 않습니다)'})
                continue
            h = md5(path)
            if h in known or h in seen_now:
                dups.append({'path': rel, 'same_as': known.get(h) or seen_now[h]})
                continue
            try:
                with Image.open(path) as raw:
                    date = taken_date(raw, path)
                    im = ImageOps.exif_transpose(raw).convert('RGB')
            except Exception as e:
                heic = f.lower().endswith(('.heic', '.heif'))
                why = 'HEIC 사진은 pillow-heif 가 필요합니다 (python3 -m pip install pillow-heif)' if heic else f'열 수 없음 ({e})'
                skipped.append({'path': rel, 'why': why})
                continue
            pid = 'p%04d' % nid
            nid += 1
            seen_now[h] = pid
            dhs = [dhash(im.rotate(a, expand=True)) for a in (0, 90, 180, 270)]  # 회전 정보가 빠진 사진도 찾도록
            near = sorted(((k, min(bin(d ^ v).count('1') for d in dhs)) for k, v in hashes.items()), key=lambda x: x[1])
            folder = os.path.relpath(root, inbox).replace(os.sep, '/')
            items.append({'id': pid, 'path': rel, 'md5': h, 'w': im.width, 'h': im.height, 'date': date,
                          'folder': '' if folder == '.' else folder, 'filename': os.path.splitext(f)[0],
                          'near': [[k, d] for k, d in near if d <= NEAR][:3]})
            im.thumbnail((720, 720))
            im.save(os.path.join(WORK, 'thumbs', pid + '.jpg'), quality=82)

    sheets = contact_sheets(items)
    with open(os.path.join(WORK, 'pending.json'), 'w', encoding='utf-8') as f:
        json.dump({'source_root': src_root, 'items': items, 'duplicates': dups, 'skipped': skipped}, f, ensure_ascii=False, indent=1)

    print(f'새 사진 {len(items)}장 / 이미 있는 사진 {len(dups)}장 / 건너뜀 {len(skipped)}개')
    for it in items:
        memo = ' / '.join(x for x in (it['folder'], it['filename']) if x)
        near = ', '.join(f'{k}({d})' for k, d in it['near'])
        print(f"  {it['id']}  {it['date']}  {memo}" + (f'  [비슷한 기존 사진: {near}]' if near else ''))
    for dp in dups:
        print(f"  중복: {dp['path']} = {dp['same_as']}")
    for sk in skipped:
        print(f"  건너뜀: {sk['path']} ({sk['why']})")
    if items:
        print('\n밀착 인화:', *sheets, sep='\n  ')
        print(f'\n다음: {os.path.join(WORK, "decisions.json")} 를 쓰고 apply 를 실행하세요.')
        print('형식: [{"id": "p0888", "type": "walk", "caption": "짧은 설명", "quality": 2}, ...]')


def move_into(src_root, src, folder_rel):
    dest_dir = os.path.join(src_root, folder_rel)
    os.makedirs(dest_dir, exist_ok=True)
    stem, ext = os.path.splitext(os.path.basename(src))
    dest, k = os.path.join(dest_dir, stem + ext), 1
    while os.path.exists(dest):
        dest, k = os.path.join(dest_dir, f'{stem}_{k}{ext}'), k + 1
    shutil.move(src, dest)
    return os.path.relpath(dest, src_root).replace(os.sep, '/')


def apply():
    pend_path = os.path.join(WORK, 'pending.json')
    dec_path = os.path.join(WORK, 'decisions.json')
    if not os.path.exists(pend_path):
        sys.exit('먼저 scan 을 실행하세요.')
    if not os.path.exists(dec_path):
        sys.exit(f'{dec_path} 가 없습니다.')
    with open(pend_path, encoding='utf-8') as f:
        pend = json.load(f)
    with open(dec_path, encoding='utf-8') as f:
        decs = {d['id']: d for d in json.load(f)}
    cat = load_catalog()
    valid = {t['key'] for t in cat['types']} | {'exclude', 'skip'}

    errors = []
    for it in pend['items']:
        d = decs.get(it['id'])
        if not d:
            errors.append(f"{it['id']}: 결정이 없습니다")
            continue
        if d.get('type') not in valid:
            errors.append(f"{it['id']}: 알 수 없는 유형 {d.get('type')}")
        cap = d.get('caption', '')
        if '·' in cap:
            errors.append(f"{it['id']}: 캡션에 중간점(·)이 있습니다")
        if d.get('type') not in ('exclude', 'skip') and not cap.strip():
            errors.append(f"{it['id']}: 캡션이 비어 있습니다")
    if errors:
        print('decisions.json 을 고쳐 주세요:', *errors, sep='\n  ')
        sys.exit(1)

    src_root = build.find_source() or pend['source_root']
    known = known_md5(cat)
    today = datetime.date.today().isoformat()
    added, kept = [], 0
    for it in pend['items']:
        d = decs[it['id']]
        if d['type'] == 'skip':
            kept += 1
            continue
        if it['md5'] in known:
            print('  이미 반영된 사진이라 건너뜀:', it['path'])
            continue
        src = build.resolve(src_root, it['path'])
        if not src:
            print('  파일이 없어 건너뜀:', it['path'])
            continue
        if md5(src) != it['md5']:
            print('  scan 이후 바뀐 파일이라 건너뜀:', it['path'])
            continue
        dest = move_into(src_root, src, f"{DONE}/{it['date'][:7]}")
        q = max(1, min(3, int(d.get('quality', 2))))
        cat['photos'].append({'id': it['id'], 'src': dest, 'type': d['type'], 'caption': d.get('caption', '').strip(),
                              'order': 10 * (4 - q), 'md5': it['md5'], 'date': it['date'], 'added': today})
        known[it['md5']] = it['id']
        added.append((it['id'], d['type'], d.get('caption', '').strip()))
    moved_dups = 0
    for dp in pend['duplicates']:
        src = build.resolve(src_root, dp['path'])
        if src:
            move_into(src_root, src, DUPS)
            moved_dups += 1
    save_catalog(cat)
    print()
    build.main([])

    names = {t['key']: t['ko'] for t in cat['types']} | {'exclude': '숨김'}
    shown = [a for a in added if a[1] != 'exclude']
    print(f'\n사이트에 더한 사진 {len(shown)}장 / 숨김 {len(added) - len(shown)}장 / 수신함에 남김 {kept}장 / 중복 정리 {moved_dups}장')
    for pid, t, c in added:
        print(f'  {pid}  {names.get(t, t)}  {c}')
    os.replace(pend_path, os.path.join(WORK, f'applied_{today}_pending.json'))
    os.replace(dec_path, os.path.join(WORK, f'applied_{today}_decisions.json'))
    print('\n다음: sync 스크립트로 GitHub에 올리세요. (맥 sh tools/sync.sh / 윈도우 tools\\sync.ps1)')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'scan':
        scan()
    elif cmd == 'apply':
        apply()
    else:
        print(__doc__)
