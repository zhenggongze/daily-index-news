"""
AI算力产业链资讯站 — 部署到阿里云 OSS + CDN
核心修复：强制 Content-Disposition: inline 防止浏览器下载
"""
import oss2, os, sys, json

ACCESS_KEY_ID = os.environ.get("OSS_AK_ID", "")
ACCESS_KEY_SECRET = os.environ.get("OSS_AK_SECRET", "")
if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET:
    print("ERROR: 请设置环境变量 OSS_AK_ID 和 OSS_AK_SECRET")
    sys.exit(1)

DOMAIN = "portfolio-analysis.top"
BUCKET_NAME = "portfolio-analysis-hosting"
REGION = "cn-hangzhou"
OSS_ENDPOINT = f"oss-{REGION}.aliyuncs.com"
NEWS_PREFIX = "news"

BASE = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE, "dist")
DATA_DIR = os.path.join(BASE, "public", "data")

auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, f"https://{OSS_ENDPOINT}", BUCKET_NAME)

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

def upload_file(local_path, oss_key, cache="no-cache"):
    ext = os.path.splitext(local_path)[1].lower()
    ct = CONTENT_TYPES.get(ext, "application/octet-stream")
    # 关键修复：强制 inline，防止 OSS 默认 attachment 导致浏览器下载
    headers = {
        "Content-Type": ct,
        "Content-Disposition": "inline",
        "Cache-Control": f"max-age={3600 if cache == 'long' else 0}"
    }
    with open(local_path, "rb") as f:
        bucket.put_object(oss_key, f, headers=headers)
        bucket.put_object_acl(oss_key, oss2.OBJECT_ACL_PUBLIC_READ)
    print(f"  ✅ {oss_key}")

def upload_dir(src_dir, oss_prefix):
    count = 0
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            local = os.path.join(root, fname)
            rel = os.path.relpath(local, src_dir).replace("\\", "/")
            oss_key = f"{oss_prefix}/{rel}"
            ext = os.path.splitext(fname)[1]
            upload_file(local, oss_key, cache="long" if ext in [".js", ".css", ".svg", ".png"] else "no-cache")
            count += 1
    return count

def refresh_cdn(paths):
    try:
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcdn.request.v20180510.RefreshObjectCachesRequest import RefreshObjectCachesRequest
        client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION)
        for p in paths:
            req = RefreshObjectCachesRequest()
            req.set_ObjectPath(p)
            req.set_ObjectType("File")
            client.do_action_with_exception(req)
            print(f"  ✅ CDN 刷新: {p}")
    except Exception as e:
        print(f"  ⚠️ CDN 刷新失败: {e}")

print("=" * 50)
print(f"  AI算力产业链资讯站 → {DOMAIN}/{NEWS_PREFIX}/")
print("=" * 50)

print("\n[1] 上传 dist/ (前端资源)...")
n1 = upload_dir(DIST_DIR, NEWS_PREFIX)
print(f"  共 {n1} 个文件")

print("\n[2] 上传 data/ (新闻数据)...")
n2 = upload_dir(DATA_DIR, f"{NEWS_PREFIX}/data")
print(f"  共 {n2} 个 JSON")

print("\n[3] 刷新 CDN...")
cdn_files = []
cdn_files.append(f"https://{DOMAIN}/{NEWS_PREFIX}/index.html")
for f in sorted(os.listdir(DIST_DIR)):
    local = os.path.join(DIST_DIR, f)
    if os.path.isfile(local) and f != "index.html":
        cdn_files.append(f"https://{DOMAIN}/{NEWS_PREFIX}/{f}")
    elif os.path.isdir(local) and f != "data":
        for sub in sorted(os.listdir(local)):
            cdn_files.append(f"https://{DOMAIN}/{NEWS_PREFIX}/{f}/{sub}")
# 刷新数据文件
for fname in sorted(os.listdir(DATA_DIR)):
    if fname.endswith(".json"):
        cdn_files.append(f"https://{DOMAIN}/{NEWS_PREFIX}/data/{fname}")
for f in cdn_files:
    refresh_cdn([f])
print(f"  共刷新 {len(cdn_files)} 个文件")

print(f"\n{'=' * 50}")
print(f"  ✅ 部署完成!")
print(f"  {'=' * 40}")
print(f"  访问: https://{DOMAIN}/news/index.html")
print(f"  数据: https://{DOMAIN}/news/data/")

print("\n[4] 修复文件头 (防止浏览器下载)...")
for obj in oss2.ObjectIteratorV2(bucket, prefix=f"{NEWS_PREFIX}/"):
    key = obj.key
    if key.endswith("/"):
        continue
    try:
        bucket.update_object_meta(key, {"Content-Disposition": "inline"})
    except:
        pass
print("  全部 inline ✅")

print("\n[5] 二次刷新 CDN...")
for f in cdn_files:
    refresh_cdn([f])

print(f"\n{'=' * 50}")
print(f"  ✅ 全部完成!")
print(f"{'=' * 50}")
