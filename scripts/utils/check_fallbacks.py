"""EN 폰트들의 fallback 구조 확인"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

env = UnityPy.load(BUNDLE)

# pid -> name 맵
pid_name = {}
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        try:
            d = obj.read()
            pid_name[obj.path_id] = d.m_Name
        except:
            pass

# 주요 EN 폰트 fallback 확인
targets = {
    'Vollkorn-Regular SDF EN',
    'Vollkorn-SemiBold SDF',
    'Itim-Regular SDF EN',
    'Schoolbell-Regular EN',
    'NanumPenScript-Regular EN',
    'TMP Settings',
}

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    try:
        d = obj.read()
        if d.m_Name not in targets:
            continue
        print(f'\n=== {d.m_Name} (pid={obj.path_id}) ===')
        if hasattr(d, 'm_FallbackFontAssets'):
            falls = d.m_FallbackFontAssets or []
            print(f'  fallback ({len(falls)}개):')
            for fb in falls:
                print(f'    -> pid={fb.m_PathID} | {pid_name.get(fb.m_PathID, "?")}')
        if hasattr(d, 'm_fallbackFontAssets'):
            falls = d.m_fallbackFontAssets or []
            print(f'  global fallback ({len(falls)}개):')
            for fb in falls:
                print(f'    -> pid={fb.m_PathID} | {pid_name.get(fb.m_PathID, "?")}')
        if hasattr(d, 'm_defaultFontAsset'):
            df = d.m_defaultFontAsset
            print(f'  defaultFont: pid={df.m_PathID} | {pid_name.get(df.m_PathID, "?")}')
    except:
        pass
