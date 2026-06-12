"""
신문 관련 두 가지 수정:
  1. PL Yarn 테이블에 신문 기사 6줄 한국어 업데이트
  2. PL 번들 null 스프라이트 수정 (Newspaper_Title, Maps, New, Sold 등 12개)
     - EN CAB을 PL external fileID=5로 추가
     - fileID=0 스프라이트들을 fileID=5로 재설정
"""
import UnityPy, warnings, sys, copy
from UnityPy.files.SerializedFile import FileIdentifier

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
PL_BUNDLE  = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
EN_BUNDLE  = BUNDLE_DIR + 'loca_en_assets_all.bundle'

# EN CAB path (fileID=0 스프라이트들의 실제 위치)
EN_CAB_PATH = 'archive:/CAB-439cafc120cba2c9cd1e5a344624f41d/CAB-439cafc120cba2c9cd1e5a344624f41d'

YARN_PL_PID = -4050940925882462320  # Loca_Demo Yarn PL

# ── 신문 기사 한국어 번역 (6줄) ───────────────────────────────────────────────
NEWSPAPER_KO = {
    'line:04657e7': 'H1: 역대 최대 규모의 토요 장터',
    'line:02868a6': 'H2: 완벽한 날씨 덕분에 역대 최다 방문객 기대<br>',
    'line:0203b31': 'Body: 타임 마을의 <b>벼룩시장</b>에서 이번 주말도 방문객들은 마음껏 구경하고 흥정하며 쇼핑을 즐길 수 있습니다.',
    'line:04a93d6': 'Body: 빈티지 의류, 예술품, 식물, 생활용품, 레코드판 등 다양한 물품이 판매될 예정입니다. 이번엔 새 책들도 만날 수 있을지는 아직 미지수네요...',
    'line:06f9148': 'Body: <b>직원 팁:</b> 오전 9시~11시 사이에 방문하시면 가장 좋은 물건을 건질 수 있어요.',
    'line:0aca6b1': 'Author: 페른 에스트라다',
}

# ── PL 번들 로드 ──────────────────────────────────────────────────────────────
print('PL 번들 로드...')
env_pl = UnityPy.load(PL_BUNDLE)

# ── 1. Yarn PL 테이블 업데이트 ────────────────────────────────────────────────
print('\n[1] Yarn 테이블 신문 번역 업데이트...')
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == YARN_PL_PID:
        raw = obj.read_typetree()
        keys = raw['dictionary']['keyData']
        vals = raw['dictionary']['valueData']
        kv = dict(zip(keys, vals))

        updated = 0
        for k, ko_text in NEWSPAPER_KO.items():
            if k in kv:
                kv[k] = ko_text
                updated += 1
            else:
                keys.append(k)
                vals.append(ko_text)
                kv[k] = ko_text
                updated += 1

        raw['dictionary']['keyData']   = list(kv.keys())
        raw['dictionary']['valueData'] = list(kv.values())
        obj.save_typetree(raw)
        print(f'  {updated}줄 업데이트 완료 (총 {len(kv)}개)')
        break

# ── 2. null 스프라이트 수정 ───────────────────────────────────────────────────
print('\n[2] null 스프라이트 수정...')

# EN 번들에서 fileID=0 스프라이트 목록 수집
env_en = UnityPy.load(EN_BUNDLE)
en_internal_sprites = {}  # key -> pathID (fileID=0인 것들만)
for obj in env_en.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if raw.get('m_Name') == 'Loca_Base Sprites EN':
            for k, v in zip(raw['dictionary']['keyData'], raw['dictionary']['valueData']):
                if isinstance(v, dict) and v.get('m_FileID', -1) == 0 and v.get('m_PathID', 0) != 0:
                    en_internal_sprites[k] = v['m_PathID']
            break
print(f'  EN internal 스프라이트: {len(en_internal_sprites)}개')

# PL CAB 가져오기
pl_cab = None
for cab_name, cab in list(env_pl.files.values())[0].files.items():
    pl_cab = cab
    print(f'  PL CAB: {cab_name}')
    print(f'  현재 externals: {len(pl_cab.externals)}개')
    break

# EN CAB이 이미 external에 있는지 확인
existing_paths = {e.path for e in pl_cab.externals}
if EN_CAB_PATH not in existing_paths:
    new_ext = copy.copy(pl_cab.externals[0])
    object.__setattr__(new_ext, 'path', EN_CAB_PATH)
    object.__setattr__(new_ext, 'guid', b'\x00' * 16)
    object.__setattr__(new_ext, 'type', 0)
    object.__setattr__(new_ext, 'temp_empty', '')
    pl_cab.externals.append(new_ext)
    pl_cab.mark_changed()
    print(f'  EN CAB 추가 → fileID={len(pl_cab.externals)}')
else:
    print(f'  EN CAB 이미 존재')

# EN CAB의 fileID 결정 (1-indexed)
en_file_id = next(
    (i + 1 for i, e in enumerate(pl_cab.externals) if e.path == EN_CAB_PATH), None
)
print(f'  EN CAB fileID = {en_file_id}')

# PL Sprites 테이블에서 null 항목을 EN internal 스프라이트로 업데이트
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if 'Sprites' in raw.get('m_Name', '') and 'PL' in raw.get('m_Name', ''):
            keys = raw['dictionary']['keyData']
            vals = raw['dictionary']['valueData']
            updated = 0
            for i, (k, v) in enumerate(zip(keys, vals)):
                if k in en_internal_sprites:
                    if isinstance(v, dict) and v.get('m_PathID', 0) == 0:
                        vals[i] = {'m_FileID': en_file_id, 'm_PathID': en_internal_sprites[k]}
                        updated += 1
            raw['dictionary']['valueData'] = vals
            obj.save_typetree(raw)

            null_after = sum(1 for v in vals if isinstance(v, dict) and v.get('m_PathID', 0) == 0)
            print(f'  {raw["m_Name"]}: {updated}개 수정, null 잔여 {null_after}개')
            break

# ── 저장 ─────────────────────────────────────────────────────────────────────
print('\nPL 번들 저장...')
with open(PL_BUNDLE, 'wb') as f:
    f.write(env_pl.file.save())
print('저장 완료')

# ── 검증 ─────────────────────────────────────────────────────────────────────
print('\n=== 검증 ===')
env_v = UnityPy.load(PL_BUNDLE)
for obj in env_v.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if 'Sprites' in raw.get('m_Name', '') and 'PL' in raw.get('m_Name', ''):
            dic = raw['dictionary']
            null_count = sum(1 for v in dic['valueData'] if isinstance(v, dict) and v.get('m_PathID', 0) == 0)
            print(f'{raw["m_Name"]}: 총 {len(dic["keyData"])}개, null {null_count}개')
            for k, v in zip(dic['keyData'], dic['valueData']):
                if any(x in k for x in ('Newspaper', 'New', 'Sold', 'Map')):
                    status = '✓' if isinstance(v, dict) and v.get('m_PathID', 0) != 0 else '✗'
                    print(f'  {status} {k}')
            break
