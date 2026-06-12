import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

LOCA = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/loca_en_assets_all.bundle'
env = UnityPy.load(LOCA)

total_mb = 0
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour':
        try:
            d = obj.read()
            name = d.m_Name
            attrs = [a for a in dir(d) if not a.startswith('_')][:10]
            # dictionary 구조 확인
            if hasattr(d, 'dictionary'):
                dic = d.dictionary
                dic_attrs = [a for a in dir(dic) if not a.startswith('_')]
                print(f'{name}: dic attrs = {dic_attrs[:8]}')
                if hasattr(dic, 'keyData'):
                    keys = list(dic.keyData)
                    vals = list(dic.valueData)
                    ko = [(k,v) for k,v in zip(keys,vals) if any('가'<=c<='힣' for c in str(v))]
                    print(f'  total={len(keys)} korean={len(ko)}')
                    if ko:
                        k,v = ko[0]
                        print(f'  sample: {repr(str(k)[:30])} -> {repr(str(v)[:50])}')
            elif hasattr(d, 'LanguageID'):
                print(f'{name}: LanguageID={d.LanguageID}')
            else:
                print(f'{name}: attrs={attrs}')
        except Exception as e:
            print(f'  ERR: {e}')
