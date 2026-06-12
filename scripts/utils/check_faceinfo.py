"""NanumPenScript face info + 기존 EN 글리프 크기 확인"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

# 백업에서 원본 확인
BACKUP = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle.backup'
env = UnityPy.load(BACKUP)

targets = ['NanumPenScript-Regular EN', 'NanumPenScript-Regular',
           'Vollkorn-Regular SDF EN', 'Schoolbell-Regular EN', 'Itim-Regular SDF EN']

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    d = obj.read()
    if d.m_Name not in targets:
        continue
    print(f'\n=== {d.m_Name} ===')
    fi = d.m_FaceInfo
    attrs = [a for a in dir(fi) if not a.startswith('_')]
    print(f'FaceInfo attrs: {attrs}')
    for a in attrs:
        if a not in ('assets_file','object_reader','save','set_object_reader','get_type'):
            try:
                print(f'  {a}: {getattr(fi, a)}')
            except:
                pass

    if d.m_CharacterTable:
        print(f'char_table: {len(d.m_CharacterTable)}개')
        # 영문 알파벳 'A' 글리프 크기 확인
        for c in d.m_CharacterTable:
            if c.m_Unicode == ord('A'):
                g = next((g for g in d.m_GlyphTable if g.m_Index == c.m_GlyphIndex), None)
                if g:
                    print(f"  'A' glyph: rect=({g.m_GlyphRect.m_X},{g.m_GlyphRect.m_Y} {g.m_GlyphRect.m_Width}x{g.m_GlyphRect.m_Height})")
                    print(f"  'A' metrics: adv={g.m_Metrics.m_HorizontalAdvance:.1f} bY={g.m_Metrics.m_HorizontalBearingY:.1f} h={g.m_Metrics.m_Height:.1f}")
