"""
memomentKkukkkuk → NotoSansJP-SemiBold (UI 전반)
KCCPakKyongni    → NotoSansSC-Light (특수 메모)
(Mac 버전)
"""
import UnityPy, warnings, json, os, glob as _glob
import freetype, numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import ast as _ast

warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

PROJ_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANS_DIR = os.path.join(PROJ_DIR, 'translation')
FONTS_DIR = os.path.join(PROJ_DIR, 'fonts')

BUNDLE_DIR = os.path.expanduser(
    '~/Library/Application Support/Steam/steamapps/common/'
    'Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/'
    'StreamingAssets/aa/StandaloneOSX/'
)
BUNDLE = BUNDLE_DIR + 'tmp_assets_all_b1a6409f18e4aa561fbb224684a03088.bundle'
import sys
if len(sys.argv) > 1:
    BUNDLE = sys.argv[1]

# ★ memomentKkukkkuk은 리포에 없으므로 직접 경로 지정
MEMO_FONT_PATH = os.path.join(FONTS_DIR, 'memomentKkukkkuk.ttf')
KCC_FONT_PATH  = os.path.join(FONTS_DIR, 'KCCPakKyongni.ttf')

GLYPH_PX   = 40
PADDING    = 6
ATLAS_W    = 2048
ATLAS_H    = 2048
POINT_SIZE = 90

ITIM_BASE_PID      =  8449472204274111930
SEMIBOLD_FONT_PID  =  3523651493037469584
SEMIBOLD_TEX_PID   = -7587779429925130352
SCHOOLBELL_BASE_PID =  1334214029199024105
SC_LIGHT_FONT_PID  = -7161292832032528865
SC_LIGHT_TEX_PID   =  5975520222849230367
NOTO_REG_PID       = -3081274781549595770   # 체인 삽입 기준점
TMPL_PID           =  1598803222731014773   # Vollkorn-Regular SDF EN (템플릿 소스)

def clone(obj):
    new = object.__new__(type(obj))
    new.__dict__.update(obj.__dict__)
    return new

used = set()
with open(os.path.join(TRANS_DIR, 'to_translate_books_ko.json'), encoding='utf-8') as f:
    for v in json.load(f).values(): used.update(v)
with open(os.path.join(TRANS_DIR, 'to_translate_main_ko.json'), encoding='utf-8') as f:
    for val in json.load(f).values():
        parsed = _ast.literal_eval(val) if isinstance(val, str) else val
        for v in parsed.values(): used.update(str(v))
with open(os.path.join(TRANS_DIR, 'to_translate_dialogue_ko.json'), encoding='utf-8') as f:
    for v in json.load(f).values():
        text = v.get('text', '') if isinstance(v, dict) else str(v)
        used.update(text)
for path in _glob.glob(os.path.join(TRANS_DIR, 'characters', '*.json')):
    with open(path, encoding='utf-8') as f:
        for v in json.load(f).values():
            text = v.get('text', '') if isinstance(v, dict) else str(v)
            used.update(text)
with open(os.path.join(TRANS_DIR, 'newspaper_articles_ko.json'), encoding='utf-8') as f:
    for v in json.load(f).values():
        text = v.get('text', '') if isinstance(v, dict) else str(v)
        used.update(text)

