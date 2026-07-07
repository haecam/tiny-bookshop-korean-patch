"""
Mac 배포용 zip 빌드 스크립트

1. 게임 경로에서 번들 파일을 스테이징 폴더로 복사
2. 스테이징 폴더에서 번역 주입
3. release/mac/ 에 zip 파일 생성

배포 zip 안에 들어가는 파일:
  StandaloneOSX/
    tmp_assets_all_*.bundle      (폰트 SDF 포함)
    loca_pl_assets_all.bundle    (한국어 번역 포함)
    loca_en_assets_all.bundle    (언어 표시명 '한국어' 포함)
    yarn_assets_all.bundle       (한국어 대사 포함)
    gameinit_assets_all.bundle   (언어 목록에 PL 추가)

사용자는 zip을 풀어서 StandaloneOSX/ 폴더 안 파일들을
자신의 게임 경로에 복사하면 됩니다.
"""
import UnityPy, warnings, json, os, glob, sys, shutil, zipfile, ast, subprocess

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
PROJ_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANS_DIR = os.path.join(PROJ_DIR, 'translation')

GAME_DIR = os.path.expanduser(
    '~/Library/Application Support/Steam/steamapps/common/'
    'Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/'
    'StreamingAssets/aa/StandaloneOSX'
)

STAGING_DIR = os.path.join(PROJ_DIR, 'release', 'mac', '_staging', 'StandaloneOSX')
RELEASE_DIR = os.path.join(PROJ_DIR, 'release', 'mac')
ZIP_NAME    = 'TinyBookshop_한국어패치_mac_v0.1.zip'

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(RELEASE_DIR, exist_ok=True)

# ── path_ids ──────────────────────────────────────────────────────────────────
TEXTS_PL_PID   = 6208505299439420760   # Loca_Base Texts PL
YARN_ENGB_PID  = -3371373143731600161  # en-GB (yarn_assets_all)
LOCA_INFO_PID  = -7696966092034010949  # LocalizationInfo (gameinit)
LOCA_EN_TEXTS_PID = 6208505299439420760  # Loca_Base Texts EN (loca_en에서 재사용, 같은 pid)

# ── 1. 게임 번들 → 스테이징 복사 ─────────────────────────────────────────────
print('=== 1단계: 번들 파일 스테이징 복사 ===')

tmp_bundles = sorted(glob.glob(os.path.join(GAME_DIR, 'tmp_assets_all_*.bundle')))
if not tmp_bundles:
    print(f'ERROR: tmp_assets_all_*.bundle 파일을 찾을 수 없습니다.\n  경로: {GAME_DIR}')
    sys.exit(1)
TMP_BUNDLE_NAME = os.path.basename(tmp_bundles[0])

for fname in [TMP_BUNDLE_NAME, 'loca_pl_assets_all.bundle', 'loca_en_assets_all.bundle', 'yarn_assets_all.bundle', 'gameinit_assets_all.bundle']:
    src = os.path.join(GAME_DIR, fname)
    # yarn은 백업(원본 영어)이 있으면 우선 사용
    if fname == 'yarn_assets_all.bundle':
        backup_src = src + '.backup'
        if os.path.exists(backup_src):
            src = backup_src
            print(f'  복사: {fname} (백업에서 복원)')
        else:
            print(f'  복사: {fname}')
    else:
        print(f'  복사: {fname}')
    dst = os.path.join(STAGING_DIR, fname)
    if not os.path.exists(src):
        print(f'ERROR: 게임 파일 없음: {src}')
        sys.exit(1)
    shutil.copy2(src, dst)

TMP_BUNDLE      = os.path.join(STAGING_DIR, TMP_BUNDLE_NAME)
EN_BUNDLE       = os.path.join(STAGING_DIR, 'loca_en_assets_all.bundle')
EN_BACKUP       = os.path.join(STAGING_DIR, 'loca_en_assets_all.bundle.backup')
PL_BUNDLE       = os.path.join(STAGING_DIR, 'loca_pl_assets_all.bundle')
YARN_BUNDLE     = os.path.join(STAGING_DIR, 'yarn_assets_all.bundle')
GAMEINIT_BUNDLE = os.path.join(STAGING_DIR, 'gameinit_assets_all.bundle')

shutil.copy2(EN_BUNDLE, EN_BACKUP)  # inject_pl_bundle이 필요로 하는 백업

# ── 1b. 폰트 베이킹 (스테이징 번들에 직접 적용) ──────────────────────────────
print('\n=== 1b단계: 폰트 SDF 베이킹 ===')
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
bake_scripts = [
    ('bake_ridibatang_mac.py',    'RIDIBatang → NotoSansJP-Light'),
    ('bake_bookkmyungjo_mac.py',  'BookkMyungjo → NotoSansJP-Light/SC-SemiBold'),
    ('bake_itim_schoolbell_mac.py','memoment/KCC → NotoSansJP-SemiBold/SC-Light'),
]
for script_name, label in bake_scripts:
    print(f'\n  [{label}]')
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, script_name), TMP_BUNDLE],
        capture_output=False,
    )
    if result.returncode != 0:
        print(f'  ERROR: {script_name} 실패 (returncode={result.returncode})')
        sys.exit(1)

