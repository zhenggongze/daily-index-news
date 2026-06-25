"""修复 OSS 文件元数据 + 刷新 CDN"""
import oss2, os
from aliyunsdkcore.client import AcsClient
from aliyunsdkcdn.request.v20180510.RefreshObjectCachesRequest import RefreshObjectCachesRequest

AK = os.environ.get("OSS_AK_ID", "")
SK = os.environ.get("OSS_AK_SECRET", "")
if not AK or not SK:
    print("❌ 请设置 OSS_AK_ID / OSS_AK_SECRET 环境变量")
    exit(1)
bucket = oss2.Bucket(oss2.Auth(AK, SK), "https://oss-cn-hangzhou.aliyuncs.com", "portfolio-analysis-hosting")
client = AcsClient(AK, SK, "cn-hangzhou")

files = [
    "news/index.html",
    "news/favicon.svg",
    "news/assets/index-Cfbjw7AR.css",
    "news/assets/index-B0HbVRPC.js",
    "news/assets/index-B0HbVRPC.js.map",
    "news/data/index.json",
    "news/data/2026-06-22.json",
    "news/data/2026-06-23.json",
]

for f in files:
    bucket.update_object_meta(f, {"Content-Disposition": "inline"})
    meta = bucket.head_object(f)
    cd = meta.headers.get("Content-Disposition", "NONE")
    print(f"  OK {f} -> {cd}")

print("\n刷新 CDN...")
for f in files:
    req = RefreshObjectCachesRequest()
    req.set_ObjectPath(f"https://portfolio-analysis.top/{f}")
    req.set_ObjectType("File")
    client.do_action_with_exception(req)
    print(f"  CDN: {f}")
print("\nDone!")
