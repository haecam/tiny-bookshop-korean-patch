"""
UnityPy save 신뢰성 진단:
NanumPenScript-Regular의 실제 직렬화 바이트를 확인해서
Dynamic 설정이 제대로 쓰여졌는지 검증
"""
import UnityPy, warnings, struct
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'
BACKUP = BUNDLE + '.backup'

# 백업에서 원본 Nanum 바이트 읽기
env_orig = UnityPy.load(BACKUP)
orig_bytes = None
for obj in env_orig.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if data.m_Name == 'NanumPenScript-Regular':
            orig_bytes = obj.get_raw_data()
            print(f'원본 raw data 크기: {len(orig_bytes)}')
            # atlasPopulationMode 위치 찾기 (int = 4 bytes, value=0)
            # mode=0 이 어디있는지 찾아보기
            break

# 수정된 번들에서 바이트 읽기
env_mod = UnityPy.load(BUNDLE)
mod_bytes = None
for obj in env_mod.objects:
    if obj.type.name == 'MonoBehaviour':
        data = obj.read()
        if data.m_Name == 'NanumPenScript-Regular':
            mod_bytes = obj.get_raw_data()
            print(f'수정본 raw data 크기: {len(mod_bytes)}')
            print(f'mode 값 (읽기): {data.m_AtlasPopulationMode}')
            print(f'sourceFontFile pathID (읽기): {data.m_SourceFontFile.m_PathID}')
            break

if orig_bytes and mod_bytes:
    print(f'\n바이트 변경 위치:')
    count = 0
    for i, (a, b) in enumerate(zip(orig_bytes, mod_bytes)):
        if a != b:
            print(f'  offset {i:5d}: {a:3d} -> {b:3d}')
            count += 1
            if count > 30:
                print(f'  ... (총 {sum(1 for x,y in zip(orig_bytes,mod_bytes) if x!=y)}개 다름)')
                break

    # 길이 차이
    if len(orig_bytes) != len(mod_bytes):
        print(f'크기 변화: {len(orig_bytes)} -> {len(mod_bytes)} ({len(mod_bytes)-len(orig_bytes):+d} bytes)')
