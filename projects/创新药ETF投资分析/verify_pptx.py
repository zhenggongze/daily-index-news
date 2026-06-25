import zipfile

output_path = r'd:\TRAE SOLO CN\投资指数资讯\projects\创新药ETF投资分析\创新药ETF投资分析报告.pptx'

with open(output_path, 'rb') as f:
    head = f.read(4)

print("First 4 bytes:", list(head))
is_zip = head == b'PK\x03\x04'
print("Is PK zip:", is_zip)

if is_zip:
    z = zipfile.ZipFile(output_path, 'r')
    print(f"Valid ZIP with {len(z.namelist())} entries")
    for n in z.namelist():
        print(f"  {n}")
    z.close()
else:
    with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(200)
    print("File content preview:")
    print(repr(content[:150]))