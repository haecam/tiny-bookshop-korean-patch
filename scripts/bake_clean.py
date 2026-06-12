"""
한글 폰트 주입 (v2 - NotoSansJP 타겟)

핵심 변경:
  - NanumPenScript-Regular (글로벌 fallback): 백업 원본(128x128 placeholder)으로 복원
  - NotoSansJP-Regular SDF: 여기에 한글 폰트 굽기

이유:
  NanumPenScript-Regular는 Mansalva 기반 버텍스 왜곡 Material을 씀.
  여기에 한글을 구우면 SubMesh가 아닌 메인 Material로 렌더링되어 제목에서 깨짐.
  NotoSansJP는 자체 Material(깔끔 SDF)을 쓰고,
  NanumPenScript-Regular의 fallback 체인에 이미 포함되어 있어서
  한글이 NotoSansJP의 Material로 렌더링됨 → 버텍스 왜곡 없음.

fallback 체인:
  Primary font -> NanumPenScript-Regular (placeholder, 1자)
               -> ShantellSans
               -> NanumPenScript-Regular EN (Mansalva, Latin only)
               -> NotoSansJP-Regular SDF  ← 한글이 여기서 렌더링 (own Material)
               -> NotoSansSC-Regular SDF
"""
import UnityPy, warnings, json, shutil
import freetype, numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE  = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'
BACKUP  = BUNDLE + '.backup'

# ★ 메인 한글 폰트
KOREAN_FONT_PATH  = 'C:/Users/Bin/tb_korean_patch/fonts/Asummerflowertree.ttf'
# 커버 못하는 글자 fallback 폰트
FALLBACK_FONT_PATH = 'C:/Users/Bin/tb_korean_patch/fonts/NanumPenScript.ttf'

# ── 설정 ─────────────────────────────────────────────────────────────────────
GLYPH_PX   = 40
PADDING    = 6
ATLAS_W    = 2048
ATLAS_H    = 2048
POINT_SIZE = 90    # NotoSansJP-Regular m_PointSize  →  scale = 90/40 = 2.25

# path_ids
EN_FONT_PID    = -8380681616436361876   # NanumPenScript-Regular EN (FontAsset)
EN_TEX_PID     =  8014247901559850348   # NanumPenScript-Regular EN Atlas (Texture2D)
MAIN_FONT_PID  =  3949198417172128679   # NanumPenScript-Regular (placeholder 복원 대상)
MAIN_TEX_PID   = -3694003398043999321   # NanumPenScript-Regular Atlas (복원 대상)
NOTO_FONT_PID  = -3081274781549595770   # NotoSansJP-Regular SDF  ← 한글 주입 타겟
NOTO_TEX_PID   =  6366186281923113862   # NotoSansJP-Regular Atlas (Texture2D)

def clone(obj):
    new = object.__new__(type(obj))
    new.__dict__.update(obj.__dict__)
    return new

# ── 글자 수집 (모든 번역 파일 포함) ──────────────────────────────────────────
import ast as _ast
used = set()

# 책 번역
with open('C:/Users/Bin/tb_korean_patch/translation/to_translate_books_ko.json', encoding='utf-8') as f:
    for v in json.load(f).values():
        used.update(v)

# UI 번역 (메인/설정/추천)
with open('C:/Users/Bin/tb_korean_patch/translation/to_translate_main_ko.json', encoding='utf-8') as f:
    for val in json.load(f).values():
        parsed = _ast.literal_eval(val) if isinstance(val, str) else val
        for v in parsed.values():
            used.update(str(v))

# 대화 번역
with open('C:/Users/Bin/tb_korean_patch/translation/to_translate_dialogue_ko.json', encoding='utf-8') as f:
    for v in json.load(f).values():
        text = v.get('text', '') if isinstance(v, dict) else str(v)
        used.update(text)