hangul = sorted(c for c in used if '가' <= c <= '힣')
basics = sorted(set(' !"\'()*+,-./:;<=>?@[]_'
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'))
CHARS = sorted(set(hangul) | set(basics))
print(f'구울 글자: {len(CHARS)}자 (한글 {len(hangul)}자)')

def bake_sdf(font_path, label):
    face = freetype.Face(font_path)
    face.set_pixel_sizes(GLYPH_PX, GLYPH_PX)
    atlas  = np.zeros((ATLAS_H, ATLAS_W), dtype=np.uint8)
    packed = []
    cx, cy, row_h = 0, 0, 0
    miss = 0
    print(f'{label} SDF 렌더링 중...')
    for ch in CHARS:
        try:
            face.load_char(ord(ch), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
            if face.glyph.bitmap.width == 0: continue
        except:
            miss += 1; continue
        g, bm = face.glyph, face.glyph.bitmap
        buf   = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.width)
        ph, pw = bm.rows + 2*PADDING, bm.width + 2*PADDING
        pad2  = np.zeros((ph, pw), np.float32)
        pad2[PADDING:PADDING+bm.rows, PADDING:PADDING+bm.width] = buf / 255.0
        ins = distance_transform_edt(pad2  > 0.5)
        out = distance_transform_edt(pad2 <= 0.5)
        sdf = (np.clip((ins - out) / PADDING * 0.5 + 0.5, 0, 1) * 255).astype(np.uint8)
        if cx + pw > ATLAS_W: cx = 0; cy += row_h + 1; row_h = 0
        if cy + ph > ATLAS_H: print(f'  WARNING: atlas full at {len(packed)}'); break
        atlas[cy:cy+ph, cx:cx+pw] = sdf
        packed.append({
            'ch': ch, 'ax': cx, 'ay': cy, 'aw': pw, 'ah': ph,
            'advance': g.advance.x / 64.0,
            'bearing_x': float(g.bitmap_left), 'bearing_y': float(g.bitmap_top),
            'bm_w': float(bm.width), 'bm_h': float(bm.rows),
        })
        row_h = max(row_h, ph); cx += pw + 1
    print(f'  완료: {len(packed)}자 (미처리 {miss}자)')
    return atlas, packed

atlas_memo, packed_memo = bake_sdf(MEMO_FONT_PATH, 'memomentKkukkkuk')
atlas_kcc,  packed_kcc  = bake_sdf(KCC_FONT_PATH,  'KCCPakKyongni')

scale = POINT_SIZE / GLYPH_PX
env = UnityPy.load(BUNDLE)

tmpl_c0, tmpl_g0 = None, None
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == TMPL_PID:
        d = obj.read()
        if d.m_CharacterTable:
            tmpl_c0, tmpl_g0 = d.m_CharacterTable[0], d.m_GlyphTable[0]
        break

def build_font_asset(packed, d):
    new_chars, new_glyphs = [], []
    for idx, p in enumerate(packed):
        nc = clone(tmpl_c0)
        nc.m_Unicode    = ord(p['ch'])
        nc.m_GlyphIndex = idx
        nc.m_Scale      = 1.0
        new_chars.append(nc)
        ng = clone(tmpl_g0)
        ng.m_Index      = idx
        ng.m_Scale      = 1.0
        ng.m_AtlasIndex = 0
        nm = clone(tmpl_g0.m_Metrics)
        nm.m_Width               = p['bm_w']      * scale
        nm.m_Height              = p['bm_h']      * scale
        nm.m_HorizontalBearingX  = p['bearing_x'] * scale
        nm.m_HorizontalBearingY  = p['bearing_y'] * scale
        nm.m_HorizontalAdvance   = p['advance']   * scale
        ng.m_Metrics = nm
        nr = clone(tmpl_g0.m_GlyphRect)
        nr.m_X      = p['ax'] + PADDING
        nr.m_Y      = ATLAS_H - (p['ay'] + PADDING) - int(p['bm_h'])
        nr.m_Width  = int(p['bm_w'])
        nr.m_Height = int(p['bm_h'])
        ng.m_GlyphRect = nr
        new_glyphs.append(ng)
    d.m_AtlasPopulationMode = 0
    d.m_AtlasWidth          = ATLAS_W
    d.m_AtlasHeight         = ATLAS_H
    d.m_AtlasPadding        = PADDING
    d.m_CharacterTable      = new_chars
    d.m_GlyphTable          = new_glyphs
    return len(new_chars)

def inject_atlas(tex_obj, atlas):
    tex = tex_obj.read()
    print(f'  텍스처: {tex.m_Width}x{tex.m_Height} -> {ATLAS_W}x{ATLAS_H}')
    rgba = Image.new('RGBA', (ATLAS_W, ATLAS_H), (255, 255, 255, 0))
    rgba.putalpha(Image.fromarray(atlas, 'L'))
    tex.image = rgba
    tex.save()

def insert_into_chain(raw, new_pid, before_pid, label):
    chain = raw.get('m_FallbackFontAssetTable', [])
    if any(fb.get('m_PathID') == new_pid for fb in chain):
        print(f'  {label}: 이미 존재 (중복 삽입 생략)')
        return raw
    idx = next((i for i, fb in enumerate(chain) if fb.get('m_PathID') == before_pid), -1)
    if idx >= 0:
        chain.insert(idx, {'m_FileID': 0, 'm_PathID': new_pid})
        raw['m_FallbackFontAssetTable'] = chain
        print(f'  {label}: 인덱스 {idx}에 삽입 완료 (체인 {len(chain)}개)')
    else:
        print(f'  ERROR: {label} 기준점 pid={before_pid}를 찾지 못함')
    return raw

print('\n[1] memomentKkukkkuk → NotoSansJP-SemiBold')
for obj in env.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == SEMIBOLD_TEX_PID:
        inject_atlas(obj, atlas_memo); break
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == SEMIBOLD_FONT_PID:
        d = obj.read()
        n = build_font_asset(packed_memo, d)
        d.save()
        print(f'  NotoSansJP-SemiBold: {n}자 저장'); break

print('\n[2] KCCPakKyongni → NotoSansSC-Light')
for obj in env.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == SC_LIGHT_TEX_PID:
        inject_atlas(obj, atlas_kcc); break
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == SC_LIGHT_FONT_PID:
        d = obj.read()
        n = build_font_asset(packed_kcc, d)
        d.save()
        print(f'  NotoSansSC-Light: {n}자 저장'); break

print('\n[3] Itim 체인 수정 (UI 전반)')
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == ITIM_BASE_PID:
        raw = obj.read_typetree()
        raw = insert_into_chain(raw, SEMIBOLD_FONT_PID, NOTO_REG_PID, 'memoment→Itim')
        obj.save_typetree(raw); break

print('\n[4] Schoolbell 체인 수정 (특수 메모)')
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == SCHOOLBELL_BASE_PID:
        raw = obj.read_typetree()
        raw = insert_into_chain(raw, SC_LIGHT_FONT_PID, NOTO_REG_PID, 'KCCPakKyongni→Schoolbell')
        obj.save_typetree(raw); break

with open(BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n완료!')