# ── 2. inject_pl_bundle: EN → PL + 한국어 책 제목 ────────────────────────────
print('\n=== 2단계: PL 번들 생성 (책 제목 주입) ===')

with open(os.path.join(TRANS_DIR, 'to_translate_books_ko.json'), encoding='utf-8') as f:
    ko_books = json.load(f)
print(f'  책 번역: {len(ko_books)}개')

shutil.copy2(EN_BACKUP, PL_BUNDLE)

env = UnityPy.load(PL_BUNDLE)
stats = {'tables': 0, 'name_changed': 0, 'lang_changed': 0, 'books_injected': 0}

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    raw = obj.read_typetree()
    changed = False

    if raw.get('LanguageID') == 'EN':
        raw['LanguageID'] = 'PL'
        stats['lang_changed'] += 1
        changed = True

    name = raw.get('m_Name', '')
    if name.endswith(' EN'):
        raw['m_Name'] = name[:-3] + ' PL'
        stats['name_changed'] += 1
        changed = True
    elif ' EN ' in name:
        raw['m_Name'] = name.replace(' EN ', ' PL ')
        stats['name_changed'] += 1
        changed = True

    if 'Base Books' in name and 'dictionary' in raw:
        dic = raw['dictionary']
        keys = dic.get('keyData', [])
        values = dic.get('valueData', [])
        new_values = []
        for k, v in zip(keys, values):
            if k in ko_books and ko_books[k]:
                if isinstance(v, dict) and 'strings' in v and v['strings']:
                    v = dict(v)
                    v['strings'] = list(v['strings'])
                    v['strings'][0] = ko_books[k]
                    stats['books_injected'] += 1
            new_values.append(v)
        dic['valueData'] = new_values
        changed = True

    if changed:
        obj.save_typetree(raw)
        stats['tables'] += 1

with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())

shutil.copy2(EN_BACKUP, EN_BUNDLE)  # EN 복원

print(f'  책 제목 주입: {stats["books_injected"]}개')

# ── 3. inject_pl_main: UI 텍스트 주입 ────────────────────────────────────────
print('\n=== 3단계: UI 텍스트 주입 ===')

with open(os.path.join(TRANS_DIR, 'to_translate_main_ko.json'), encoding='utf-8') as f:
    raw_data = json.load(f)

new_translations = {}
for table_name, val in raw_data.items():
    parsed = ast.literal_eval(val) if isinstance(val, str) else val
    for k, v in parsed.items():
        if isinstance(v, str):
            new_translations[k] = {'strings': [v]}
        elif isinstance(v, dict):
            new_translations[k] = v
        else:
            new_translations[k] = {'strings': [str(v)]}
print(f'  UI 번역: {len(new_translations)}개')

env = UnityPy.load(PL_BUNDLE)
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == TEXTS_PL_PID:
        raw = obj.read_typetree()
        existing_keys = raw['dictionary']['keyData']
        existing_vals = raw['dictionary']['valueData']
        merged_keys = list(existing_keys)
        merged_vals = list(existing_vals)
        added = 0
        for k, v in new_translations.items():
            if k not in set(existing_keys):
                merged_keys.append(k)
                merged_vals.append(v)
                added += 1
        raw['dictionary']['keyData'] = merged_keys
        raw['dictionary']['valueData'] = merged_vals
        obj.save_typetree(raw)
        print(f'  UI 텍스트 추가: {added}개 (총 {len(merged_keys)}개)')
        break

with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())

# ── 4. inject_yarn: 한국어 대사 주입 ─────────────────────────────────────────
print('\n=== 4단계: 대사 주입 ===')

def extract_text(val):
    if isinstance(val, dict):
        return val.get('text', '')
    return str(val)

ko_lines = {}
base_path = os.path.join(TRANS_DIR, 'to_translate_dialogue_ko.json')
if os.path.exists(base_path):
    for k, v in json.load(open(base_path, encoding='utf-8')).items():
        t = extract_text(v)
        if t: ko_lines[k] = t

char_dir = os.path.join(TRANS_DIR, 'characters')
for path in sorted(glob.glob(os.path.join(char_dir, '*.json'))):
    for k, v in json.load(open(path, encoding='utf-8')).items():
        t = extract_text(v)
        if t: ko_lines[k] = t

news_path = os.path.join(TRANS_DIR, 'newspaper_articles_ko.json')
if os.path.exists(news_path):
    for k, v in json.load(open(news_path, encoding='utf-8')).items():
        t = extract_text(v)
        if t: ko_lines[k] = t

