"""책 제목 TMP 컴포넌트 찾기 - 한 번에 하나씩"""
import UnityPy, warnings, os, sys
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BASE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'

KNOWN_FONTS = {
    -8380681616436361876: 'NanumPenScript-Regular EN',
     3949198417172128679: 'NanumPenScript-Regular',
     1598803222731014773: 'Vollkorn-Regular SDF EN',
    -3677393051516155784: 'Schoolbell-Regular EN',
    -3676257516557452952: 'Vollkorn-SemiBold SDF',
     8259034355840925290: 'DialogueScript EN',
    -1525049071735834178: 'Itim-Regular SDF EN',
}

bname = sys.argv[1] if len(sys.argv) > 1 else 'basecontent_assets_all.bundle'
bpath = BASE + bname
print(f'검사: {bname}')
env = UnityPy.load(bpath)

results = {}
for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    try:
        d = obj.read()
        for attr in ('m_fontAsset', 'm_FontAsset'):
            ref = getattr(d, attr, None)
            if ref and hasattr(ref, 'm_PathID') and ref.m_PathID != 0:
                fname = KNOWN_FONTS.get(ref.m_PathID, f'unknown({ref.m_PathID})')
                name  = getattr(d, 'm_Name', '?')
                results[obj.path_id] = (name, fname, ref.m_PathID)
                break
    except:
        pass

for pid, (name, fname, fpid) in sorted(results.items(), key=lambda x: x[1][1]):
    print(f'  path_id={pid} name="{name}" -> {fname}')
print(f'총 {len(results)}개 TMP 컴포넌트')
