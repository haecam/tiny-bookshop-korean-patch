import UnityPy, warnings
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

env = UnityPy.load(BUNDLE)

for obj in env.objects:
    if obj.type.name == 'Font':
        data = obj.read()
        if data.m_Name == 'NanumPenScript-Regular':
            fdata = bytes(data.m_FontData)
            print('폰트 데이터 크기:', len(fdata), 'bytes')
            magic = fdata[:4]
            print('매직 바이트:', magic.hex())

            is_valid = (magic == bytes([0,1,0,0]) or  # TTF
                        magic == b'OTTO' or             # OTF
                        magic == b'true' or             # TTF variant
                        magic[:2] == b'\x1f\x8b')       # gzip

            if is_valid:
                print('유효한 폰트 파일!')
                with open('C:/Users/Bin/NanumPenScript.ttf', 'wb') as f:
                    f.write(fdata)
                print('저장: C:/Users/Bin/NanumPenScript.ttf')
            else:
                print('비정상 - 폰트 데이터 없거나 압축됨')
            break