print(f'  한국어 대사: {len(ko_lines)}개')

def is_expression_tag(en_value):
    """캐릭터 표정 태그인지 판별 ('Anne: happy' 같은 단일 단어 태그)"""
    text = en_value.split(': ', 1)[-1].strip() if ': ' in en_value else en_value.strip()
    # 공백 없고 문장부호 없는 단일 단어 → 표정 태그
    return ' ' not in text and not any(c in text for c in '.!?,;\'\"')

env = UnityPy.load(YARN_BUNDLE)
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_ENGB_PID:
        raw = obj.read_typetree()
        st = raw['_stringTable']
        keys = st['keys']
        vals = st['values']
        new_vals = []
        applied = 0
        skipped_tag = 0
        for k, v in zip(keys, vals):
            if k in ko_lines and ko_lines[k] and not is_expression_tag(v):
                new_vals.append(ko_lines[k])
                applied += 1
            else:
                if k in ko_lines and ko_lines[k]:
                    skipped_tag += 1
                new_vals.append(v)
        st['values'] = new_vals
        raw['_stringTable'] = st
        obj.save_typetree(raw)
        print(f'  대사 적용: {applied}/{len(keys)}개 (표정 태그 보존: {skipped_tag}개)')
        break

with open(YARN_BUNDLE, 'wb') as f:
    f.write(env.file.save())

# ── 5. gameinit: 언어 목록에 PL 추가 ────────────────────────────────────────
print('\n=== 5단계: 언어 목록에 PL(한국어) 추가 ===')

env = UnityPy.load(GAMEINIT_BUNDLE)
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == LOCA_INFO_PID:
        raw = obj.read_typetree()
        langs = raw.get('availableLanguages', [])
        if any(l['LanguageID'] == 'PL' for l in langs):
            print('  PL 이미 존재')
        else:
            pl_entry = {
                'LanguageID': 'PL',
                'additionalLanguageAliases': ['ko', 'ko-KR', 'Korean', 'KO', 'pl', 'pl-PL', 'Polish', 'POLISH'],
                'cultureInfoID': 'ko-KR',
                'LanguageName': {'key': 'Language_PL'},
                'enabled': 1,
                'forceDisableOnSwitch': 0,
                'percentSign': '',
                'charSpeedMultiplier': 1.0
            }
            langs.append(pl_entry)
            raw['availableLanguages'] = langs
            obj.save_typetree(raw)
            print(f'  PL 추가 완료 (총 {len(langs)}개 언어)')
        break

with open(GAMEINIT_BUNDLE, 'wb') as f:
    f.write(env.file.save())

# ── 6. loca_en: Language_PL 표시명 '한국어'로 변경 ───────────────────────────
print('\n=== 6단계: 언어 표시명 Polski → 한국어 ===')

env = UnityPy.load(EN_BUNDLE)
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        dic = raw.get('dictionary', {})
        keys = dic.get('keyData', [])
        if 'Language_PL' in keys:
            vals = dic.get('valueData', [])
            idx = keys.index('Language_PL')
            vals[idx] = {'strings': ['한국어']}
            dic['valueData'] = vals
            raw['dictionary'] = dic
            obj.save_typetree(raw)
            print(f'  Language_PL → 한국어 변경 완료 ({raw["m_Name"]})')
            break

with open(EN_BUNDLE, 'wb') as f:
    f.write(env.file.save())

# ── 7. 불필요한 파일 정리 후 zip 생성 ────────────────────────────────────────
print('\n=== 7단계: zip 패키징 ===')

os.remove(EN_BACKUP)

zip_path = os.path.join(RELEASE_DIR, ZIP_NAME)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fname in os.listdir(STAGING_DIR):
        fpath = os.path.join(STAGING_DIR, fname)
        arcname = os.path.join('StandaloneOSX', fname)
        zf.write(fpath, arcname)
        size_mb = os.path.getsize(fpath) / 1024 / 1024
        print(f'  추가: {fname} ({size_mb:.1f} MB)')

zip_size = os.path.getsize(zip_path) / 1024 / 1024
print(f'\nzip 생성 완료: release/mac/{ZIP_NAME} ({zip_size:.1f} MB)')

# ── 8. 스테이징 정리 ─────────────────────────────────────────────────────────
shutil.rmtree(os.path.join(PROJ_DIR, 'release', 'mac', '_staging'))
print('스테이징 폴더 정리 완료')
print('\n=== 빌드 완료 ===')
print(f'배포 파일: release/mac/{ZIP_NAME}')
print('사용자 설치 경로:')
print('  ~/Library/Application Support/Steam/steamapps/common/')
print('  Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/')
print('  StreamingAssets/aa/StandaloneOSX/')
