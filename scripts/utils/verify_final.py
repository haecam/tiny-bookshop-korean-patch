"""최종 상태 검증"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'
env = UnityPy.load(BUNDLE)

pid_name = {}
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        try:
            d = obj.read()
            pid_name[obj.path_id] = d.m_Name
        except:
            pass

check_fonts = {
    3949198417172128679:   'NanumPenScript-Regular (TMP Settings fallback)',
    -8380681616436361876:  'NanumPenScript-Regular EN',
}

for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        pid = obj.path_id
        if pid in check_fonts:
            d = obj.read()
            hangul = sum(1 for c in d.m_CharacterTable if 0xAC00 <= c.m_Unicode <= 0xD7A3)
            sample = ''.join(chr(c.m_Unicode) for c in d.m_CharacterTable if 0xAC00 <= c.m_Unicode <= 0xD7A3)[:8]
            tex_pid = d.m_AtlasTextures[0].m_PathID if d.m_AtlasTextures else '?'
            print(f'{check_fonts[pid]}:')
            print(f'  mode={d.m_AtlasPopulationMode} atlas={d.m_AtlasWidth}x{d.m_AtlasHeight}')
            print(f'  chars={len(d.m_CharacterTable)} 한글={hangul} 샘플="{sample}"')
            print(f'  atlas_tex_pid={tex_pid}')
            # 텍스처 크기 확인
            for obj2 in env.objects:
                if obj2.type.name == 'Texture2D' and obj2.path_id == tex_pid:
                    t = obj2.read()
                    print(f'  텍스처: {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat}')
            print()

# TMP Settings fallback 확인
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        d = obj.read()
        if d.m_Name == 'TMP Settings':
            falls = d.m_fallbackFontAssets or []
            print(f'TMP Settings 글로벌 fallback ({len(falls)}개):')
            for fb in falls:
                mode = '?'
                chars = '?'
                for obj2 in env.objects:
                    if obj2.type.name == 'MonoBehaviour' and obj2.path_id == fb.m_PathID:
                        d2 = obj2.read()
                        mode = d2.m_AtlasPopulationMode
                        chars = len(d2.m_CharacterTable)
                        break
                print(f'  -> {pid_name.get(fb.m_PathID,"?")} | mode={mode} | chars={chars}')
