"""loca_en 번들 한글 적용 여부 확인"""
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
        keys   = list(d.dictionary.keyData)
        values = list(d.dictionary.valueData)
        # 한글 포함된 항목 샘플링
        korean = [(k, v) for k, v in zip(keys, values) if any('가' <= c <= '힣' for c in v)]
        if korean:
            print(f'테이블 "{d.m_Name}": 전체 {len(keys)}개 중 한글 {len(korean)}개')
            for k, v in korean[:5]:
                print(f'  {repr(k)}: {repr(v[:40])}')
            print()
    except:
        pass
