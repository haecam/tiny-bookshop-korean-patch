"""
BookkMyungjo Vollkorn 컨텍스트 적용

Light → NotoSansJP-Light 컨테이너 (Vollkorn-Regular 체인, 기존 RIDIBatang 교체)
Bold  → NotoSansSC-SemiBold 컨테이너 (Vollkorn-SemiBold/Italic 체인에 신규 삽입)

체인 결과:
  Vollkorn-Regular:        [..., NotoSansJP-Light(BookkMyungjo_Light), NotoSansJP-Regular, ...]
  Vollkorn-SemiBold:       [NotoSansSC-SemiBold(BookkMyungjo_Bold), NanumPenScript, ...]
  Vollkorn-Italic:         [NotoSansJP-Light(BookkMyungjo_Light), NanumPenScript, ...]
  Vollkorn-SemiBoldItalic: [NotoSansSC-SemiBold(BookkMyungjo_Bold), NanumPenScript, ...]
"""
import UnityPy, warnings, json, ast as _ast, glob as _glob
import freetype, numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

warnings.filterwarnings('ignore')
UnityPy.config.FALLBACK_UNITY_VERSION = '2021.3.58f1'

BUNDLE = 'C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/StandaloneWindows64/tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle'

LIGHT_FONT_PATH = 'C:/git/tiny-bookshop-korean-patch/fonts/BookkMyungjo_Light.ttf'
BOLD_FONT_PATH  = 'C:/git/tiny-bookshop-korean-patch/fonts/BookkMyungjo_Bold.ttf'

GLYPH_PX   = 40
PADDING    = 6
ATLAS_W    = 2048
ATLAS_H    = 2048
POINT_SIZE = 90

# 컨테이너 path_ids
NOTO_LIGHT_FONT_PID  = -3725201330635205967   # NotoSansJP-Light  → BookkMyungjo_Light
NOTO_LIGHT_TEX_PID   =  8020837963401532081
SC_SEMIBOLD_FONT_PID = -1629860644874142470   # NotoSansSC-SemiBold → BookkMyungjo_Bold
SC_SEMIBOLD_TEX_PID  =  8010781936477224186

# Vollkorn 변형 path_ids
VOLLKORN_BASE_PID     =  6994376558487935071  # Regular base (64x64) - 체인 이미 있음
VOLLKORN_SEMIBOLD_PID = -3676257516557452952  # SemiBold
VOLLKORN_ITALIC_PID   = -2591061356695468985  # Italic
VOLLKORN_SEMIITALIC_PID = 8850812671115949161 # SemiBoldItalic

NOTO_REG_PID = -3081274781549595770  # NotoSansJP-Regular (체인 삽입 기준점)

def clone(obj):
    new = object.__new__(type(obj))
    new.__dict__.update(obj.__dict__)
    return new

# ── 글자 수집 ─────────────────────────────────────────────────────────────────
used = set()
with open('C:/git/tiny-bookshop-korean-patch/translation/to_translate_books_ko.json', encoding='utf-8') as f:
    for v in json.load(f).values(): used.update(v)
with open('C:/git/tiny-bookshop-korean-patch/translation/to_translate_main_ko.json', encoding='utf-8') as f:
    for val in json.load(f).values():
        parsed = _ast.literal_eval(val) if isinstance(val, str) else val
        for v in parsed.values(): used.update(str(v))
with open('C:/git/tiny-bookshop-korean-patch/translation/to_translate_dialogue_ko.json', encoding='utf-8') as f:
    for v in json.load(f).values():
        text = v.get('text', '') if isinstance(v, dict) else str(v)
        used.update(text)
for path in _glob.glob('C:/git/tiny-bookshop-korean-patch/translation/characters/*.json'):
    with open(path, encoding='utf-8') as f:
        for v in json.load(f).values():
            text = v.get('text', '') if isinstance(v, dict) else str(v)
            used.update(text)
with open('C:/git/tiny-bookshop-korean-patch/translation/newspaper_articles_ko.json', encoding='utf-8') as f:
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
            if face.glyph.bitmap.width == 0:
                continue
        except:
            miss += 1; continue
        g, bm = face.glyph, face.glyph.bitmap
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
            print(f'  WARNING: atlas full at {len(packed)}'); break
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

atlas_light, packed_light = bake_sdf(LIGHT_FONT_PATH, 'BookkMyungjo_Light')
atlas_bold,  packed_bold  = bake_sdf(BOLD_FONT_PATH,  'BookkMyungjo_Bold')

Image.fromarray(atlas_light).save('C:/git/tiny-bookshop-korean-patch/preview/atlas_bookklight_preview.png')
Image.fromarray(atlas_bold ).save('C:/git/tiny-bookshop-korean-patch/preview/atlas_bokkbold_preview.png')
print('미리보기 저장 완료')

scale = POINT_SIZE / GLYPH_PX
env = UnityPy.load(BUNDLE)

# 템플릿
tmpl_c0, tmpl_g0 = None, None
for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id == NOTO_REG_PID:
        d = obj.read()
        if d.m_CharacterTable:
            tmpl_c0, tmpl_g0 = d.m_CharacterTable[0], d.m_GlyphTable[0]
        break

