import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'
BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'
env = UnityPy.load(BUNDLE)
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        if d.m_Name in ('NanumPenScript-Regular EN', 'NanumPenScript-Regular'):
            print(f'{d.m_Name}: atW={d.m_AtlasWidth} atH={d.m_AtlasHeight}')
            tex_pid = d.m_AtlasTextures[0].m_PathID
            for obj2 in env.objects:
                if obj2.type.name == 'Texture2D' and obj2.path_id == tex_pid:
                    t = obj2.read()
                    print(f'  Texture2D: {t.m_Width}x{t.m_Height}')
