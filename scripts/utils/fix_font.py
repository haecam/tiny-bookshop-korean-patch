import UnityPy, warnings, shutil, os, copy
warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2022.3.0f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'
BACKUP = BUNDLE + '.backup'

NANUM_FONT_FILE_PID  = 2327579649561429402   # Font (실제 .ttf 파일)
NANUM_TMP_ASSET_PID  = 3949198417172128679   # TMP FontAsset (MonoBehaviour)

# 한글이 깨지는 EN 폰트들 (fallback에 Nanum 추가 대상)
TARGET_FONTS = [
    'Vollkorn-Regular SDF',
    'Vollkorn-Regular SDF EN',
    'Vollkorn-SemiBold SDF',
    'Vollkorn-Italic SDF',
    'Vollkorn-SemiBoldItalic SDF',
    'Itim-Regular SDF EN',
    'Bristol SDF',
    'DialogueScript EN',
    'Schoolbell-Regular EN',
]

# 백업
if not os.path.exists(BACKUP):
    shutil.copy2(BUNDLE, BACKUP)
    print('백업 생성:', BACKUP)

env = UnityPy.load(BUNDLE)

nanum_pptr_template = None   # 기존 PPtr 복사해서 템플릿으로 사용

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    data = obj.read()
    if not hasattr(data, 'm_AtlasPopulationMode'):
        continue

    # ── 1. NanumPenScript-Regular: Static → Dynamic ──────────────────────
    if data.m_Name == 'NanumPenScript-Regular':
        print(f'[Nanum] mode: {data.m_AtlasPopulationMode} -> 1 (Dynamic)')
        data.m_AtlasPopulationMode = 1

        # source font file 참조 설정
        src = data.m_SourceFontFile
        print(f'  before SourceFontFile pathID: {src.m_PathID}')
        src.m_PathID = NANUM_FONT_FILE_PID
        src.m_FileID = 0
        print(f'  after  SourceFontFile pathID: {src.m_PathID}')

        # 기존 1개짜리 static atlas 초기화
        data.m_CharacterTable = []
        data.m_GlyphTable = []
        data.m_AtlasWidth  = 1024
        data.m_AtlasHeight = 1024
        data.m_AtlasTextureIndex = 0

        # fallback PPtr 템플릿 추출 (나중에 다른 폰트에 추가용)
        if data.m_FallbackFontAssetTable:
            nanum_pptr_template = copy.copy(data.m_FallbackFontAssetTable[0])

        data.save()
        print('  [OK] NanumPenScript-Regular -> Dynamic')

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    data = obj.read()
    if not hasattr(data, 'm_FallbackFontAssetTable'):
        continue
    if data.m_Name not in TARGET_FONTS:
        continue

    # ── 2. EN 폰트들 fallback 맨 앞에 Nanum 추가 ─────────────────────────
    existing_pids = [f.m_PathID for f in (data.m_FallbackFontAssetTable or [])]
    if NANUM_TMP_ASSET_PID in existing_pids:
        print(f'[Skip] {data.m_Name}: 이미 Nanum fallback 있음')
        continue

    # PPtr 생성 - 기존 fallback 항목을 복사해서 pathID만 교체
    if data.m_FallbackFontAssetTable:
        new_pptr = copy.copy(data.m_FallbackFontAssetTable[0])
    elif nanum_pptr_template:
        new_pptr = copy.copy(nanum_pptr_template)
    else:
        print(f'[WARN] {data.m_Name}: PPtr 템플릿 없음, 스킵')
        continue

    new_pptr.m_PathID = NANUM_TMP_ASSET_PID
    new_pptr.m_FileID = 0

    # 맨 앞에 삽입 (우선순위 높게)
    data.m_FallbackFontAssetTable.insert(0, new_pptr)
    data.save()
    print(f'[OK] {data.m_Name}: Nanum fallback 추가')

# 저장
with open(BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n저장 완료:', BUNDLE)
