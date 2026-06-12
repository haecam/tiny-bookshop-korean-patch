"""
TMP Settings의 글로벌 fallback에 NanumPenScript 추가
- 모든 폰트가 한글 글리프 못 찾으면 여기로 와서 NanumPenScript로 렌더링
"""
import UnityPy, warnings, shutil, os, copy
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

NANUM_TMP_PID = 3949198417172128679  # NanumPenScript-Regular TMP FontAsset

env = UnityPy.load(BUNDLE)

# path_id -> name 매핑
pid_map = {}
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if hasattr(data, 'm_AtlasPopulationMode'):
            pid_map[obj.path_id] = data.m_Name

# TMP Settings 확인 및 수정
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if data.m_Name == 'TMP Settings':
            print('=== TMP Settings 현재 상태 ===')
            default_font = data.m_defaultFontAsset
            print(f'defaultFontAsset pathID: {default_font.m_PathID} -> {pid_map.get(default_font.m_PathID, "?")}')

            fallbacks = data.m_fallbackFontAssets or []
            print(f'글로벌 fallback 수: {len(fallbacks)}')
            for f in fallbacks:
                print(f'  {f.m_PathID} -> {pid_map.get(f.m_PathID, "?")}')

            # NanumPenScript가 이미 있는지 확인
            existing_pids = [f.m_PathID for f in fallbacks]
            if NANUM_TMP_PID in existing_pids:
                print('\n이미 Nanum 글로벌 fallback 있음')
                break

            # 기존 fallback에서 PPtr 복사해서 Nanum 추가
            if fallbacks:
                new_pptr = copy.copy(fallbacks[0])
            else:
                # fallback이 비어있으면 defaultFontAsset에서 복사
                new_pptr = copy.copy(default_font)

            new_pptr.m_PathID = NANUM_TMP_PID
            new_pptr.m_FileID = 0

            # 맨 앞에 추가 (최우선)
            data.m_fallbackFontAssets.insert(0, new_pptr)
            data.save()

            # 확인
            print(f'\n추가 후 fallback 수: {len(data.m_fallbackFontAssets)}')
            for f in data.m_fallbackFontAssets:
                marker = ' <-- Nanum 추가됨' if f.m_PathID == NANUM_TMP_PID else ''
                print(f'  {f.m_PathID} -> {pid_map.get(f.m_PathID, "?")}{marker}')
            break

with open(BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n저장 완료')
