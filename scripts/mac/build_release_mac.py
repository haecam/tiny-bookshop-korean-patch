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
import UnityPy, warnings, json, os, glob, sys, shutil, zipfile, ast, subprocess, copy

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
# Mac: loca_en 복사 불가 - 내부 CAB 파일 ID가 동일해 Unity가 "same files already loaded" 충돌 발생
# 원본 loca_pl을 직접 수정해야 함. 책 제목은 EN fallback 사용 (loca_pl에 책 데이터 없음)
TEXTS_PL_PID  = 4698197123910342691   # Loca_Base Texts PL (원본 loca_pl의 실제 PID)
YARN_PL_PID   = -4050940925882462320  # Loca_Demo Yarn PL (loca_pl 내부, Windows 방식과 동일)
YARN_ENGB_PID = -3371373143731600161  # en-GB 기준값 소스 (yarn_assets_all, 수정 안 함)
LOCA_INFO_PID = -7696966092034010949  # LocalizationInfo (gameinit)

# ── 1. 게임 번들 → 스테이징 복사 ─────────────────────────────────────────────
print('=== 1단계: 번들 파일 스테이징 복사 ===')

tmp_bundles = sorted(glob.glob(os.path.join(GAME_DIR, 'tmp_assets_all_*.bundle')))
if not tmp_bundles:
    print(f'ERROR: tmp_assets_all_*.bundle 파일을 찾을 수 없습니다.\n  경로: {GAME_DIR}')
    sys.exit(1)
TMP_BUNDLE_NAME = os.path.basename(tmp_bundles[0])

for fname in [TMP_BUNDLE_NAME, 'loca_pl_assets_all.bundle', 'loca_en_assets_all.bundle', 'yarn_assets_all.bundle', 'gameinit_assets_all.bundle', 'basecontentatoms_assets_all.bundle']:
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
PL_BUNDLE       = os.path.join(STAGING_DIR, 'loca_pl_assets_all.bundle')
YARN_BUNDLE     = os.path.join(STAGING_DIR, 'yarn_assets_all.bundle')
GAMEINIT_BUNDLE = os.path.join(STAGING_DIR, 'gameinit_assets_all.bundle')
ATOMS_BUNDLE    = os.path.join(STAGING_DIR, 'basecontentatoms_assets_all.bundle')

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

# ── 2. bookProfileMap_Books_PL: LoadNoBooks → LoadByLabel 수정 ──────────────
# 원본 loca_pl의 bookProfileMap이 LoadNoBooks 클래스를 사용해서 Total Weight=0 오류 발생
# EN(basecontentatoms_assets_all)은 LoadByLabel(label="BaseBooks")를 사용 → 동일하게 변경
# LoadByLabel 타입이 loca_pl ref_types에 없으므로 EN 번들에서 가져와서 주입 필요
BOOK_MAP_PL_PID  = -4942490322029175684
EN_ATOMS_BUNDLE  = ATOMS_BUNDLE
EN_BOOK_MAP_PID  = 2544964665192164594
print('\n=== 2단계: bookProfileMap LoadNoBooks → LoadByLabel 수정 ===')

# EN 번들에서 LoadByLabel SerializedType 노드 추출
env_atoms = UnityPy.load(EN_ATOMS_BUNDLE)
lb_type = None
for obj in env_atoms.objects:
    if obj.path_id == EN_BOOK_MAP_PID:
        for rt in obj.assets_file.ref_types:
            if rt.m_ClassName == 'LoadByLabel':
                lb_type = rt
                break
        break

if lb_type is None:
    print('  WARNING: LoadByLabel 타입을 EN 번들에서 찾지 못함 - 책 로딩 수정 생략')
