"""저장된 FontAsset 검증"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

env = UnityPy.load(BUNDLE)
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        if d.m_Name == 'NanumPenScript-Regular EN':
            print(f'== NanumPenScript-Regular EN ==')
            print(f'  mode:  {d.m_AtlasPopulationMode} (0=Static)')
            print(f'  atlas: {d.m_AtlasWidth}x{d.m_AtlasHeight}')
            print(f'  chars: {len(d.m_CharacterTable)}')
            print(f'  glyphs:{len(d.m_GlyphTable)}')

            # 한글 포함 여부 확인
            unicodes = [c.m_Unicode for c in d.m_CharacterTable]
            hangul_count = sum(1 for u in unicodes if 0xAC00 <= u <= 0xD7A3)
            print(f'  한글 수: {hangul_count}')
            if hangul_count:
                sample = [chr(u) for u in unicodes if 0xAC00 <= u <= 0xD7A3][:10]
                print(f'  샘플: {"".join(sample)}')

            # glyph rect 확인
            g0 = d.m_GlyphTable[0]
            r = g0.m_GlyphRect
            print(f'  glyph[0] rect: ({r.m_X},{r.m_Y}) {r.m_Width}x{r.m_Height}')
            m = g0.m_Metrics
            print(f'  glyph[0] metrics: adv={m.m_HorizontalAdvance:.1f}')

            # 텍스처 크기
            tex_pid = d.m_AtlasTextures[0].m_PathID
            for obj2 in env.objects:
                if obj2.type.name == 'Texture2D' and obj2.path_id == tex_pid:
                    tex = obj2.read()
                    print(f'  texture: {tex.m_Width}x{tex.m_Height} fmt={tex.m_TextureFormat}')
            break
