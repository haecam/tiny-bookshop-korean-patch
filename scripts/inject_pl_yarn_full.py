"""
PL Yarn 테이블 전체 채우기:
  EN base 6592개를 기본값(영어)으로 채우고
  우리 번역 1483개를 한국어로 덮어쓰기
  → Missing Yarn Line 오류 해결
"""
import UnityPy, warnings, sys, json
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BASE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
PL_BUNDLE = BASE + 'loca_pl_assets_all.bundle'
YARN_PL_PID = -4050940925882462320

# ── EN base 전체 로드 ────────────────────────────────────────────────────────
env_yarn = UnityPy.load(BASE + 'yarn_assets_all.bundle')
en_base = {}
for obj in env_yarn.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if raw.get('m_Name') == 'en-GB':
            st = raw['_stringTable']
            en_base = dict(zip(st['keys'], st['values']))
            break
print(f'EN base: {len(en_base)}개')

# ── 한국어 번역 로드 ─────────────────────────────────────────────────────────
with open('C:/git/tiny-bookshop-korean-patch/translation/to_translate_dialogue_ko.json', encoding='utf-8') as f:
    ko_raw = json.load(f)

ko_lines = {}
for k, v in ko_raw.items():
    ko_lines[k] = v.get('text', '') if isinstance(v, dict) else str(v)
print(f'한국어 번역: {len(ko_lines)}개')

# ── 최종 테이블 구성: EN base 전체 + 한국어 덮어쓰기 ─────────────────────────
final_keys = list(en_base.keys())
final_vals = []
ko_applied = 0

for k in final_keys:
    if k in ko_lines and ko_lines[k]:
        final_vals.append(ko_lines[k])
        ko_applied += 1
    else:
        final_vals.append(en_base[k])  # 영어 fallback

# 한국어 번역 중 EN base에 없는 키도 추가 (혹시 모를 항목)
for k, v in ko_lines.items():
    if k not in en_base and v:
        final_keys.append(k)
        final_vals.append(v)

print(f'최종: {len(final_keys)}개 (한국어 {ko_applied}개, 영어 {len(final_keys)-ko_applied}개)')

# ── PL 번들 수정 ─────────────────────────────────────────────────────────────
env_pl = UnityPy.load(PL_BUNDLE)
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_PL_PID:
        raw = obj.read_typetree()
        raw['dictionary']['keyData']   = final_keys
        raw['dictionary']['valueData'] = final_vals
        obj.save_typetree(raw)
        print(f'저장: {raw["m_Name"]}')
        break

with open(PL_BUNDLE, 'wb') as f:
    f.write(env_pl.file.save())
print('완료')
