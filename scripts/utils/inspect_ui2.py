"""ui_scenes에서 NanumPenScript-Regular EN 참조하는 객체 분석"""
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
EN_PID = -8380681616436361876

env = UnityPy.load(BUNDLE)

# raw bytes로 참조 찾기
for obj in env.objects:
    try:
        raw = obj.get_raw_data()
        en_bytes = EN_PID.to_bytes(8, 'little', signed=True)
        if en_bytes not in raw:
            continue
        print(f'type={obj.type.name} path_id={obj.path_id}')
        if obj.type.name == 'MonoBehaviour':
            try:
                d = obj.read()
                print(f'  name={d.m_Name}')
                # fontAsset 속성 찾기
                for a in dir(d):
                    if 'font' in a.lower():
                        v = getattr(d, a, None)
                        if v is not None:
                            if hasattr(v, 'm_PathID'):
                                fname = KNOWN.get(v.m_PathID, f'pid={v.m_PathID}')
                                print(f'  {a} -> {fname}')
                            else:
                                print(f'  {a} = {str(v)[:80]}')
            except Exception as e:
                print(f'  (read error: {e})')
    except:
        pass
