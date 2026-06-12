"""
PL 번들 Loca_Base Texts PL에 UI 텍스트 한국어 병합 주입

기존 내용 (2786개 책 제목/설명/저자) 유지하면서
to_translate_main_ko.json의 3개 테이블 추가:
  - Loca_Base Texts EN    : 2459개 (UI 전반)
  - Loca_Additional Texts EN: 255개 (설정 설명 등)
  - Loca_Recommendations EN: 581개 (책 추천 UI)
"""

import UnityPy, warnings, json, sys, ast
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
PL_BUNDLE  = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
KO_JSON    = 'C:/Users/Bin/tb_korean_patch/translation/to_translate_main_ko.json'

TEXTS_PL_PID = 4698197123910342691  # Loca_Base Texts PL

# ── 새 번역 로드 ─────────────────────────────────────────────────────────────
with open(KO_JSON, encoding='utf-8') as f:
    raw_data = json.load(f)

new_translations = {}  # key -> {'strings': ['한국어']}
for table_name, val in raw_data.items():
    parsed = ast.literal_eval(val) if isinstance(val, str) else val
    for k, v in parsed.items():
        # 값이 문자열이면 strings 형식으로 감싸기
        if isinstance(v, str):
            new_translations[k] = {'strings': [v]}
        elif isinstance(v, dict):
            new_translations[k] = v
        else:
            new_translations[k] = {'strings': [str(v)]}

print(f'새 번역: {len(new_translations)}개')

# ── PL 번들 수정 ─────────────────────────────────────────────────────────────
print('PL 번들 로드...')
env = UnityPy.load(PL_BUNDLE)

modified = False
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == TEXTS_PL_PID:
        raw = obj.read_typetree()
        existing_keys = raw['dictionary']['keyData']
        existing_vals = raw['dictionary']['valueData']
        print(f'  기존: {len(existing_keys)}개 (책 제목/설명)')

        # 기존 데이터 + 새 번역 병합
        merged_keys = list(existing_keys)
        merged_vals = list(existing_vals)

        added = 0
        for k, v in new_translations.items():
            if k not in set(existing_keys):
                merged_keys.append(k)
                merged_vals.append(v)
                added += 1

        raw['dictionary']['keyData']   = merged_keys
        raw['dictionary']['valueData'] = merged_vals
        obj.save_typetree(raw)
        print(f'  추가: {added}개')
        print(f'  병합 후 총: {len(merged_keys)}개')
        modified = True
        break

if not modified:
    print(f'ERROR: Loca_Base Texts PL 오브젝트를 찾지 못했습니다')
    exit(1)

# ── 저장 ─────────────────────────────────────────────────────────────────────
with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n저장 완료')

# ── 검증 ─────────────────────────────────────────────────────────────────────
print('\n=== 검증 ===')
env2 = UnityPy.load(PL_BUNDLE)
for obj in env2.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        dic = raw.get('dictionary', {})
        n = len(dic.get('keyData', []))
        if n > 0:
            kr = sum(1 for v in dic['valueData']
                     if isinstance(v, dict) and v.get('strings')
                     and any('가' <= c <= '힣' for c in (v['strings'][0] or '')))
            print(f'  {raw["m_Name"]}: 총 {n}개, 한국어 {kr}개')

print('\n완료! 게임 재시작 후 한국어로 UI 텍스트 확인')
