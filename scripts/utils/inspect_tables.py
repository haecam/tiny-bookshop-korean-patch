import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

# 백업에서 로드 (원본 구조 확인용)
BACKUP = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle.backup'
env = UnityPy.load(BACKUP)

# NanumPenScript EN (217자 있는 완성된 버전) 구조 확인
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if data.m_Name == 'NanumPenScript-Regular EN':
            print('=== NanumPenScript-Regular EN (완성된 버전) ===')
            print(f'mode: {data.m_AtlasPopulationMode}')
            print(f'atlas: {data.m_AtlasWidth}x{data.m_AtlasHeight}')
            print(f'char_table 크기: {len(data.m_CharacterTable)}')
            print(f'glyph_table 크기: {len(data.m_GlyphTable)}')

            # char_table 구조
            if data.m_CharacterTable:
                c = data.m_CharacterTable[0]
                print()
                print('char_table[0] attrs:', [a for a in dir(c) if not a.startswith('_')])
                print('char_table[0] unicode:', c.m_Unicode)
                print('char_table[0] glyphIndex:', c.m_GlyphIndex)
                print('char_table[0] scale:', c.m_Scale)

            # glyph_table 구조
            if data.m_GlyphTable:
                g = data.m_GlyphTable[0]
                print()
                print('glyph_table[0] attrs:', [a for a in dir(g) if not a.startswith('_')])
                print('glyph_table[0] index:', g.m_Index)
                m = g.m_Metrics
                print('glyph metrics attrs:', [a for a in dir(m) if not a.startswith('_')])
                print('  width:', m.m_Width)
                print('  height:', m.m_Height)
                print('  bearingX:', m.m_HorizontalBearingX)
                print('  bearingY:', m.m_HorizontalBearingY)
                print('  advance:', m.m_HorizontalAdvance)
                r = g.m_GlyphRect
                print('glyph rect attrs:', [a for a in dir(r) if not a.startswith('_')])
                print('  x:', r.m_X, 'y:', r.m_Y, 'w:', r.m_Width, 'h:', r.m_Height)

            # 아틀라스 텍스처 포맷
            tex_pid = data.m_AtlasTextures[0].m_PathID if data.m_AtlasTextures else None
            break

print()
print(f'atlas texture path_id: {tex_pid}')
for obj in env.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == tex_pid:
        tex = obj.read()
        print(f'texture: {tex.m_Name} {tex.m_Width}x{tex.m_Height} format={tex.m_TextureFormat}')
        break
