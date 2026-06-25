import zipfile, os

f = r'd:\TRAE SOLO CN\投资指数资讯\projects\创新药ETF投资分析\ppt_test.pptx'
if os.path.exists(f):
    os.remove(f)

svg_path = r'd:\TRAE SOLO CN\投资指数资讯\projects\创新药ETF投资分析\svg\slide_001.svg'
with open(svg_path, 'rb') as sf:
    svg_data = sf.read()
print(f'SVG size: {len(svg_data)} bytes')

with zipfile.ZipFile(f, 'w', zipfile.ZIP_STORED) as z:
    z.writestr('[Content_Types].xml', b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
    z.writestr('ppt/media/image1.svg', svg_data)

print(f'File size: {os.path.getsize(f)}')
z2 = zipfile.ZipFile(f, 'r')
print(f'Files: {z2.namelist()}')
z2.close()
print('OK')