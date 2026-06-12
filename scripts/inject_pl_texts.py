"""
PL 번들 in-place 수정: Loca_Base Texts PL에 한국어 책 제목/설명 주입

전략:
  - EN 번들 백업에서 Loca_Base Books EN의 전체 키 목록 추출
  - to_translate_books_ko.json에서 한국어 번역 로드
  - PL 번들의 Loca_Base Texts PL (pid=4698197123910342691)을 in-place 수정
    keyData / valueData를 한국어 번역으로 채움
  - path_id 유지 → catalog.json 수정 불필요
  - EN 번들은 백업에서 복원 → 순수 영어 참고용

결과:
  Polish 선택 → 한국어 책 제목/설명
  English 선택 → 영어 (번역 비교용)
"""

import UnityPy, warnings, json, shutil, os
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
EN_BUNDLE  = BUNDLE_DIR + 'loca_en_assets_all.bundle'
EN_BACKUP  = BUNDLE_DIR + 'loca_en_assets_all.bundle.backup'
PL_BUNDLE  = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
PL_BACKUP  = BUNDLE_DIR + 'loca_pl_assets_all.bundle.backup'

KO_JSON    = 'C:/Users/Bin/tb_korean_patch/translation/to_translate_books_ko.json'

LOCA_BASE_TEXTS_PL_PID = 4698197123910342691

# ── 1. 한국어 번역 로드 ─────────────────────────────────────────────────────
print('한국어 번역 로드...')
with open(KO_JSON, encoding='utf-8') as f:
    ko_books = json.load(f)
print(f'  번역 항목: {len(ko_books)}개')

# ── 2. EN 백업에서 Loca_Base Books EN 키 전체 추출 ──────────────────────────
print('\nEN 번들 백업에서 책 키 추출...')
env_en = UnityPy.load(EN_BACKUP)

en_books_keys   = []   # Title_/Description_/Author_ 키 순서 (원본 그대로 유지)
en_books_values = []   # {'strings': ['영어 텍스트']} 형식

for obj in env_en.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        name = raw.get('m_Name', '')
        if 'Base Books' in name:
            dic = raw.get('dictionary', {})
            en_books_keys   = dic.get('keyData', [])
            en_books_values = dic.get('valueData', [])
            print(f'  {name}: {len(en_books_keys)}개 키 추출')
            # 샘플 확인
            for k, v in list(zip(en_books_keys, en_books_values))[:3]:
                print(f'    {k}: {str(v)[:60]}')
            break

if not en_books_keys:
    print('ERROR: Loca_Base Books EN 키를 찾지 못했습니다!')
    exit(1)

# ── 3. 한국어 값 배열 생성 ─────────────────────────────────────────────────
#    순서: EN 키 순서 그대로, 번역 있으면 한국어 / 없으면 영어 원문
print('\n한국어 값 배열 생성...')
ko_values = []
ko_count  = 0
en_count  = 0

for k, v_en in zip(en_books_keys, en_books_values):
    if k in ko_books and ko_books[k]:
        ko_text = ko_books[k]
        ko_values.append({'strings': [ko_text]})
        ko_count += 1
    else:
        # 번역 없으면 원문 영어 유지
        ko_values.append(v_en)
        en_count += 1

print(f'  한국어: {ko_count}개 / 영어 fallback: {en_count}개 / 총: {len(ko_values)}개')

# ── 4. PL 번들 in-place 수정 ────────────────────────────────────────────────
print(f'\nPL 번들 수정 중 (path_id={LOCA_BASE_TEXTS_PL_PID} in-place)...')
env_pl = UnityPy.load(PL_BUNDLE)

modified = False
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == LOCA_BASE_TEXTS_PL_PID:
        raw = obj.read_typetree()
        print(f'  대상: {raw.get("m_Name")} (path_id={obj.path_id})')
        print(f'  기존: {len(raw["dictionary"]["keyData"])}개 항목')

        raw['dictionary']['keyData']   = en_books_keys
        raw['dictionary']['valueData'] = ko_values

        obj.save_typetree(raw)
        print(f'  → {len(en_books_keys)}개 항목 주입 완료')
        modified = True
        break

if not modified:
    print(f'ERROR: path_id {LOCA_BASE_TEXTS_PL_PID} 를 PL 번들에서 찾지 못했습니다!')
    exit(1)

# ── 5. PL 번들 저장 ─────────────────────────────────────────────────────────
print('\nPL 번들 저장...')
with open(PL_BUNDLE, 'wb') as f:
    f.write(env_pl.file.save())
print('  저장 완료')

# ── 6. EN 번들 순수 영어로 복원 ─────────────────────────────────────────────
print('\nEN 번들 순수 영어로 복원...')
shutil.copy2(EN_BACKUP, EN_BUNDLE)
print('  복원 완료')

# ── 7. 결과 검증 ────────────────────────────────────────────────────────────
print('\n=== 결과 검증 ===')

print('\n[PL 번들]')
env_v = UnityPy.load(PL_BUNDLE)
for obj in env_v.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        name = raw.get('m_Name', '?')
        lang = raw.get('LanguageID', '?')
        dic  = raw.get('dictionary', {})
        if 'keyData' in dic:
            keys = dic['keyData']
            vals = dic['valueData']
            kr = sum(1 for v in vals
                     if isinstance(v, dict) and v.get('strings')
                     and any('가' <= c <= '힣' for c in (v['strings'][0] or '')))
            print(f'  {name} (lang={lang}, 총={len(keys)}, 한국어={kr})')
            if kr > 0:
                # 샘플 몇 개
                for k, v in zip(keys, vals):
                    if isinstance(v, dict) and v.get('strings') and any('가' <= c <= '힣' for c in (v['strings'][0] or '')):
                        print(f'    {k}: {v["strings"][0][:40]}')
                        break

print('\n[EN 번들 복원 확인]')
env_e = UnityPy.load(EN_BUNDLE)
for obj in env_e.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        name = raw.get('m_Name', '?')
        dic  = raw.get('dictionary', {})
        if 'keyData' in dic:
            keys = dic['keyData']
            vals = dic['valueData']
            kr = sum(1 for v in vals
                     if isinstance(v, dict) and v.get('strings')
                     and any('가' <= c <= '힣' for c in str(v.get('strings', [''])[0] or '')))
            en_flag = '✅ 순수 영어' if kr == 0 else f'⚠️  한국어 {kr}개 남아있음'
            print(f'  {name} (총={len(keys)}, {en_flag})')

print('\n완료!')
print('  Polish 선택  →  한국어 책 제목/설명')
print('  English 선택 →  영어 (번역 비교용)')
