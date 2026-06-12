"""ui 번들 raw bytes 분석 - 폰트 참조 위치 찾기"""
import UnityPy, warnings, struct
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/ui_scenes_scenes_all.bundle'
KNOWN = {
    -8380681616436361876: 'NanumPenScript-Regular EN',
     3949198417172128679: 'NanumPenScript-Regular',
     1598803222731014773: 'Vollkorn-Regular SDF EN',
    -3677393051516155784: 'Schoolbell-Regular EN',
}

env = UnityPy.load(BUNDLE)

# 모든 객체 타입 개요
type_counts = {}
for obj in env.objects:
    t = obj.type.name
    type_counts[t] = type_counts.get(t, 0) + 1
print('객체 타입:', dict(sorted(type_counts.items())))

# MonoBehaviour 이름 확인
print('\nMonoBehaviour 목록:')
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        try:
            d = obj.read()
            print(f'  pid={obj.path_id} name="{d.m_Name}"')
        except Exception as e:
            # raw로 이름 추출 시도
            try:
                raw = obj.get_raw_data()
                # 일반적으로 m_Name은 앞쪽에 있음
                if len(raw) > 8:
                    name_len = struct.unpack_from('<I', raw, 0)[0]
                    if 0 < name_len < 100:
                        name = raw[4:4+name_len].decode('utf-8', errors='ignore')
                        print(f'  pid={obj.path_id} raw_name="{name}" (err:{e})')
                    else:
                        print(f'  pid={obj.path_id} len={len(raw)} (err:{e})')
            except:
                print(f'  pid={obj.path_id} (unreadable)')