else:
    env = UnityPy.load(PL_BUNDLE)
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour' and obj.path_id == BOOK_MAP_PL_PID:
            af = obj.assets_file
            # LoadByLabel 타입이 PL ref_types에 없으면 추가
            if not any(rt.m_ClassName == 'LoadByLabel' for rt in af.ref_types):
                af.ref_types.append(lb_type)
                af.mark_changed()
            raw = obj.read_typetree()
            refs = raw.get('references', {}).get('RefIds', [])
            lb_rid = raw.get('loadingBehavior', {}).get('rid')
            changed = False
            for ref in refs:
                if ref.get('rid') == lb_rid:
                    old_class = ref.get('type', {}).get('class', '')
                    if old_class == 'LoadNoBooks':
                        ref['type']['class'] = 'LoadByLabel'
                        ref['data'] = {'label': 'BaseBooks'}
                        changed = True
                        print(f'  LoadNoBooks → LoadByLabel (label="BaseBooks") 변경 완료')
                    else:
                        print(f'  이미 {old_class!r} (변경 불필요)')
                    break
            if changed:
                raw['references']['RefIds'] = refs
                obj.save_typetree(raw)
            break
    with open(PL_BUNDLE, 'wb') as f:
        f.write(env.file.save())

# basecontentatoms bookProfileMap_bookMap_X: LanguageID EN → "" (모든 언어에서 책 로드)
BOOK_MAP_PIDS = [
    -8617087727119501617, -6778395894939660626, -5333094954729345578,
    -921562150139066733, -40148986831196783, 158355228715938831,
    1971513495904204374, 3040073631708490807, 4113660763058764979,
    5002050191976784672, 7431006823350376679,
]
env_atoms = UnityPy.load(ATOMS_BUNDLE)
atoms_changed = 0
for obj in env_atoms.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id in BOOK_MAP_PIDS:
        raw = obj.read_typetree()
        if raw.get('LanguageID') == 'EN':
            raw['LanguageID'] = ''
            obj.save_typetree(raw)
            atoms_changed += 1
with open(ATOMS_BUNDLE, 'wb') as f:
    f.write(env_atoms.file.save())
print(f'  bookProfileMap LanguageID EN→"" 변경: {atoms_changed}개')

# ── 2b. loca_pl Sprites: EN externals 추가 + Sprites 테이블 복사 ─────────────
# loca_pl에는 external이 1개뿐 (fileID=1만), EN은 4개 (fileID=2=장르아이콘 포함)
# fix_pl_sprites.py와 동일한 방식으로 Mac에 적용
print('\n=== 2b단계: Sprites externals + 테이블 복사 ===')

# EN Sprites 테이블 + externals 읽기
env_en_tmp = UnityPy.load(EN_BUNDLE)
en_sprite_keys, en_sprite_vals = [], []
for obj in env_en_tmp.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if raw.get('m_Name') == 'Loca_Base Sprites EN':
            en_sprite_keys = raw['dictionary']['keyData']
            en_sprite_vals = raw['dictionary']['valueData']
            print(f'  EN Sprites: {len(en_sprite_keys)}개')
            break

en_externals = []
for cab in list(env_en_tmp.files.values())[0].files.values():
    en_externals = cab.externals
    break

# PL 번들에 externals 추가 + Sprites 테이블 업데이트
SPRITES_PL_PID = -567524315626770795
env = UnityPy.load(PL_BUNDLE)
pl_cab = None
for cab in list(env.files.values())[0].files.values():
    pl_cab = cab
    break

existing_paths = {e.path for e in pl_cab.externals}
for en_ext in en_externals[1:]:  # index 0(fileID=1)은 이미 있음
    if en_ext.path not in existing_paths:
        new_ext = copy.copy(pl_cab.externals[0])
        object.__setattr__(new_ext, 'path', en_ext.path)
        object.__setattr__(new_ext, 'guid', b'\x00' * 16)
        object.__setattr__(new_ext, 'type', 0)
        object.__setattr__(new_ext, 'temp_empty', '')
        pl_cab.externals.append(new_ext)
        pl_cab.mark_changed()
        existing_paths.add(en_ext.path)
        print(f'  external 추가: {en_ext.path.split("/")[-1]}')