hangul = sorted(c for c in used if '가' <= c <= '힣')
basics = sorted(set(' !"\'()*+,-./:;<=>?@[]_'
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'))
CHARS = sorted(set(hangul) | set(basics))
print(f'구울 글자: {len(CHARS)}자 (한글 {len(hangul)}자)')

# ── SDF 렌더링 ────────────────────────────────────────────────────────────────
face_main     = freetype.Face(KOREAN_FONT_PATH)
face_main.set_pixel_sizes(GLYPH_PX, GLYPH_PX)
face_fallback = freetype.Face(FALLBACK_FONT_PATH)
face_fallback.set_pixel_sizes(GLYPH_PX, GLYPH_PX)

atlas  = np.zeros((ATLAS_H, ATLAS_W), dtype=np.uint8)
packed = []
cx, cy, row_h = 0, 0, 0

print('SDF 렌더링 중...')
miss_count = 0
for ch in CHARS:
    cur = None
    for f in (face_main, face_fallback):
        try:
            f.load_char(ord(ch), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
            if f.glyph.bitmap.width > 0:
                cur = f; break
        except: pass
    if cur is None:
        miss_count += 1; continue
    g, bm = cur.glyph, cur.glyph.bitmap
    if bm.width == 0:
        continue
    buf  = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.width)
    ph, pw = bm.rows + 2*PADDING, bm.width + 2*PADDING
    pad2 = np.zeros((ph, pw), np.float32)
    pad2[PADDING:PADDING+bm.rows, PADDING:PADDING+bm.width] = buf / 255.0
    ins = distance_transform_edt(pad2  > 0.5)
    out = distance_transform_edt(pad2 <= 0.5)
    sdf = (np.clip((ins - out) / PADDING * 0.5 + 0.5, 0, 1) * 255).astype(np.uint8)
    if cx + pw > ATLAS_W:
        cx = 0; cy += row_h + 1; row_h = 0
    if cy + ph > ATLAS_H:
        print(f'  WARNING: atlas full at {len(packed)} chars'); break
    atlas[cy:cy+ph, cx:cx+pw] = sdf
    packed.append({
        'ch': ch, 'ax': cx, 'ay': cy, 'aw': pw, 'ah': ph,
        'advance': g.advance.x/64.0, 'bearing_x': float(g.bitmap_left),
        'bearing_y': float(g.bitmap_top), 'bm_w': float(bm.width), 'bm_h': float(bm.rows),
    })
    row_h = max(row_h, ph); cx += pw + 1

print(f'완료: {len(packed)}자 (미처리 {miss_count}자)')
Image.fromarray(atlas).save('C:/Users/Bin/tb_korean_patch/preview/atlas_clean_preview.png')
print('미리보기 저장: preview/atlas_clean_preview.png')

# ── 번들 수정 ─────────────────────────────────────────────────────────────────
scale = POINT_SIZE / GLYPH_PX
print(f'\nscale = {POINT_SIZE}/{GLYPH_PX} = {scale}')

env_mod = UnityPy.load(BUNDLE)
env_bak = UnityPy.load(BACKUP)

# ── 백업에서 raw 데이터 수집 ──────────────────────────────────────────────────
bak_bytes = {}  # pid -> raw bytes
for obj in env_bak.objects:
    if obj.path_id in (EN_FONT_PID, EN_TEX_PID, MAIN_FONT_PID, MAIN_TEX_PID):
        bak_bytes[obj.path_id] = obj.get_raw_data()

print(f'백업 데이터: {[(k, len(v)) for k, v in bak_bytes.items()]}')

# 템플릿 char/glyph (EN 폰트의 첫 번째 문자 사용)
bak_c0, bak_g0 = None, None
for obj in env_bak.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == EN_FONT_PID:
        d2 = obj.read()
        bak_c0, bak_g0 = d2.m_CharacterTable[0], d2.m_GlyphTable[0]
        break

# ── 1. NanumPenScript-Regular EN 원본 복원 ───────────────────────────────────
for obj in env_mod.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == EN_FONT_PID:
        obj.set_raw_data(bak_bytes[EN_FONT_PID])
        print('NanumPenScript-Regular EN: 원본 복원')
        break
for obj in env_mod.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == EN_TEX_PID:
        obj.set_raw_data(bak_bytes[EN_TEX_PID])
        print('NanumPenScript-Regular EN 텍스처: 원본 복원')
        break

# ── 2. NanumPenScript-Regular 원본 복원 (placeholder로 되돌리기) ─────────────
for obj in env_mod.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == MAIN_FONT_PID:
        obj.set_raw_data(bak_bytes[MAIN_FONT_PID])
        print('NanumPenScript-Regular: 원본 placeholder 복원')
        break
for obj in env_mod.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == MAIN_TEX_PID:
        obj.set_raw_data(bak_bytes[MAIN_TEX_PID])
        print('NanumPenScript-Regular 텍스처: 원본 복원')
        break

# ── 3. NotoSansJP-Regular SDF Atlas 텍스처 교체 ──────────────────────────────
for obj in env_mod.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == NOTO_TEX_PID:
        tex = obj.read()
        print(f'\nNotoSansJP 텍스처: {tex.m_Width}x{tex.m_Height} -> {ATLAS_W}x{ATLAS_H}')
        rgba = Image.new('RGBA', (ATLAS_W, ATLAS_H), (255, 255, 255, 0))
        rgba.putalpha(Image.fromarray(atlas, 'L'))
        tex.image = rgba
        tex.save()
        break

# ── 4. NotoSansJP-Regular SDF FontAsset 교체 ─────────────────────────────────
for obj in env_mod.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == NOTO_FONT_PID:
        d = obj.read()
        new_chars, new_glyphs = [], []
        for idx, p in enumerate(packed):
            nc = clone(bak_c0)
            nc.m_Unicode    = ord(p['ch'])
            nc.m_GlyphIndex = idx
            nc.m_Scale      = 1.0
            new_chars.append(nc)

            ng = clone(bak_g0)
            ng.m_Index      = idx
            ng.m_Scale      = 1.0
            ng.m_AtlasIndex = 0

            nm = clone(bak_g0.m_Metrics)
            nm.m_Width               = p['bm_w']      * scale
            nm.m_Height              = p['bm_h']      * scale
            nm.m_HorizontalBearingX  = p['bearing_x'] * scale
            nm.m_HorizontalBearingY  = p['bearing_y'] * scale
            nm.m_HorizontalAdvance   = p['advance']   * scale
            ng.m_Metrics = nm

            nr = clone(bak_g0.m_GlyphRect)
            # TMP 표준: GlyphRect = 글리프 내부 영역 (패딩 제외)
            # TMP가 m_AtlasPadding 만큼 UV를 추가 확장해서 SDF 그라디언트 캡처
            nr.m_X      = p['ax'] + PADDING
            nr.m_Y      = ATLAS_H - (p['ay'] + PADDING) - int(p['bm_h'])
            nr.m_Width  = int(p['bm_w'])
            nr.m_Height = int(p['bm_h'])
            ng.m_GlyphRect = nr

            new_glyphs.append(ng)

        d.m_AtlasPopulationMode = 0          # Static
        d.m_AtlasWidth          = ATLAS_W
        d.m_AtlasHeight         = ATLAS_H
        d.m_AtlasPadding        = PADDING    # 우리 SDF padding과 일치시킴 (원본=9, 우리=6)
        d.m_CharacterTable      = new_chars
        d.m_GlyphTable          = new_glyphs
        d.save()
        print(f'NotoSansJP-Regular: {len(new_chars)}자 저장 (Static 모드)')
        break

with open(BUNDLE, 'wb') as f:
    f.write(env_mod.file.save())
print('\n완료!')
print('- 한글 -> NotoSansJP Material (버텍스 왜곡 없음)')
print('- 제목 한글도 깔끔하게 렌더링됨')
