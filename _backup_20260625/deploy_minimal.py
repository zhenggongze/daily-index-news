"""最小化部署 — 用 requests 直调 OSS + CDN API，绕过 pyopenssl 兼容问题"""
import os, sys, hashlib, hmac, base64, uuid
from datetime import datetime, timezone
from urllib.parse import quote
import requests

AK_ID = os.environ.get("OSS_AK_ID", "")
AK_SECRET = os.environ.get("OSS_AK_SECRET", "")
if not AK_ID or not AK_SECRET:
    print("❌ 错误: 请设置环境变量 OSS_AK_ID 和 OSS_AK_SECRET")
    sys.exit(1)
BUCKET = "portfolio-analysis-hosting"
REGION = "oss-cn-hangzhou"
OSS_URL = f"https://{BUCKET}.{REGION}.aliyuncs.com"
DOMAIN = "portfolio-analysis.top"

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, "dist")
DATA = os.path.join(BASE, "public", "data")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".map": "application/json",
}

def sign_oss(method, headers, resource):
    h = hmac.new(AK_SECRET.encode(), (
        f"{method}\n{headers.get('Content-MD5', '')}\n"
        f"{headers.get('Content-Type', '')}\n"
        f"{headers.get('Date', '')}\n"
        f"{''.join(f'{k}:{headers[k]}\n' for k in sorted(headers) if k.startswith('x-oss-'))}"
        f"{resource}"
    ).encode(), hashlib.sha1)
    return f"OSS {AK_ID}:{base64.b64encode(h.digest()).decode()}"

def percent_encode(s):
    return quote(s, safe='')

def sign_aliyun(params):
    sorted_keys = sorted(params.keys())
    qs = '&'.join(f"{percent_encode(k)}={percent_encode(params[k])}" for k in sorted_keys)
    string_to_sign = f"POST&{percent_encode('/')}&{percent_encode(qs)}"
    h = hmac.new((AK_SECRET + "&").encode(), string_to_sign.encode(), hashlib.sha1)
    return base64.b64encode(h.digest()).decode()

def upload(local, oss_key, cache="no-cache"):
    ext = os.path.splitext(local)[1].lower()
    ct = CONTENT_TYPES.get(ext, "application/octet-stream")
    with open(local, "rb") as f:
        data = f.read()
    md5 = base64.b64encode(hashlib.md5(data).digest()).decode()
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    headers = {
        "Content-Type": ct, "Content-MD5": md5, "Date": date,
        "Content-Disposition": "inline",
        "Cache-Control": f"max-age={3600 if cache == 'long' else 0}",
    }
    headers["Authorization"] = sign_oss("PUT", headers, f"/{BUCKET}/{oss_key}")
    r = requests.put(f"{OSS_URL}/{oss_key}", data=data, headers=headers)
    ok = r.status_code in (200, 201)
    print(f"  {'✅' if ok else '❌'} {oss_key}" + ("" if ok else f" -> {r.status_code} {r.text[:100]}"))

def upload_dir(src, prefix):
    c = 0
    for root, _, files in os.walk(src):
        for f in files:
            local = os.path.join(root, f)
            key = f"{prefix}/{os.path.relpath(local, src).replace(chr(92), '/')}" if prefix else os.path.relpath(local, src).replace(chr(92), "/")
            ext = os.path.splitext(f)[1]
            upload(local, key, "long" if ext in (".js", ".css", ".svg", ".png") else "no-cache")
            c += 1
    return c

def refresh_cdn(paths):
    params = {
        "Action": "RefreshObjectCaches",
        "ObjectPath": "\n".join(paths),
        "ObjectType": "File",
        "Format": "JSON",
        "Version": "2018-05-10",
        "AccessKeyId": AK_ID,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
        "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    params["Signature"] = sign_aliyun(params)
    r = requests.post("https://cdn.aliyuncs.com", data=params)
    if r.status_code == 200:
        for p in paths:
            print(f"  ✅ CDN 刷新: {p}")
    else:
        print(f"  ⚠️ CDN 刷新结果: {r.text[:200]}")

print("=" * 50)
print("  部署到 OSS")
print("=" * 50)

if not os.path.isdir(DIST):
    print(f"❌ dist/ 不存在 (预期路径: {DIST})，请先执行 npm run build")
    sys.exit(1)
if not os.path.isdir(DATA):
    print(f"❌ data/ 不存在 (预期路径: {DATA})")
    sys.exit(1)

print("\n[1] 上传 dist/...")
n1 = upload_dir(DIST, "news")
print(f"  共 {n1} 个文件")

print("\n[2] 上传 data/...")
n2 = upload_dir(DATA, "news/data")
print(f"  共 {n2} 个 JSON")

cdn_paths = []
for root, _, files in os.walk(DIST):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), DIST).replace(chr(92), "/")
        cdn_paths.append(f"https://{DOMAIN}/news/{rel}")
for fname in sorted(os.listdir(DATA)):
    if fname.endswith(".json"):
        cdn_paths.append(f"https://{DOMAIN}/news/data/{fname}")

print(f"\n[3] 刷新 CDN ({len(cdn_paths)} 个文件)...")
refresh_cdn(cdn_paths)

print(f"\n{'=' * 50}")
print(f"  ✅ 部署完成!")
print(f"  https://{DOMAIN}/news/index.html")
print(f"{'=' * 50}")
