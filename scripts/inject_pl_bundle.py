"""
EN 번들 구조를 기반으로 PL 번들을 한국어 번들로 재구성

흐름:
1. EN 백업 (원본) 번들을 PL 번들 파일 위치에 복사
2. UnityPy의 read_typetree / save_typetree를 사용해서:
   - 모든 MonoBehaviour의 LanguageID: EN -> PL
   - 모든 MonoBehaviour의 m_Name: "...EN" -> "...PL"
   - Loca_Base Books: 한국어 번역 주입 (strings[0] 교체)
3. PL 번들 저장
4. EN 번들 원본 복원

결과: 폴란드어 선택 시 -> 한국어 책 제목 + 영어 UI
"""
import UnityPy, warnings, json, shutil, os
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
EN_BUNDLE  = BUNDLE_DIR + 'loca_en_assets_all.bundle'
EN_BACKUP  = BUNDLE_DIR + 'loca_en_assets_all.bundle.backup'
PL_BUNDLE  = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
PL_BACKUP  = BUNDLE_DIR + 'loca_pl_assets_all.bundle.backup'

KO_JSON    = 'C:/git/tiny-bookshop-korean-patch/translation/to_translate_books_ko.json'

# --- 한국어 책 번역 로드 -------------------------------------------------------
print('한국어 번역 로드...')
with open(KO_JSON, encoding='utf-8') as f:
    ko_books = json.load(f)
print(f'  번역 항목: {len(ko_books)}개')

# --- PL 번들 백업 (최초 1회) ---------------------------------------------------
if not os.path.exists(PL_BACKUP):
    shutil.copy2(PL_BUNDLE, PL_BACKUP)
    print(f'PL 번들 백업: {PL_BACKUP}')
else:
    print(f'PL 번들 백업 이미 존재')

# --- EN 백업을 PL 위치로 복사 --------------------------------------------------
print('\nEN 백업 -> PL 위치 복사...')
shutil.copy2(EN_BACKUP, PL_BUNDLE)
print('  복사 완료')

# --- PL 번들 로드 및 수정 ------------------------------------------------------
print('\nPL 번들 수정 중...')
env = UnityPy.load(PL_BUNDLE)

stats = {'tables': 0, 'name_changed': 0, 'lang_changed': 0,
         'books_injected': 0, 'books_missing': 0}

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue

    raw = obj.read_typetree()
    changed = False

    # --- LanguageID 변경 ---
    if raw.get('LanguageID') == 'EN':
        raw['LanguageID'] = 'PL'
        stats['lang_changed'] += 1
        changed = True

    # --- m_Name 변경 ---
    name = raw.get('m_Name', '')
    if name.endswith(' EN'):
        raw['m_Name'] = name[:-3] + ' PL'
        stats['name_changed'] += 1
        changed = True
    elif ' EN ' in name:
        raw['m_Name'] = name.replace(' EN ', ' PL ')
        stats['name_changed'] += 1
        changed = True

    # --- Loca_Base Books: 한국어 주입 ---
    if 'Base Books' in name and 'dictionary' in raw:
        dic = raw['dictionary']
        keys   = dic.get('keyData', [])
        values = dic.get('valueData', [])
        new_values = []
        for k, v in zip(keys, values):
            if k in ko_books and ko_books[k]:
                # v는 {'strings': ['원문']} 형태
                if isinstance(v, dict) and 'strings' in v and v['strings']:
                    v = dict(v)  # 복사
                    v['strings'] = list(v['strings'])
                    v['strings'][0] = ko_books[k]
                    stats['books_injected'] += 1
                else:
                    stats['books_missing'] += 1
            new_values.append(v)
        dic['valueData'] = new_values
        changed = True

    if changed:
        obj.save_typetree(raw)
        stats['tables'] += 1

print(f'  수정된 테이블: {stats["tables"]}개')
print(f'  이름 변경: {stats["name_changed"]}개')
print(f'  LanguageID 변경: {stats["lang_changed"]}개')
print(f'  한국어 책 주입: {stats["books_injected"]}개')
if stats['books_missing']:
    print(f'  WARNING 누락: {stats["books_missing"]}개')

# --- PL 번들 저장 --------------------------------------------------------------
print('\nPL 번들 저장 중...')
with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())
print(f'  저장 완료')

# --- EN 번들 원본 복원 ---------------------------------------------------------
print('\nEN 번들 원본 복원...')
shutil.copy2(EN_BACKUP, EN_BUNDLE)
print(f'  복원 완료')

# --- 결과 검증 -----------------------------------------------------------------
print('\n=== 결과 검증 ===')
env_v = UnityPy.load(PL_BUNDLE)
for obj in env_v.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    raw = obj.read_typetree()
    name = raw.get('m_Name', '?')
    lang = raw.get('LanguageID', '?')
    dic  = raw.get('dictionary', {})
    if 'keyData' in dic:
        keys = dic['keyData']
        vals = dic['valueData']
        kr = sum(1 for v in vals
                 if isinstance(v, dict) and v.get('strings')
                 and any('가' <= c <= '힣' for c in v['strings'][0]))
        print(f'  {name} (lang={lang}, strings={len(keys)}, KR={kr})')
    else:
        print(f'  {name} (lang={lang}, no dict)')

env_e = UnityPy.load(EN_BUNDLE)
print('\nEN 번들 복원 확인:')
for obj in env_e.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    raw = obj.read_typetree()
    name = raw.get('m_Name', '?')
    lang = raw.get('LanguageID', '?')
    dic  = raw.get('dictionary', {})
    if 'keyData' in dic:
        print(f'  {name} (lang={lang}, strings={len(dic["keyData"])})')

print('\n완료! 게임에서 Polish(PL) 선택 -> 한국어 책 제목')