def build_and_save(font_pid, tex_pid, packed, atlas, label):
    for obj in env.objects:
        if obj.type.name == 'Texture2D' and obj.path_id == tex_pid:
            tex = obj.read()
            print(f'\n  {label} 텍스처: {tex.m_Width}x{tex.m_Height} -> {ATLAS_W}x{ATLAS_H}')
            rgba = Image.new('RGBA', (ATLAS_W, ATLAS_H), (255, 255, 255, 0))
            rgba.putalpha(Image.fromarray(atlas, 'L'))
            tex.image = rgba
            tex.save()
            break
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour' and obj.path_id == font_pid:
            d = obj.read()
            new_chars, new_glyphs = [], []
            for idx, p in enumerate(packed):
                nc = clone(tmpl_c0); nc.m_Unicode = ord(p['ch']); nc.m_GlyphIndex = idx; nc.m_Scale = 1.0
                new_chars.append(nc)
                ng = clone(tmpl_g0); ng.m_Index = idx; ng.m_Scale = 1.0; ng.m_AtlasIndex = 0
                nm = clone(tmpl_g0.m_Metrics)
                nm.m_Width = p['bm_w'] * scale; nm.m_Height = p['bm_h'] * scale
                nm.m_HorizontalBearingX = p['bearing_x'] * scale
                nm.m_HorizontalBearingY = p['bearing_y'] * scale
                nm.m_HorizontalAdvance  = p['advance']   * scale
                ng.m_Metrics = nm
                nr = clone(tmpl_g0.m_GlyphRect)
                nr.m_X = p['ax'] + PADDING
                nr.m_Y = ATLAS_H - (p['ay'] + PADDING) - int(p['bm_h'])
                nr.m_Width = int(p['bm_w']); nr.m_Height = int(p['bm_h'])
                ng.m_GlyphRect = nr
                new_glyphs.append(ng)
            d.m_AtlasPopulationMode = 0; d.m_AtlasWidth = ATLAS_W; d.m_AtlasHeight = ATLAS_H
            d.m_AtlasPadding = PADDING; d.m_CharacterTable = new_chars; d.m_GlyphTable = new_glyphs
            d.save()
            print(f'  {label}: {len(new_chars)}자 저장')
            break

# ── 1. NotoSansJP-Light ← BookkMyungjo_Light (Vollkorn Regular/Italic용) ──────
print('\n[1] BookkMyungjo_Light → NotoSansJP-Light')
build_and_save(NOTO_LIGHT_FONT_PID, NOTO_LIGHT_TEX_PID, packed_light, atlas_light, 'BookkMyungjo_Light')

# ── 2. NotoSansSC-SemiBold ← BookkMyungjo_Bold (Vollkorn Bold용) ──────────────
print('\n[2] BookkMyungjo_Bold → NotoSansSC-SemiBold')
build_and_save(SC_SEMIBOLD_FONT_PID, SC_SEMIBOLD_TEX_PID, packed_bold, atlas_bold, 'BookkMyungjo_Bold')

# ── 3. Vollkorn 체인 업데이트 ─────────────────────────────────────────────────
print('\n[3] Vollkorn 체인 업데이트...')

def insert_at_front(raw, new_pid, label):
    chain = raw.get('m_FallbackFontAssetTable', [])
    if not any(fb.get('m_PathID') == new_pid for fb in chain):
        chain.insert(0, {'m_FileID': 0, 'm_PathID': new_pid})
        raw['m_FallbackFontAssetTable'] = chain
        print(f'  {label}: 맨 앞에 삽입 (체인 {len(chain)}개)')
    else:
        print(f'  {label}: 이미 존재')
    return raw

def insert_before(raw, new_pid, before_pid, label):
    chain = raw.get('m_FallbackFontAssetTable', [])
    if any(fb.get('m_PathID') == new_pid for fb in chain):
        print(f'  {label}: 이미 존재'); return raw
    idx = next((i for i, fb in enumerate(chain) if fb.get('m_PathID') == before_pid), -1)
    if idx >= 0:
        chain.insert(idx, {'m_FileID': 0, 'm_PathID': new_pid})
        print(f'  {label}: 인덱스 {idx} 앞에 삽입 (체인 {len(chain)}개)')
    else:
        chain.insert(0, {'m_FileID': 0, 'm_PathID': new_pid})
        print(f'  {label}: 기준점 없어 맨 앞에 삽입')
    raw['m_FallbackFontAssetTable'] = chain
    return raw

TARGETS = {
    VOLLKORN_BASE_PID:     ('Regular base',       NOTO_LIGHT_FONT_PID,  'before', NOTO_REG_PID),
    VOLLKORN_SEMIBOLD_PID: ('SemiBold',           SC_SEMIBOLD_FONT_PID, 'front',  None),
    VOLLKORN_ITALIC_PID:   ('Italic',             NOTO_LIGHT_FONT_PID,  'front',  None),
    VOLLKORN_SEMIITALIC_PID: ('SemiBoldItalic',   SC_SEMIBOLD_FONT_PID, 'front',  None),
}

for obj in env.objects:
    if obj.type.name == 'MonoBehaviour' and obj.path_id in TARGETS:
        name, new_pid, mode, before_pid = TARGETS[obj.path_id]
        raw = obj.read_typetree()
        if mode == 'before':
            raw = insert_before(raw, new_pid, before_pid, f'Vollkorn-{name}')
        else:
            raw = insert_at_front(raw, new_pid, f'Vollkorn-{name}')
        obj.save_typetree(raw)

with open(BUNDLE, 'wb') as f:
    f.write(env.file.save())
print('\n완료!')
print('- Vollkorn Regular/Italic 한글 → BookkMyungjo_Light')
print('- Vollkorn SemiBold/SemiBoldItalic 한글 → BookkMyungjo_Bold')
