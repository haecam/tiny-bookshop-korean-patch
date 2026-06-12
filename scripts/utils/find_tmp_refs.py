"""모든 번들에서 NanumPenScript-Regular EN 참조 찾기 - 안전하게"""
import UnityPy, warnings, os, json
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BASE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'

# 알려진 TMP 폰트 path_id
TARGET_PIDS = {
    -8380681616436361876: 'NanumPenScript-Regular EN',
     3949198417172128679: 'NanumPenScript-Regular',
     1598803222731014773: 'Vollkorn-Regular SDF EN',
    -3677393051516155784: 'Schoolbell-Regular EN',
    -1525049071735834178: 'Itim-Regular SDF EN',
     8259034355840925290: 'DialogueScript EN',
}

skip = {'loca_', 'audio_', 'shader', 'duplicat', 'isolat', 'monoscript', 'unitybuiltin', 'backup'}
results = {}

for fname in sorted(os.listdir(BASE)):
    if not fname.endswith('.bundle'):
        continue
    if any(s in fname for s in skip):
        continue

    bpath = os.path.join(BASE, fname)
    try:
        env = UnityPy.load(bpath)
    except:
        continue

    bundle_results = []
    for obj in env.objects:
        try:
            raw = obj.get_raw_data()
            # raw bytes에서 path_id 패턴 찾기 (binary search)
            for pid, pname in TARGET_PIDS.items():
                pid_bytes = pid.to_bytes(8, 'little', signed=True)
                if pid_bytes in raw:
                    bundle_results.append(f'  obj_type={obj.type.name} pid={obj.path_id} -> refs {pname}')
        except:
            pass

    if bundle_results:
        print(f'\n=== {fname} ===')
        seen = set()
        for r in bundle_results:
            if r not in seen:
                print(r)
                seen.add(r)

print('\n완료')
