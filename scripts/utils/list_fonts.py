"""TMP 번들의 모든 폰트 에셋 나열"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

env = UnityPy.load(BUNDLE)
print('=== TMP 번들 내 MonoBehaviour ===')
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
                print(f'  pid={obj.path_id:25d} | mode={mode} | {aw}x{ah} | {chars}chars | {name}')
            else:
                print(f'  pid={obj.path_id:25d} | (Settings/Other) | {name}')
        except:
            pass

print()
print('=== Texture2D ===')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        t = obj.read()
        print(f'  pid={obj.path_id:25d} | {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat} | {t.m_Name}')

print()
print('=== Font (.ttf) ===')
for obj in env.objects:
    if obj.type.name == 'Font':
        f = obj.read()
        print(f'  pid={obj.path_id:25d} | {f.m_Name}')
