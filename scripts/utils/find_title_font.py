"""책 제목 텍스트 컴포넌트가 어느 폰트를 참조하는지 찾기"""
import UnityPy, warnings, os
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BASE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'

# TMP 폰트 path_id들 (알고있는 것)
KNOWN_FONTS = {
    -8380681616436361876: 'NanumPenScript-Regular EN',
    3949198417172128679:  'NanumPenScript-Regular',
    1598803222731014773:  'Vollkorn-Regular SDF EN',
    -3677393051516155784: 'Schoolbell-Regular EN',
    -3676257516557452952: 'Vollkorn-SemiBold SDF',
    8259034355840925290:  'DialogueScript EN',
    -1525049071735834178: 'Itim-Regular SDF EN',
    -3918262767295505232: 'caveat cyrillic SDF',
}

# 관심 번들들
bundles = [
    'basecontent_assets_all.bundle',
    'basesceneobjects_assets_all.bundle',
    'basecharacters_assets_all.bundle',
    'ui_scenes_scenes_all.bundle',
    'bookattributes_assets_all.bundle',
]

for bname in bundles:
    bpath = BASE + bname
    if not os.path.exists(bpath):
        continue
    try:
        env = UnityPy.load(bpath)
    except:
        continue

    found_any = False
    for obj in env.objects:
        if obj.type.name not in ('MonoBehaviour', 'GameObject', 'RectTransform'):
            continue
        try:
            d = obj.read()
            # TMP Text 컴포넌트는 m_fontAsset 또는 m_FontAsset 속성을 가짐
            font_ref = None
            if hasattr(d, 'm_fontAsset'):
                font_ref = d.m_fontAsset
            elif hasattr(d, 'm_FontAsset'):
                font_ref = d.m_FontAsset

            if font_ref and hasattr(font_ref, 'm_PathID') and font_ref.m_PathID != 0:
                fname = KNOWN_FONTS.get(font_ref.m_PathID, f'pid={font_ref.m_PathID}')
                name = getattr(d, 'm_Name', '?')
                if not found_any:
                    print(f'\n=== {bname} ===')
                    found_any = True
                print(f'  obj:{obj.path_id} "{name}" -> font: {fname}')
        except:
            pass