for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == SPRITES_PL_PID:
        raw = obj.read_typetree()
        new_keys = list(raw['dictionary']['keyData'])
        new_vals = list(raw['dictionary']['valueData'])
        existing_key_set = set(new_keys)
        updated = added = 0
        for k, v in zip(en_sprite_keys, en_sprite_vals):
            if not isinstance(v, dict): continue
            if v.get('m_FileID', 0) == 0: continue  # 번들 내장 스프라이트 제외
            if k in existing_key_set:
                idx = new_keys.index(k)
                if isinstance(new_vals[idx], dict) and new_vals[idx].get('m_PathID', 0) == 0:
                    new_vals[idx] = {'m_FileID': v['m_FileID'], 'm_PathID': v['m_PathID']}
                    updated += 1
            else:
                new_keys.append(k)
                new_vals.append({'m_FileID': v['m_FileID'], 'm_PathID': v['m_PathID']})
                added += 1
        raw['dictionary']['keyData'] = new_keys
        raw['dictionary']['valueData'] = new_vals
        obj.save_typetree(raw)
        print(f'  Sprites: 업데이트 {updated}개, 추가 {added}개 (총 {len(new_keys)}개)')
        break

with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())

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

# ── 4. inject_yarn: 한국어 대사 → loca_pl Yarn PL 슬롯 주입 (Windows 방식) ───
# yarn_assets_all.bundle의 en-GB는 건드리지 않음
# loca_pl 내부 'Loca_Demo Yarn PL' (pid=YARN_PL_PID)에 EN base + 한국어 덮어쓰기
print('\n=== 4단계: 대사 주입 (loca_pl Yarn PL 슬롯) ===')

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

# EN base 전체를 yarn_assets_all en-GB에서 읽어옴
en_base = {}
env_yarn = UnityPy.load(YARN_BUNDLE)
for obj in env_yarn.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_ENGB_PID:
        raw = obj.read_typetree()
        st = raw['_stringTable']
        en_base = dict(zip(st['keys'], st['values']))
        break
print(f'  EN base: {len(en_base)}개')

# EN base 전체 + 한국어 덮어쓰기 → Yarn PL 테이블 구성
final_keys = list(en_base.keys())
final_vals = []
ko_applied = 0
for k in final_keys:
    if k in ko_lines and ko_lines[k]:
        final_vals.append(ko_lines[k])
        ko_applied += 1
    else:
        final_vals.append(en_base[k])
# EN base에 없는 한국어 번역 키도 추가
for k, v in ko_lines.items():
    if k not in en_base and v:
        final_keys.append(k)
        final_vals.append(v)

print(f'  최종: {len(final_keys)}개 (한국어 {ko_applied}개, 영어 {len(final_keys)-ko_applied}개)')

# loca_pl의 Yarn PL 슬롯에 주입 (PL 번들은 이미 앞 단계에서 로드/저장됨, 재로드)
env = UnityPy.load(PL_BUNDLE)
found = False
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_PL_PID:
        raw = obj.read_typetree()
        raw['dictionary']['keyData']   = final_keys
        raw['dictionary']['valueData'] = final_vals
        obj.save_typetree(raw)
        print(f'  저장: {raw["m_Name"]}')
        found = True
        break
if not found:
    print(f'  WARNING: Yarn PL 슬롯(pid={YARN_PL_PID})을 찾지 못했습니다')

with open(PL_BUNDLE, 'wb') as f:
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

# ── 7. zip 생성 + 파일 복사 ──────────────────────────────────────────────────
print('\n=== 7단계: zip 패키징 및 파일 복사 ===')

# zip 생성
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

# 압축 해제 파일도 release/mac/files/ 에 복사
FILES_DIR = os.path.join(RELEASE_DIR, 'files')
os.makedirs(FILES_DIR, exist_ok=True)
print(f'\n파일 복사: release/mac/files/')
for fname in os.listdir(STAGING_DIR):
    src = os.path.join(STAGING_DIR, fname)
    dst = os.path.join(FILES_DIR, fname)
    shutil.copy2(src, dst)
    print(f'  {fname}')

# ── 8. 스테이징 정리 ─────────────────────────────────────────────────────────
shutil.rmtree(os.path.join(PROJ_DIR, 'release', 'mac', '_staging'))
print('스테이징 폴더 정리 완료')
print('\n=== 빌드 완료 ===')
print(f'배포 파일: release/mac/{ZIP_NAME}')
print('사용자 설치 경로:')
print('  ~/Library/Application Support/Steam/steamapps/common/')
print('  Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/')
print('  StreamingAssets/aa/StandaloneOSX/')
