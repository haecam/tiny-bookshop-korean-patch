"""
PL 번들 Loca_Demo Yarn PL에 한국어 대사 주입

소스: to_translate_dialogue_ko.json (1483개)
  - 562개: 현재 게임 활성 노드 → 게임에서 한국어로 표시됨
  - 921개: 미사용/삭제 노드 → 주입되지만 게임에서 호출 안 됨 (무해)

valueData 형식: 순수 텍스트 문자열 (DE/RU 등과 동일)
path_id: -4050940925882462320 (Loca_Demo Yarn PL)
"""

import UnityPy, warnings, json, sys
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
PL_BUNDLE  = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
KO_JSON    = 'C:/Users/Bin/tb_korean_patch/translation/to_translate_dialogue_ko.json'

YARN_PL_PID = -4050940925882462320  # Loca_Demo Yarn PL

# ── 번역 로드 ────────────────────────────────────────────────────────────────
with open(KO_JSON, encoding='utf-8') as f:
    ko_raw = json.load(f)

# 값이 dict {'text': '...'} 형태 → 순수 텍스트만 추출
ko_lines = {}
for line_id, val in ko_raw.items():
    if isinstance(val, dict):
        ko_lines[line_id] = val.get('text', '')
    else:
        ko_lines[line_id] = str(val)

print(f'번역 로드: {len(ko_lines)}개')

# ── PL 번들 수정 ─────────────────────────────────────────────────────────────
print('PL 번들 수정 중...')
env = UnityPy.load(PL_BUNDLE)

modified = False
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_PL_PID:
        raw = obj.read_typetree()
        print(f'  대상: {raw["m_Name"]} (기존 {len(raw["dictionary"]["keyData"])}개)')

        raw['dictionary']['keyData']   = list(ko_lines.keys())
        raw['dictionary']['valueData'] = list(ko_lines.values())

        obj.save_typetree(raw)
        print(f'  → {len(ko_lines)}개 주입 완료')
        modified = True
        break

if not modified:
    print(f'ERROR: Yarn PL 오브젝트를 찾지 못했습니다 (pid={YARN_PL_PID})')
    exit(1)

# ── 저장 ─────────────────────────────────────────────────────────────────────
with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('저장 완료')

# ── 검증 ─────────────────────────────────────────────────────────────────────
print('\n=== 검증 ===')
env2 = UnityPy.load(PL_BUNDLE)
for obj in env2.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_PL_PID:
        raw = obj.read_typetree()
        keys = raw['dictionary']['keyData']
        vals = raw['dictionary']['valueData']
        kr = sum(1 for v in vals if any('가' <= c <= '힣' for c in str(v)))
        print(f'  {raw["m_Name"]}: 총 {len(keys)}개, 한국어 {kr}개')
        print('  샘플 3개:')
        for k, v in zip(keys[:3], vals[:3]):
            print(f'    {k}: {str(v)[:50]}')
        break
