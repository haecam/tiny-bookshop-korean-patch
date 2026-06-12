"""ui_scenes 번들에서 책 제목 관련 컴포넌트 구조 파악"""
import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/ui_scenes_scenes_all.bundle'
KNOWN = {
    -8380681616436361876: 'NanumPenScript-Regular EN',
     3949198417172128679: 'NanumPenScript-Regular',
     1598803222731014773: 'Vollkorn-Regular SDF EN',
    -3677393051516155784: 'Schoolbell-Regular EN',
    -1525049071735834178: 'Itim-Regular SDF EN',
}

env = UnityPy.load(BUNDLE)

TARGET_PID = -589433345097503893

for obj in env.objects:
    if obj.path_id != TARGET_PID:
        continue
    d = obj.read()
    print(f'type: {obj.type.name}')
    print(f'name: {d.m_Name}')
    attrs = [a for a in dir(d) if not a.startswith('_')]
    print(f'attrs: {attrs}')
    for a in attrs:
        try:
            v = getattr(d, a)
            vs = str(v)
            # PPtr 참조면 path_id 확인
            if hasattr(v, 'm_PathID'):
                vname = KNOWN.get(v.m_PathID, f'pid={v.m_PathID}')
                print(f'  {a}: PPtr -> {vname}')
            elif isinstance(v, list) and v and hasattr(v[0], 'm_PathID'):
                print(f'  {a}: [{len(v)} PPtrs]')
                for i, item in enumerate(v[:5]):
                    iname = KNOWN.get(item.m_PathID, f'pid={item.m_PathID}')
                    print(f'    [{i}] -> {iname}')
            elif 'font' in a.lower() or 'Font' in a:
                print(f'  {a}: {vs[:100]}')
        except:
            pass
