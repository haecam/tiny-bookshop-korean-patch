import UnityPy, warnings, sys, io
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'   # 실제 버전으로 수정

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

env = UnityPy.load(BUNDLE)

pid_to_name = {}
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if hasattr(data, 'm_AtlasPopulationMode'):
            pid_to_name[obj.path_id] = data.m_Name

print('=== NanumPenScript-Regular 상태 ===')
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if data.m_Name == 'NanumPenScript-Regular':
            print(f'  mode: {data.m_AtlasPopulationMode}  (1=Dynamic 이어야 함)')
            print(f'  SourceFontFile pathID: {data.m_SourceFontFile.m_PathID}  (2327579649561429402 이어야 함)')
            print(f'  chars: {len(data.m_CharacterTable)}')
            break

print()
print('=== Vollkorn-Regular SDF fallback 목록 ===')
NANUM_PID = 3949198417172128679
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if data.m_Name == 'Vollkorn-Regular SDF':
            fb = data.m_FallbackFontAssetTable or []
            for f in fb:
                name = pid_to_name.get(f.m_PathID, '(unknown)')
                marker = '  <-- Nanum 추가됨' if f.m_PathID == NANUM_PID else ''
                print(f'  {f.m_PathID}: {name}{marker}')
            break
