import zipfile, os, glob

svg_dir = r"d:\TRAE SOLO CN\投资指数资讯\projects\创新药ETF投资分析\svg"
output_path = r"d:\TRAE SOLO CN\投资指数资讯\projects\创新药ETF投资分析\创新药ETF投资分析报告.pptx"
PPT_W = 12192000
PPT_H = 6858000

svg_files = sorted(glob.glob(os.path.join(svg_dir, "*.svg")))
n = len(svg_files)
print(f"Slides: {n}")

if os.path.exists(output_path):
    os.remove(output_path)

# Build CT
ct_parts = []
ct_parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
ct_parts.append('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">')
ct_parts.append('<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>')
ct_parts.append('<Default Extension="xml" ContentType="application/xml"/>')
ct_parts.append('<Default Extension="svg" ContentType="image/svg+xml"/>')
ct_parts.append('<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>')
for i in range(1, n+1):
    ct_parts.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
ct_parts.append('<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>')
ct_parts.append('<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>')
ct_parts.append('<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>')
ct_parts.append('</Types>')

# Pres XML
pres_parts = []
pres_parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
pres_parts.append('<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')
pres_parts.append('<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>')
pres_parts.append('<p:sldIdLst>')
for i in range(1, n+1):
    pres_parts.append(f'<p:sldId id="{i}" r:id="rId{i}"/>')
pres_parts.append('</p:sldIdLst>')
pres_parts.append(f'<p:sldSz cx="{PPT_W}" cy="{PPT_H}"/>')
pres_parts.append(f'<p:notesSz cx="6858000" cy="9144000"/>')
pres_parts.append('</p:presentation>')

# Pres rels
prel_parts = []
prel_parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
prel_parts.append('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">')
prel_parts.append('<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>')
for i in range(1, n+1):
    prel_parts.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
prel_parts.append('</Relationships>')

with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as z:
    z.writestr('[Content_Types].xml', ''.join(ct_parts).encode('utf-8'))
    z.writestr('_rels/.rels', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
    z.writestr('ppt/presentation.xml', ''.join(pres_parts).encode('utf-8'))
    z.writestr('ppt/_rels/presentation.xml.rels', ''.join(prel_parts).encode('utf-8'))
    z.writestr('ppt/slideMasters/slideMaster1.xml', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>')
    z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>')
    z.writestr('ppt/slideLayouts/slideLayout1.xml', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld></p:sldLayout>')
    z.writestr('ppt/theme/theme1.xml', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Default"><a:themeElements><a:clrScheme name="Default"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2><a:accent1><a:srgbClr val="4472C4"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2><a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4><a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Default"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme><a:fmtScheme name="Default"/></a:themeElements></a:theme>')

    for idx, svg_path in enumerate(svg_files):
        slide_num = idx + 1
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        z.writestr(f'ppt/media/image{slide_num}.svg', svg_data)

        slide_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/><p:pic><p:nvPicPr><p:cNvPr id="2" name="Picture {slide_num}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{PPT_W}" cy="{PPT_H}"/></a:xfrm><a:prstGeom prst="rect"/></p:spPr></p:pic></p:spTree></p:cSld></p:sld>'
        z.writestr(f'ppt/slides/slide{slide_num}.xml', slide_xml.encode('utf-8'))

        slide_rel = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{slide_num}.svg"/></Relationships>'
        z.writestr(f'ppt/slides/_rels/slide{slide_num}.xml.rels', slide_rel.encode('utf-8'))

        print(f"  Slide {slide_num}: {os.path.basename(svg_path)}")

print(f"\nPPTX saved to: {output_path}")
print(f"Total slides: {n}")