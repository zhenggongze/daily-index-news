"""最小化部署 — 用阿里云官方 oss2 SDK 上传 + requests 刷新 CDN

替换手写 HMAC-SHA1 签名，从根因解决 OSS 部署失败问题。
"""
import os, sys, json, uuid
from datetime import datetime, timezone
from urllib.parse import quote
import requests

# oss2 是阿里云官方 OSS Python SDK，内部处理签名
import oss2

AK_ID = os.environ.get("OSS_AK_ID", "")
AK_SECRET = os.environ.get("OSS_AK_SECRET", "")
if not AK_ID or not AK_SECRET:
    print("!!DEPLOY_FAIL!! ERROR_MISSING_CREDS")
    sys.exit(1)

BUCKET = "portfolio-analysis-hosting"
ENDPOINT = "https://oss-cn-hangzhou.aliyuncs.com"
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

# 初始化 oss2 客户端（签名全部由 SDK 处理）
auth = oss2.Auth(AK_ID, AK_SECRET)
bucket = oss2.Bucket(auth, ENDPOINT, BUCKET, connect_timeout=30)


def fail(msg):
    print(f"!!DEPLOY_FAIL!! {msg}", flush=True)
    sys.exit(1)


def test_oss_connection():
    """测试 OSS 连接与凭据是否有效（通过 list 前 1 个对象）"""
    try:
        info = bucket.get_bucket_info()
        print(f"  OSS连接测试: ✅ bucket={info.name} region={info.location}")
        return True
    except oss2.exceptions.OssError as e:
        print(f"  OSS连接测试: ❌ OssError status={e.status} code={e.code} msg={e.message[:200]}")
        return False
    except Exception as e:
        print(f"  OSS连接测试: ❌ {type(e).__name__}: {str(e)[:200]}")
        return False


def upload(local, oss_key, cache="no-cache"):
    """用 oss2 上传单个文件"""
    ext = os.path.splitext(local)[1].lower()
    ct = CONTENT_TYPES.get(ext, "application/octet-stream")
    headers = {
        "Content-Type": ct,
        "Content-Disposition": "inline",
        "Cache-Control": f"max-age={3600 if cache == 'long' else 0}",
    }
    try:
        result = bucket.put_object_from_file(oss_key, local, headers=headers)
        if result.status == 200:
            print(f"  ✅ {oss_key}")
            return True
        else:
            print(f"  ❌ {oss_key} -> status={result.status}")
            return False
    except oss2.exceptions.OssError as e:
        print(f"  ❌ {oss_key} -> OssError status={e.status} code={e.code} msg={e.message[:150]}")
        return False
    except Exception as e:
        print(f"  ❌ {oss_key} -> {type(e).__name__}: {str(e)[:150]}")
        return False


def upload_dir(src, prefix):
    """递归上传目录，返回上传数与失败数"""
    ok = 0
    fail_cnt = 0
    for root, _, files in os.walk(src):
        for f in files:
            local = os.path.join(root, f)
            rel = os.path.relpath(local, src).replace("\\", "/")
            key = f"{prefix}/{rel}" if prefix else rel
            ext = os.path.splitext(f)[1]
            if upload(local, key, "long" if ext in (".js", ".css", ".svg", ".png") else "no-cache"):
                ok += 1
            else:
                fail_cnt += 1
    return ok, fail_cnt


def percent_encode(s):
    return quote(s, safe='')


def sign_aliyun(params):
    """阿里云通用 RPC 签名（用于 CDN 刷新 API）"""
    import hashlib, hmac, base64
    sorted_keys = sorted(params.keys())
    qs = '&'.join(f"{percent_encode(k)}={percent_encode(params[k])}" for k in sorted_keys)
    string_to_sign = f"POST&{percent_encode('/')}&{percent_encode(qs)}"
    h = hmac.new((AK_SECRET + "&").encode(), string_to_sign.encode(), hashlib.sha1)
    return base64.b64encode(h.digest()).decode()


def refresh_cdn(paths):
    """CDN 刷新（失败不致命，只警告）"""
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
    try:
        r = requests.post("https://cdn.aliyuncs.com", data=params, timeout=20)
        if r.status_code == 200:
            for p in paths:
                print(f"  ✅ CDN 刷新: {p}")
        else:
            print(f"  ⚠️ CDN 刷新结果: HTTP {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  ⚠️ CDN 刷新异常: {type(e).__name__}: {str(e)[:200]}")


print("=" * 50)
print("  部署到 OSS (oss2 SDK)")
print("=" * 50)

if not os.path.isdir(DIST):
    fail("DIST_NOT_FOUND")
if not os.path.isdir(DATA):
    fail("DATA_NOT_FOUND")

if not test_oss_connection():
    fail("OSS_CONN_FAIL")

print("\n[1] 上传 dist/...")
n1_ok, n1_fail = upload_dir(DIST, "news")
print(f"  成功 {n1_ok} 个, 失败 {n1_fail} 个")
if n1_fail > 0:
    fail(f"DIST_UPLOAD_FAILED count={n1_fail}")

print("\n[2] 合并 OSS 上已有数据文件并重建 index.json ...")
DATA_PREFIX = "news/data"
existing_oss = set()
try:
    for obj in oss2.ObjectIteratorV2(bucket, prefix=DATA_PREFIX + "/"):
        key = obj.key
        if key.endswith(".json"):
            fname = key.split("/")[-1]
            if fname not in ("index.json", "breakthrough.json"):
                existing_oss.add(fname)
    print(f"  OSS 上已有数据文件: {sorted(existing_oss)}")
except Exception as e:
    print(f"  列出 OSS 已有文件失败(非致命): {e}")
local_files = set()
for fname in os.listdir(DATA):
    if fname.endswith(".json") and fname not in ("index.json", "breakthrough.json"):
        local_files.add(fname)
all_dates = sorted(local_files | existing_oss)
print(f"  合并后全部日期: {all_dates}")
compact_dates = [f.replace(".json", "") for f in all_dates]
idx_path = os.path.join(DATA, "index.json")
with open(idx_path, "w", encoding="utf-8") as f:
    json.dump({"dates": compact_dates, "count": len(compact_dates)}, f, ensure_ascii=False, indent=2)
missing = existing_oss - local_files
if missing:
    print(f"  需要从 OSS 下载缺失文件: {sorted(missing)}")
    for fname in sorted(missing):
        oss_key = f"{DATA_PREFIX}/{fname}"
        local_path = os.path.join(DATA, fname)
        try:
            bucket.get_object_to_file(oss_key, local_path)
            print(f"    ✅ 已下载 {fname}")
        except Exception as e:
            print(f"    ❌ 下载 {fname} 失败: {e}")

print("\n[2] 上传 data/...")
n2_ok, n2_fail = upload_dir(DATA, DATA_PREFIX)
print(f"  成功 {n2_ok} 个, 失败 {n2_fail} 个")
if n2_fail > 0:
    fail(f"DATA_UPLOAD_FAILED count={n2_fail}")

cdn_paths = []
for root, _, files in os.walk(DIST):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), DIST).replace("\\", "/")
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
