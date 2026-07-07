"""
맥용 번들 구조 확인 스크립트

실행 전 확인:
  pip install UnityPy

실행:
  python scripts/utils/inspect_mac_bundles.py
"""
import UnityPy, warnings, glob, os, sys

warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BUNDLE_DIR = os.path.expanduser(
    '~/Library/Application Support/Steam/steamapps/common/'
    'Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/'
    'StreamingAssets/aa/StandaloneOSX'
)

if not os.path.isdir(BUNDLE_DIR):
    print(f'ERROR: 번들 디렉토리를 찾을 수 없습니다:\n  {BUNDLE_DIR}')
    sys.exit(1)

print(f'번들 디렉토리: {BUNDLE_DIR}\n')

tmp_bundles = sorted(glob.glob(os.path.join(BUNDLE_DIR, 'tmp_assets_all_*.bundle')))
print(f'=== tmp 번들 파일 ({len(tmp_bundles)}개) ===')
for p in tmp_bundles:
    print(f'  {os.path.basename(p)}')

if not tmp_bundles:
    print('  (없음)')
    sys.exit(1)

TMP_BUNDLE = tmp_bundles[0]
print(f'\n사용할 번들: {os.path.basename(TMP_BUNDLE)}\n')

env = UnityPy.load(TMP_BUNDLE)

print('=== MonoBehaviour (폰트 에셋) ===')
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        try:
            d = obj.read()
            name = d.m_Name
            if hasattr(d, 'm_AtlasPopulationMode'):
                mode = d.m_AtlasPopulationMode
                chars = len(d.m_CharacterTable) if hasattr(d, 'm_CharacterTable') and d.m_CharacterTable else 0
                aw = getattr(d, 'm_AtlasWidth', 0)
                ah = getattr(d, 'm_AtlasHeight', 0)
                fallbacks = []
                if hasattr(d, 'm_FallbackFontAssetTable'):
                    fallbacks = [fb.m_PathID for fb in (d.m_FallbackFontAssetTable or [])]
                fb_str = f' fallbacks={fallbacks}' if fallbacks else ''
                print(f'  pid={obj.path_id:25d} | mode={mode} | {aw}x{ah} | {chars}chars | {name}{fb_str}')
            else:
                print(f'  pid={obj.path_id:25d} | (Other) | {name}')
        except Exception as e:
            print(f'  pid={obj.path_id:25d} | ERROR: {e}')

print()
print('=== Texture2D ===')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        t = obj.read()
        print(f'  pid={obj.path_id:25d} | {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat} | {t.m_Name}')

print()
print('=== loca 번들 path_id ===')
for bundle_name in ('loca_pl_assets_all.bundle', 'loca_en_assets_all.bundle'):
    path = os.path.join(BUNDLE_DIR, bundle_name)
    if not os.path.exists(path):
        print(f'  {bundle_name}: 없음')
        continue
    lenv = UnityPy.load(path)
    print(f'\n  [{bundle_name}]')
    for obj in lenv.objects:
        if obj.type.name == 'MonoBehaviour':
            try:
                raw = obj.read_typetree()
                name = raw.get('m_Name', '?')
                dic  = raw.get('dictionary', {})
                n    = len(dic.get('keyData', []))
                lang = raw.get('LanguageID', '')
                lang_str = f' lang={lang}' if lang else ''
                print(f'    pid={obj.path_id:25d} | {n}keys{lang_str} | {name}')
            except Exception as e:
                print(f'    pid={obj.path_id:25d} | ERROR: {e}')

print('\n완료!')
