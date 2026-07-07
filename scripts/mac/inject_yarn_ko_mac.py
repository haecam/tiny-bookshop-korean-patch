"""
yarn_assets_all.bundle의 en-GB 스트링 테이블에 한국어 대사 주입 (Mac 전용)

Mac loca_pl 번들에는 Yarn 오브젝트가 없어서 대사는 en-GB로 폴백됨.
en-GB에 한국어를 직접 덮어써서 Polish 선택 시 한국어 대사가 표시되도록 처리.
"""
import UnityPy, warnings, json, os, glob, sys

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
YARN_BUNDLE = BUNDLE_DIR + 'yarn_assets_all.bundle'
YARN_BACKUP = YARN_BUNDLE + '.backup'

# en-GB 오브젝트 path_id
ENGB_PID = -3371373143731600161

# ── 번역 로드 & 병합 ──────────────────────────────────────────────────────────
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
        text = extract_text(v)
        if text:
            ko_lines[k] = text
    print(f'기존 번역: {len(data)}개 로드')

char_dir = os.path.join(TRANS_DIR, 'characters')
char_count = 0
for path in sorted(glob.glob(os.path.join(char_dir, '*.json'))):
    data = load_json(path)
    before = len(ko_lines)
    for k, v in data.items():
        text = extract_text(v)
        if text:
            ko_lines[k] = text
    char_count += len(ko_lines) - before
print(f'캐릭터 대사: {char_count}개 추가')

news_path = os.path.join(TRANS_DIR, 'newspaper_articles_ko.json')
if os.path.exists(news_path):
    data = load_json(news_path)
    before = len(ko_lines)
    for k, v in data.items():
        text = extract_text(v)
        if text:
            ko_lines[k] = text
    print(f'신문 기사: {len(data)}개 로드 ({len(ko_lines) - before}개 신규)')

print(f'\n총 한국어 번역: {len(ko_lines)}개 라인')

# ── 번들 백업 ─────────────────────────────────────────────────────────────────
if not os.path.exists(YARN_BACKUP):
    import shutil
    shutil.copy2(YARN_BUNDLE, YARN_BACKUP)
    print(f'yarn 번들 백업 완료')
else:
    print(f'yarn 번들 백업 이미 존재')

# ── en-GB 스트링 테이블 패치 ──────────────────────────────────────────────────
print('\nyan 번들 로드...')
env = UnityPy.load(YARN_BUNDLE)

modified = False
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == ENGB_PID:
        raw = obj.read_typetree()
        st = raw.get('_stringTable', {})
        keys = st.get('keys', [])
        vals = st.get('values', [])
        print(f'  en-GB 원본: {len(keys)}개 라인')

        applied = 0
        new_vals = []
        for k, v in zip(keys, vals):
            if k in ko_lines and ko_lines[k]:
                new_vals.append(ko_lines[k])
                applied += 1
            else:
                new_vals.append(v)  # 영어 유지

        st['values'] = new_vals
        raw['_stringTable'] = st
        obj.save_typetree(raw)
        print(f'  한국어 적용: {applied}개 / {len(keys)}개')
        modified = True
        break

if not modified:
    print(f'ERROR: en-GB 오브젝트를 찾지 못했습니다 (pid={ENGB_PID})')
    sys.exit(1)

# ── 저장 ─────────────────────────────────────────────────────────────────────
with open(YARN_BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n저장 완료!')
print('- Polish 선택 시 한국어 대사 표시')
print('- 미번역 대사는 영어로 표시')
