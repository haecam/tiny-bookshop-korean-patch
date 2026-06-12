import re

with open('C:/Program Files (x86)/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop_Data/StreamingAssets/aa/catalog.json', encoding='utf-8') as f:
    content = f.read()

crcs = re.findall(r'"m_CRC":\s*\d+', content)
hashes = re.findall(r'"[Hh]ash":\s*"[a-f0-9]+"', content)
print('CRC 항목 수:', len(crcs))
print('Hash 항목 수:', len(hashes))
if crcs:
    print('CRC 예시:', crcs[:3])
if hashes:
    print('Hash 예시:', hashes[:3])

# loca_en 번들 주변 내용
idx_en = content.find('loca_en_assets_all')
print()
print('loca_en 주변:')
print(content[max(0,idx_en-100):idx_en+200])
