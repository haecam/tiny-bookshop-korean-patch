"""EN 번들의 로케일 테이블 구조 + catalog.json 전체 locale 매핑 분석"""
import UnityPy, warnings, json
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BASE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/'
BUNDLE_DIR = BASE + 'StandaloneWindows64/'

# ─── 1. catalog.json 언어 관련 분석 ─────────────────────────────────────────
print('=== catalog.json 분석 ===')
with open(BASE + 'catalog.json', encoding='utf-8') as f:
    cat = json.load(f)

# keys 배열에서 loca_ 관련 항목 찾기
keys = cat.get('m_Keys', cat.get('keys', []))
buckets = cat.get('m_BucketDataString', cat.get('buckets', ''))
print(f'총 키 수: {len(keys)}')

# locale 관련 키 찾기
loca_keys = [k for k in keys if isinstance(k, str) and 'loca' in k.lower()]
print(f'loca 키: {len(loca_keys)}개')
for k in loca_keys[:30]:
    print(f'  {k}')

# 언어 코드 목록 찾기
lang_keys = [k for k in keys if isinstance(k, str) and len(k) == 2 and k.isupper()]
print(f'\n언어 코드: {sorted(set(lang_keys))}')

# ─── 2. EN 번들 백업 구조 분석 ──────────────────────────────────────────────
print('\n=== EN 번들 (백업 = 원본) ===')
env_bak = UnityPy.load(BUNDLE_DIR + 'loca_en_assets_all.bundle.backup')
tables = {}
for obj in env_bak.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        name = d.m_Name
        lang = getattr(d, 'LanguageID', '?')
        if hasattr(d, 'dictionary'):
            keys_data = list(d.dictionary.keyData)
            vals_data = list(d.dictionary.valueData)
            tables[name] = {'lang': lang, 'count': len(keys_data),
                           'pid': obj.path_id, 'sample': list(zip(keys_data[:3], vals_data[:3]))}
        else:
            tables[name] = {'lang': lang, 'count': 0, 'pid': obj.path_id, 'sample': []}

for name, info in tables.items():
    print(f'  [{info["pid"]}] {name} (lang={info["lang"]}, strings={info["count"]})')
    for k, v in info['sample']:
        vstr = str(v)[:60] if v else ''
        print(f'    {k}: {vstr}')

# ─── 3. EN 번들 현재 (Korean 주입된 버전) ──────────────────────────────────
print('\n=== EN 번들 (현재 = Korean 주입됨) ===')
env_cur = UnityPy.load(BUNDLE_DIR + 'loca_en_assets_all.bundle')
for obj in env_cur.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        if hasattr(d, 'dictionary'):
            keys_data = list(d.dictionary.keyData)
            vals_data = list(d.dictionary.valueData)
            print(f'  {d.m_Name} (lang={getattr(d, "LanguageID", "?")}, strings={len(keys_data)})')
            # 한글 포함 여부
            kr_count = sum(1 for v in vals_data if any('가' <= c <= '힣' for c in str(v) if v))
            print(f'    한글 포함 항목: {kr_count}개')
            for k, v in list(zip(keys_data, vals_data))[:3]:
                print(f'    {k}: {str(v)[:60]}')

# ─── 4. Polish 번들 구조 ────────────────────────────────────────────────────
print('\n=== Polish 번들 구조 ===')
env_pl = UnityPy.load(BUNDLE_DIR + 'loca_pl_assets_all.bundle')
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        name = d.m_Name
        lang = getattr(d, 'LanguageID', '?')
        pid = obj.path_id
        if hasattr(d, 'dictionary'):
            keys_data = list(d.dictionary.keyData)
            vals_data = list(d.dictionary.valueData)
            print(f'  [{pid}] {name} (lang={lang}, strings={len(keys_data)})')
            for k, v in list(zip(keys_data, vals_data))[:3]:
                print(f'    {k}: {str(v)[:60]}')
        else:
            print(f'  [{pid}] {name} (lang={lang}, no dictionary)')

# ─── 5. 다른 번들과 비교 (JP 확인 - CJK 언어이므로 구조 비슷할 것) ─────────
print('\n=== JP 번들 구조 ===')
env_jp = UnityPy.load(BUNDLE_DIR + 'loca_jp_assets_all.bundle')
for obj in env_jp.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        if hasattr(d, 'dictionary'):
            keys_data = list(d.dictionary.keyData)
            vals_data = list(d.dictionary.valueData)
            lang = getattr(d, 'LanguageID', '?')
            print(f'  {d.m_Name} (lang={lang}, strings={len(keys_data)})')
            for k, v in list(zip(keys_data, vals_data))[:2]:
                print(f'    {k}: {str(v)[:60]}')
