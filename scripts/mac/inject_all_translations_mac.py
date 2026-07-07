"""
전체 번역 통합 주입 스크립트 (Mac 버전)

병합 대상:
  1. to_translate_dialogue_ko.json
  2. translation/characters/*.json
  3. translation/newspaper_articles_ko.json

모두 Loca_Demo Yarn PL (pid: -4050940925882462320) 에 주입
"""
import UnityPy, warnings, json, sys, glob, os

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

PROJ_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANS_DIR = os.path.join(PROJ_DIR, 'translation')

BUNDLE_DIR = os.path.expanduser(
    '~/Library/Application Support/Steam/steamapps/common/'
    'Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/'
    'StreamingAssets/aa/StandaloneOSX/'
)
PL_BUNDLE   = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
YARN_PL_PID = -4050940925882462320

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def extract_text(val):
    if isinstance(val, dict):
        return val.get('text', '')
    return str(val)

ko_lines = {}

base_path = os.path.join(TRANS_DIR, 'to_translate_dialogue_ko.json')
if os.path.exists(base_path):
    data = load_json(base_path)
    for k, v in data.items():
        ko_lines[k] = extract_text(v)
    print(f'기존 번역: {len(data)}개 로드')

char_dir = os.path.join(TRANS_DIR, 'characters')
char_count = 0
for path in sorted(glob.glob(os.path.join(char_dir, '*.json'))):
    data = load_json(path)
    before = len(ko_lines)
    for k, v in data.items():
        ko_lines[k] = extract_text(v)
    added = len(ko_lines) - before
    char_count += added
    fname = os.path.basename(path)
    print(f'  {fname}: {len(data)}개 ({added}개 신규)')
print(f'캐릭터 대사: {char_count}개 추가')

news_path = os.path.join(TRANS_DIR, 'newspaper_articles_ko.json')
if os.path.exists(news_path):
    data = load_json(news_path)
    before = len(ko_lines)
    for k, v in data.items():
        ko_lines[k] = extract_text(v)
    added = len(ko_lines) - before
    print(f'신문 기사: {len(data)}개 로드 ({added}개 신규)')

print(f'\n총 병합: {len(ko_lines)}개 라인')

print('\nPL 번들 수정 중...')
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
    sys.exit(1)

with open(PL_BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('저장 완료')

print('\n=== 검증 ===')
env2 = UnityPy.load(PL_BUNDLE)
for obj in env2.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_PL_PID:
        raw = obj.read_typetree()
        keys = raw['dictionary']['keyData']
        vals = raw['dictionary']['valueData']
        kr = sum(1 for v in vals if any('가' <= c <= '힣' for c in str(v)))
        en = sum(1 for v in vals if v and not any('가' <= c <= '힣' for c in str(v)))
        print(f'  {raw["m_Name"]}: 총 {len(keys)}개')
        print(f'  한국어 번역: {kr}개')
        print(f'  영어(미번역): {en}개')
        break