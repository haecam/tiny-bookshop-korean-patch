"""loca_en 번들에서 번역 안된 항목 찾기"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

LOCA = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/loca_en_assets_all.bundle'
env = UnityPy.load(LOCA)

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    try:
        d = obj.read()
        if not hasattr(d, 'dictionary'):
            continue
        keys = list(d.dictionary.keyData)
        vals = list(d.dictionary.valueData)
    except:
        continue

    if 'Books' not in d.m_Name:
        continue

    # 번역 안된 것 (한글 없이 영문 그대로) 찾기
    untranslated = []
    has_newline  = []
    for k, v in zip(keys, vals):
        vstr = str(v)
        # StringProvider에서 strings 배열 추출
        if 'strings=' in vstr:
            import re
            m = re.search(r"strings=\['(.+?)'\]", vstr, re.DOTALL)
            if m:
                text = m.group(1)
            else:
                text = vstr
        else:
            text = vstr

        is_korean = any('가' <= c <= '힣' for c in text)
        if not is_korean:
            untranslated.append((str(k), text[:60]))
        if '\n' in str(k) or '\n' in text:
            has_newline.append((str(k), text[:60]))

    print(f'=== {d.m_Name} ===')
    print(f'  총 {len(keys)}개, 미번역 {len(untranslated)}개, 줄바꿈 포함 {len(has_newline)}개')
    if untranslated:
        print('  미번역 샘플:')
        for k, v in untranslated[:5]:
            print(f'    {k[:50]}: {v[:50]}')
    if has_newline:
        print('  줄바꿈 샘플:')
        for k, v in has_newline[:5]:
            print(f'    {repr(k[:40])}: {repr(v[:60])}')
