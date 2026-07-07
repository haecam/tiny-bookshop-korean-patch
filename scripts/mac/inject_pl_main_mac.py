"""
PL 번들 Loca_Base Texts PL에 UI 텍스트 한국어 병합 주입 (Mac 버전)
"""
import UnityPy, warnings, json, sys, ast

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

import os
PROJ_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANS_DIR = os.path.join(PROJ_DIR, 'translation')

BUNDLE_DIR = os.path.expanduser(
    '~/Library/Application Support/Steam/steamapps/common/'
    'Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/'
    'StreamingAssets/aa/StandaloneOSX/'
)
PL_BUNDLE = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
KO_JSON   = os.path.join(TRANS_DIR, 'to_translate_main_ko.json')

TEXTS_PL_PID = 6208505299439420760

with open(KO_JSON, encoding='utf-8') as f:
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

print(f'새 번역: {len(new_translations)}개')

print('PL 번들 로드...')
env = UnityPy.load(PL_BUNDLE)

modified = False
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == TEXTS_PL_PID:
        raw = obj.read_typetree()
        existing_keys = raw['dictionary']['keyData']
        existing_vals = raw['dictionary']['valueData']
        print(f'  기존: {len(existing_keys)}개 (책 제목/설명)')

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
    print('ERROR: Loca_Base Texts PL 오브젝트를 찾지 못했습니다')
    exit(1)

with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n저장 완료')
print('\n완료! 게임 재시작 후 한국어로 UI 텍스트 확인')