"""
RIDIBatang → NotoSansJP-Light 컨테이너에 주입 (Mac 버전)
Vollkorn 체인에 삽입 → 책 본문 한글만 RIDIBatang으로 렌더링
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

# ★ RIDIBatang은 리포에 없으므로 직접 경로 지정
RIDI_FONT_PATH = os.path.join(FONTS_DIR, 'RIDIBatang.otf')

GLYPH_PX   = 40
PADDING    = 6
ATLAS_W    = 2048
ATLAS_H    = 2048
POINT_SIZE = 90

NOTO_LIGHT_FONT_PID = -3725201330635205967
NOTO_LIGHT_TEX_PID  =  8020837963401532081
NOTO_REG_PID        = -3081274781549595770
VOLLKORN_BASE_PID   =  6994376558487935071

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

face = freetype.Face(RIDI_FONT_PATH)
face.set_pixel_sizes(GLYPH_PX, GLYPH_PX)

atlas  = np.zeros((ATLAS_H, ATLAS_W), dtype=np.uint8)
packed = []
cx, cy, row_h = 0, 0, 0

print('RIDIBatang SDF 렌더링 중...')
miss_count = 0
for ch in CHARS:
    try:
        face.load_char(ord(ch), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
        if face.glyph.bitmap.width == 0: continue
    except:
        miss_count += 1; continue
    g, bm = face.glyph, face.glyph.bitmap
    buf  = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.width)
    ph, pw = bm.rows + 2*PADDING, bm.width + 2*PADDING
    pad2 = np.zeros((ph, pw), np.float32)
    pad2[PADDING:PADDING+bm.rows, PADDING:PADDING+bm.width] = buf / 255.0
    ins = distance_transform_edt(pad2  > 0.5)
    out = distance_transform_edt(pad2 <= 0.5)
    sdf = (np.clip((ins - out) / PADDING * 0.5 + 0.5, 0, 1) * 255).astype(np.uint8)
    if cx + pw > ATLAS_W: cx = 0; cy += row_h + 1; row_h = 0
    if cy + ph > ATLAS_H: print(f'  WARNING: atlas full at {len(packed)} chars'); break
    atlas[cy:cy+ph, cx:cx+pw] = sdf
    packed.append({
        'ch': ch, 'ax': cx, 'ay': cy, 'aw': pw, 'ah': ph,
        'advance': g.advance.x / 64.0,
        'bearing_x': float(g.bitmap_left), 'bearing_y': float(g.bitmap_top),
        'bm_w': float(bm.width), 'bm_h': float(bm.rows),
    })
    row_h = max(row_h, ph); cx += pw + 1

print(f'완료: {len(packed)}자 (미처리 {miss_count}자)')

scale = POINT_SIZE / GLYPH_PX
print(f'\nscale = {POINT_SIZE}/{GLYPH_PX} = {scale}')

env = UnityPy.load(BUNDLE)

tmpl_c0, tmpl_g0 = None, None
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == NOTO_REG_PID:
        d = obj.read()
        if d.m_CharacterTable:
            tmpl_c0, tmpl_g0 = d.m_CharacterTable[0], d.m_GlyphTable[0]
        break

if not tmpl_c0:
    print('ERROR: NotoSansJP-Regular 템플릿을 찾지 못했습니다')
    exit(1)

for obj in env.objects:
    if obj.type.name == 'Texture2D' and obj.path_id == NOTO_LIGHT_TEX_PID:
        tex = obj.read()
        print(f'\nNotoSansJP-Light 텍스처: {tex.m_Width}x{tex.m_Height} -> {ATLAS_W}x{ATLAS_H}')
        rgba = Image.new('RGBA', (ATLAS_W, ATLAS_H), (255, 255, 255, 0))
        rgba.putalpha(Image.fromarray(atlas, 'L'))
        tex.image = rgba
        tex.save()
        break

for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == NOTO_LIGHT_FONT_PID:
        d = obj.read()
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
        d.save()
        print(f'NotoSansJP-Light: {len(new_chars)}자 저장 (RIDIBatang, Static)')
        break

for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == VOLLKORN_BASE_PID:
        raw = obj.read_typetree()
        chain = raw.get('m_FallbackFontAssetTable', [])
        print(f'\nVollkorn 기존 체인 ({len(chain)}개):')
        for i, fb in enumerate(chain):
            print(f'  [{i}] pid={fb.get("m_PathID")}')
        noto_reg_idx = next(
            (i for i, fb in enumerate(chain) if fb.get('m_PathID') == NOTO_REG_PID), -1
        )
        if noto_reg_idx >= 0:
            chain.insert(noto_reg_idx, {'m_FileID': 0, 'm_PathID': NOTO_LIGHT_FONT_PID})
            raw['m_FallbackFontAssetTable'] = chain
            obj.save_typetree(raw)
            print(f'\n삽입 완료: 인덱스 {noto_reg_idx}에 NotoSansJP-Light(RIDIBatang) 추가')
        else:
            print('ERROR: NotoSansJP-Regular를 Vollkorn 체인에서 찾지 못했습니다')
        break

with open(BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n완료!')
