"""
PL 번들 Loca_Base Sprites PL 수정:
  - Genre 아이콘 흰 박스 → 실제 스프라이트로 교체
  - PL 번들에 외부 스프라이트 번들 dependency 추가 (fileID 2,3,4)
  - EN의 스프라이트 참조를 PL에 복사

EN external 매핑:
  fileID=2: duplicateassetisolation1 → Genre 아이콘 (UI_BookIcon_*)
  fileID=3: gameinit               → SplashLogo
  fileID=4: duplicateassetisolation5 → MenuLogo, TB logos
"""

import UnityPy, warnings, sys, shutil, os, copy
from UnityPy.files.SerializedFile import FileIdentifier
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
PL_BUNDLE  = BUNDLE_DIR + 'loca_pl_assets_all.bundle'
EN_BUNDLE  = BUNDLE_DIR + 'loca_en_assets_all.bundle'

SPRITES_PL_PID = -567524315626770795  # Loca_Base Sprites PL 확인 필요

# ── 1. EN에서 스프라이트 참조 + externals 읽기 ───────────────────────────────
print('EN 번들에서 스프라이트 참조 읽기...')
env_en = UnityPy.load(EN_BUNDLE)

en_sprite_keys = []
en_sprite_vals = []
for obj in env_en.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if raw.get('m_Name') == 'Loca_Base Sprites EN':
            en_sprite_keys = raw['dictionary']['keyData']
            en_sprite_vals = raw['dictionary']['valueData']
            print(f'  EN Sprites: {len(en_sprite_keys)}개')
            break

# EN externals
en_externals = []
for cab_name, cab in list(env_en.files.values())[0].files.items():
    en_externals = cab.externals
    break
print(f'  EN externals: {len(en_externals)}개')
for i, e in enumerate(en_externals):
    print(f'    [{i+1}]: {e.path.split("/")[-1]}')

# ── 2. PL 번들 수정 ──────────────────────────────────────────────────────────
print('\nPL 번들 수정 중...')
env_pl = UnityPy.load(PL_BUNDLE)

# PL Sprites PID 찾기
sprites_pl_pid = None
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if 'Sprites' in raw.get('m_Name', '') and 'PL' in raw.get('m_Name', ''):
            sprites_pl_pid = obj.path_id
            print(f'  PL Sprites pid={sprites_pl_pid}: {raw["m_Name"]}')
            break

# PL CAB 가져오기
pl_cab = None
for cab_name, cab in list(env_pl.files.values())[0].files.items():
    pl_cab = cab
    print(f'  PL CAB: {cab_name}')
    print(f'  현재 externals: {len(pl_cab.externals)}개')
    for i, e in enumerate(pl_cab.externals):
        print(f'    [{i+1}]: {e.path.split("/")[-1]}')
    break

# ── 3. 누락된 externals 추가 (fileID 2, 3, 4) ────────────────────────────────
print('\nexternal dependency 추가...')
existing_paths = {e.path for e in pl_cab.externals}

for i, en_ext in enumerate(en_externals):
    file_id = i + 2  # EN의 fileID=2,3,4 (index 1,2,3)
    if i == 0:
        continue  # fileID=1은 이미 있음

    if en_ext.path not in existing_paths:
        new_ext = copy.copy(pl_cab.externals[0])
        object.__setattr__(new_ext, 'path', en_ext.path)
        object.__setattr__(new_ext, 'guid', b'\x00' * 16)
        object.__setattr__(new_ext, 'type', 0)
        object.__setattr__(new_ext, 'temp_empty', '')
        pl_cab.externals.append(new_ext)
        pl_cab.mark_changed()
        existing_paths.add(en_ext.path)
        print(f'  fileID={len(pl_cab.externals)} 추가: {en_ext.name}')
    else:
        print(f'  fileID={file_id} 이미 존재: {en_ext.name}')

print(f'  추가 후 PL externals: {len(pl_cab.externals)}개')

# ── 4. PL Sprite 테이블 업데이트 (EN 참조 복사) ──────────────────────────────
print('\nSprite 테이블 업데이트...')
for obj in env_pl.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == sprites_pl_pid:
        raw = obj.read_typetree()
        print(f'  기존: {len(raw["dictionary"]["keyData"])}개')

        # EN의 모든 스프라이트 참조 복사 (fileID=0 제외 - 번들 내장 스프라이트, null 유지)
        new_keys = list(raw['dictionary']['keyData'])
        new_vals = list(raw['dictionary']['valueData'])
        existing_key_set = set(new_keys)

        updated = 0
        added = 0

        for k, v in zip(en_sprite_keys, en_sprite_vals):
            if not isinstance(v, dict):
                continue
            fid = v.get('m_FileID', 0)
            pid = v.get('m_PathID', 0)

            # fileID=0 은 번들 내장 스프라이트 → null 유지 (PL에 없음)
            if fid == 0:
                continue

            if k in existing_key_set:
                idx = new_keys.index(k)
                old_pid = new_vals[idx].get('m_PathID', 0) if isinstance(new_vals[idx], dict) else 0
                if old_pid == 0:  # null이었던 것만 업데이트
                    new_vals[idx] = {'m_FileID': fid, 'm_PathID': pid}
                    updated += 1
            else:
                new_keys.append(k)
                new_vals.append({'m_FileID': fid, 'm_PathID': pid})
                added += 1

        raw['dictionary']['keyData']   = new_keys
        raw['dictionary']['valueData'] = new_vals
        obj.save_typetree(raw)
        print(f'  업데이트: {updated}개 null→참조, 추가: {added}개 새 키')
        print(f'  총: {len(new_keys)}개')
        break

# ── 5. 저장 ──────────────────────────────────────────────────────────────────
print('\nPL 번들 저장...')
with open(PL_BUNDLE, 'wb') as f:
    f.write(env_pl.file.save())
print('저장 완료')

# ── 6. 검증 ──────────────────────────────────────────────────────────────────
print('\n=== 검증 ===')
env_v = UnityPy.load(PL_BUNDLE)
for cab_name, cab in list(env_v.files.values())[0].files.items():
    print(f'externals ({len(cab.externals)}개):')
    for i, e in enumerate(cab.externals):
        print(f'  [{i+1}]: {e.path.split("/")[-1]}')
    break

for obj in env_v.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        if 'Sprites' in raw.get('m_Name','') and 'PL' in raw.get('m_Name',''):
            dic = raw['dictionary']
            null_count = sum(1 for v in dic['valueData']
                           if isinstance(v,dict) and v.get('m_PathID',0) == 0)
            nonzero = len(dic['keyData']) - null_count
            print(f'\n{raw["m_Name"]}: 총 {len(dic["keyData"])}개')
            print(f'  실제 참조: {nonzero}개  |  null: {null_count}개')
            print('  Genre 항목:')
            for k, v in zip(dic['keyData'], dic['valueData']):
                if 'Genre_' in k:
                    fid = v.get('m_FileID','?') if isinstance(v,dict) else '?'
                    pid = v.get('m_PathID','?') if isinstance(v,dict) else '?'
                    status = '✓' if pid != 0 else '✗'
                    print(f'    {status} {k}: fileID={fid}, pathID={pid}')
            break
