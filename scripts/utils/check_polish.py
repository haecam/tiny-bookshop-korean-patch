"""Polish 번들 구조 + 게임 언어 설정 확인"""
import UnityPy, warnings, json, re
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'
BASE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/'

# 1. Polish 번들 내용
env = UnityPy.load(BASE + 'StandaloneWindows64/loca_pl_assets_all.bundle')
print('=== Polish 번들 ===')
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        print(f'  {d.m_Name}')
        if hasattr(d, 'LanguageID'):
            print(f'    LanguageID: {d.LanguageID}')
        if hasattr(d, 'dictionary'):
            keys = list(d.dictionary.keyData)
            vals = list(d.dictionary.valueData)
            print(f'    strings: {len(keys)}개')
            for k, v in list(zip(keys, vals))[:5]:
                print(f'      {k}: {str(v)[:50]}')

# 2. catalog.json에서 loca 관련 항목
print('\n=== catalog.json loca 항목 ===')
with open(BASE + 'catalog.json', 'r', encoding='utf-8') as f:
    raw = f.read()

# loca 번들명 추출
loca_entries = re.findall(r'loca_\w+', raw)
print('언어 번들들:', sorted(set(loca_entries)))

# 3. settings.json 확인
print('\n=== settings.json ===')
with open(BASE + 'settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
print(json.dumps(settings, indent=2)[:500])
