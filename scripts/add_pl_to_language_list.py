"""
Polish(PL) 언어를 게임 언어 선택 목록에 추가 + UI 표시명 '한국어'로 변경

변경 내용:
1. gameinit_assets_all.bundle → LocalizationInfo.availableLanguages에 PL 추가
   (Korean OS에서도 자동 선택되도록 ko/ko-KR 알리아스 포함)
2. loca_en_assets_all.bundle → Language_PL 값: 'Polski' → '한국어'

결과:
  언어 선택 화면에 '한국어' 항목 등장
  선택 시 PL 번들 로드 → 우리가 주입한 한국어 책 제목/설명 표시
"""

import UnityPy, warnings, json, shutil, os, sys
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE_DIR   = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/'
GAMEINIT     = BUNDLE_DIR + 'gameinit_assets_all.bundle'
GAMEINIT_BAK = GAMEINIT + '.backup'
EN_BUNDLE    = BUNDLE_DIR + 'loca_en_assets_all.bundle'
EN_BACKUP    = BUNDLE_DIR + 'loca_en_assets_all.bundle.backup'

LOCA_INFO_PID = -7696966092034010949  # LocalizationInfo path_id

# ── 1. 백업 ─────────────────────────────────────────────────────────────────
if not os.path.exists(GAMEINIT_BAK):
    shutil.copy2(GAMEINIT, GAMEINIT_BAK)
    print(f'gameinit 백업 생성: {GAMEINIT_BAK}')
else:
    print('gameinit 백업 이미 존재')

# ── 2. gameinit 수정: PL을 availableLanguages에 추가 ─────────────────────
print('\n[1] gameinit → LocalizationInfo에 PL 추가...')
env_gi = UnityPy.load(GAMEINIT)

for obj in env_gi.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == LOCA_INFO_PID:
        raw = obj.read_typetree()
        langs = raw.get('availableLanguages', [])

        # 이미 PL이 있으면 스킵
        existing_ids = [l['LanguageID'] for l in langs]
        if 'PL' in existing_ids:
            print('  PL 이미 존재, 스킵')
        else:
            # EN 항목 구조를 템플릿으로 사용
            # Korean OS 자동 선택 + Polish 수동 선택 모두 지원
            pl_entry = {
                'LanguageID': 'PL',
                'additionalLanguageAliases': [
                    'ko', 'ko-KR', 'Korean', 'KO',     # 한국어 OS에서 자동 선택
                    'pl', 'pl-PL', 'Polish', 'POLISH'   # Polish alias
                ],
                'cultureInfoID': 'ko-KR',
                'LanguageName': {'key': 'Language_PL'},
                'enabled': 1,
                'forceDisableOnSwitch': 0,
                'percentSign': '',
                'charSpeedMultiplier': 1.0
            }
            langs.append(pl_entry)
            raw['availableLanguages'] = langs
            obj.save_typetree(raw)
            print(f'  PL 추가 완료 (총 {len(langs)}개 언어)')
            aliases = pl_entry['additionalLanguageAliases']
            print(f'  aliases: {aliases}')
        break

with open(GAMEINIT, 'wb') as f:
    f.write(env_gi.file.save())
print('  gameinit 저장 완료')

# ── 3. EN 번들 수정: Language_PL → '한국어' ──────────────────────────────
print('\n[2] EN 번들 → Language_PL을 한국어로 변경...')
env_en = UnityPy.load(EN_BUNDLE)

for obj in env_en.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        dic = raw.get('dictionary', {})
        keys = dic.get('keyData', [])
        vals = dic.get('valueData', [])

        if 'Language_PL' in keys:
            idx = keys.index('Language_PL')
            old_val = vals[idx]
            print(f'  기존 Language_PL: {old_val}')
            vals[idx] = {'strings': ['한국어']}
            dic['valueData'] = vals
            raw['dictionary'] = dic
            obj.save_typetree(raw)
            print(f'  → 한국어 로 변경 완료')
            break

with open(EN_BUNDLE, 'wb') as f:
    f.write(env_en.file.save())
print('  EN 번들 저장 완료')

# ── 4. 결과 검증 ────────────────────────────────────────────────────────────
print('\n=== 검증 ===')

env_gi2 = UnityPy.load(GAMEINIT)
for obj in env_gi2.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == LOCA_INFO_PID:
        raw = obj.read_typetree()
        langs = raw['availableLanguages']
        print(f'availableLanguages ({len(langs)}개):')
        for l in langs:
            print(f'  {l["LanguageID"]}', end='')
        print()
        pl_in = any(l['LanguageID'] == 'PL' for l in langs)
        print(f'PL 포함: {pl_in}')
        break

env_en2 = UnityPy.load(EN_BUNDLE)
for obj in env_en2.objects:
    if obj.type.name == 'MonoBehaviour':
        raw = obj.read_typetree()
        dic = raw.get('dictionary', {})
        keys = dic.get('keyData', [])
        vals = dic.get('valueData', [])
        if 'Language_PL' in keys:
            idx = keys.index('Language_PL')
            print(f'Language_PL 표시명: {vals[idx]}')
            break

print()
print('완료! 게임 재시작 후 언어 선택에서 한국어 확인')
